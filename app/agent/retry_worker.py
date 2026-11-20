
from datetime import datetime, timedelta, timezone
import logging
import time

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database.models import Ticket
from app.agent.ticket_processor import TicketProcessor
from app.agent.exceptions import (
    LLMError,
    LLMTemporaryError,
    LLMConfigurationError
)
from app.agent.retry_policy import calculate_retry_delay


logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


def utc_now_naive():
    """Return current UTC time without timezone information for SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RetryWorker:

    def __init__(
        self,
        db: Session,
        processor: TicketProcessor
    ):
        self.db = db
        self.processor = processor

    def record_attempt_completion(
        self,
        ticket: Ticket,
        started_clock: float
    ):
        """Record attempt completion timestamp and duration."""

        ticket.last_attempt_completed_at = utc_now_naive()

        ticket.last_attempt_duration_ms = round(
            (time.perf_counter() - started_clock) * 1000
        )

    def process_ticket(self, ticket: Ticket):

        ticket_id = ticket.id

        # Step 1: Handle tickets that exhausted all attempts
        if ticket.classification_attempts >= MAX_ATTEMPTS:

            self.db.query(Ticket).filter(
                Ticket.id == ticket_id,
                Ticket.status.in_([
                    "RECEIVED",
                    "CLASSIFICATION_FAILED"
                ]),
                Ticket.classification_attempts >= MAX_ATTEMPTS
            ).update(
                {
                    Ticket.status: "CLASSIFICATION_BLOCKED",
                    Ticket.next_retry_at: None
                },
                synchronize_session=False
            )

            self.db.commit()
            return

        # Step 2: Get current UTC time
        now = utc_now_naive()

        # Step 3: Atomically claim the ticket
        claimed_count = self.db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.classification_attempts < MAX_ATTEMPTS,
            or_(
                Ticket.status == "RECEIVED",
                and_(
                    Ticket.status == "CLASSIFICATION_FAILED",
                    or_(
                        Ticket.next_retry_at.is_(None),
                        Ticket.next_retry_at <= now
                    )
                )
            )
        ).update(
            {
                Ticket.status: "CLASSIFYING",

                Ticket.classification_attempts:
                    Ticket.classification_attempts + 1,

                Ticket.next_retry_at: None,

                Ticket.last_attempt_started_at: now,

                Ticket.last_attempt_completed_at: None,

                Ticket.last_attempt_duration_ms: None
            },
            synchronize_session=False
        )

        self.db.commit()

        # Step 4: Check whether this worker claimed the ticket
        if claimed_count != 1:

            logger.info(
                "Ticket claim unsuccessful",
                extra={
                    "ticket_id": ticket_id
                }
            )

            return

        # Step 5: Reload the claimed ticket
        ticket = self.db.query(Ticket).filter(
            Ticket.id == ticket_id
        ).first()

        if ticket is None:
            return

        # Start measuring the processing duration
        attempt_started_clock = time.perf_counter()

        logger.info(
            "Ticket classification started",
            extra={
                "ticket_id": ticket_id,
                "attempt": ticket.classification_attempts
            }
        )

        # Step 6: Process the ticket
        try:

            result = self.processor.process_ticket(
                subject=ticket.subject,
                message=ticket.message
            )

            # Save classification
            classification = result.classification

            ticket.category = classification.category.value
            ticket.priority = classification.priority.value

            ticket.llm_input_tokens = result.input_tokens
            ticket.llm_output_tokens = result.output_tokens
            ticket.llm_total_tokens = result.total_tokens

            ticket.last_error = None
            ticket.next_retry_at = None

            if classification.requires_human:
                ticket.status = "NEEDS_HUMAN_REVIEW"
            else:
                ticket.status = "CLASSIFIED"

            # Record completion time and duration
            self.record_attempt_completion(
                ticket,
                attempt_started_clock
            )

            logger.info(
                "Ticket classification completed",
                extra={
                    "ticket_id": ticket_id,
                    "status": ticket.status,
                    "duration_ms": ticket.last_attempt_duration_ms,
                    "attempt": ticket.classification_attempts
                }
            )

            self.db.commit()

        # Step 7: Handle temporary LLM errors
        except LLMTemporaryError as exc:

            self.db.rollback()

            ticket = self.db.query(Ticket).filter(
                Ticket.id == ticket_id
            ).first()

            if ticket is None:
                return

            self.record_attempt_completion(
                ticket,
                attempt_started_clock
            )

            ticket.last_error = str(exc)

            if ticket.classification_attempts >= MAX_ATTEMPTS:

                ticket.status = "CLASSIFICATION_BLOCKED"
                ticket.next_retry_at = None

            else:

                delay = calculate_retry_delay(
                    ticket.classification_attempts
                )

                ticket.status = "CLASSIFICATION_FAILED"

                ticket.next_retry_at = (
                    utc_now_naive() + timedelta(seconds=delay)
                )

            logger.warning(
                "Temporary ticket classification failure",
                extra={
                    "ticket_id": ticket_id,
                    "error_type": type(exc).__name__,
                    "attempt": ticket.classification_attempts,
                    "duration_ms": ticket.last_attempt_duration_ms,
                    "next_status": ticket.status
                }
            )

            self.db.commit()

        # Step 8: Handle configuration errors
        except LLMConfigurationError as exc:

            self.db.rollback()

            ticket = self.db.query(Ticket).filter(
                Ticket.id == ticket_id
            ).first()

            if ticket is None:
                return

            self.record_attempt_completion(
                ticket,
                attempt_started_clock
            )

            ticket.status = "CLASSIFICATION_BLOCKED"
            ticket.last_error = str(exc)
            ticket.next_retry_at = None

            logger.error(
                "Ticket classification blocked due to configuration error",
                extra={
                    "ticket_id": ticket_id,
                    "error_type": type(exc).__name__,
                    "attempt": ticket.classification_attempts,
                    "duration_ms": ticket.last_attempt_duration_ms
                }
            )

            self.db.commit()

        # Step 9: Handle other LLM errors
        except LLMError as exc:

            self.db.rollback()

            ticket = self.db.query(Ticket).filter(
                Ticket.id == ticket_id
            ).first()

            if ticket is None:
                return

            self.record_attempt_completion(
                ticket,
                attempt_started_clock
            )

            ticket.status = "CLASSIFICATION_BLOCKED"
            ticket.last_error = str(exc)
            ticket.next_retry_at = None

            logger.error(
                "Ticket classification blocked",
                extra={
                    "ticket_id": ticket_id,
                    "error_type": type(exc).__name__,
                    "attempt": ticket.classification_attempts,
                    "duration_ms": ticket.last_attempt_duration_ms
                }
            )

            self.db.commit()

    # Step 10: Find and process eligible tickets
    def retry_failed_tickets(self):

        now = utc_now_naive()

        tickets = self.db.query(Ticket).filter(
            Ticket.status.in_([
                "RECEIVED",
                "CLASSIFICATION_FAILED"
            ]),

            Ticket.classification_attempts < MAX_ATTEMPTS,

            or_(
                Ticket.status == "RECEIVED",

                and_(
                    Ticket.status == "CLASSIFICATION_FAILED",

                    or_(
                        Ticket.next_retry_at.is_(None),
                        Ticket.next_retry_at <= now
                    )
                )
            )
        ).all()

        for ticket in tickets:
            self.process_ticket(ticket)
