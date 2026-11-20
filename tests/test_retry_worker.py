
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.database.models import Ticket

from app.agent.retry_worker import RetryWorker
from app.agent.ticket_processor import TicketProcessor
from app.agent.fake_llm_client import FakeLLMClient

from app.schemas.classification import (
    TicketClassification,
    TicketCategory,
    TicketPriority,
    TicketSentiment
)
from datetime import datetime, timezone
from app.schemas.llm_result import LLMResult

from app.agent.exceptions import (
    LLMTemporaryError,
    LLMConfigurationError
)


# Separate in-memory SQLite database for testing
@pytest.fixture
def db_session():

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


# --------------------------------------------------
# TEST 1: Successful classification and observability
# --------------------------------------------------

def test_retry_worker_successful_classification(db_session):

    fake_response = TicketClassification(
        category=TicketCategory.PAYMENT,
        priority=TicketPriority.HIGH,
        sentiment=TicketSentiment.FRUSTRATED,
        requires_human=True,
        reason="Customer reported a duplicate payment"
    )

    fake_llm = FakeLLMClient(response=fake_response)

    processor = TicketProcessor(llm_client=fake_llm)

    worker = RetryWorker(
        db=db_session,
        processor=processor
    )

    ticket = Ticket(
        id="TKT-TEST001",
        customer_name="Test Customer",
        email="test@example.com",
        order_id="ORD-1001",
        subject="Duplicate payment",
        message="I was charged twice for my order.",
        status="CLASSIFICATION_FAILED",
        classification_attempts=1
    )

    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)

    # Process ticket
    worker.process_ticket(ticket)

    db_session.refresh(ticket)

    # Verify classification
    assert ticket.status == "NEEDS_HUMAN_REVIEW"
    assert ticket.classification_attempts == 2
    assert ticket.category == "PAYMENT"
    assert ticket.priority == "HIGH"
    assert ticket.last_error is None

    # Verify processing timestamps
    assert ticket.last_attempt_started_at is not None
    assert ticket.last_attempt_completed_at is not None

    # Verify processing duration
    assert ticket.last_attempt_duration_ms is not None
    assert ticket.last_attempt_duration_ms >= 0

    # Verify LLM token usage
    assert ticket.llm_input_tokens == 100
    assert ticket.llm_output_tokens == 30
    assert ticket.llm_total_tokens == 130


# --------------------------------------------------
# TEST 2: Skip ticket after maximum attempts
# --------------------------------------------------

def test_retry_worker_skips_ticket_after_max_attempts(db_session):

    class CountingFakeLLMClient:

        def __init__(self):
            self.calls = 0

        def classify_ticket(self, subject, message):
            self.calls += 1
            raise AssertionError("LLM should not be called")

    fake_llm = CountingFakeLLMClient()

    processor = TicketProcessor(llm_client=fake_llm)

    worker = RetryWorker(
        db=db_session,
        processor=processor
    )

    ticket = Ticket(
        id="TKT-TEST002",
        customer_name="Test Customer",
        email="test@example.com",
        order_id="ORD-1002",
        subject="Payment failed",
        message="Payment was deducted twice.",
        status="CLASSIFICATION_FAILED",
        classification_attempts=3
    )

    db_session.add(ticket)
    db_session.commit()

    worker.process_ticket(ticket)

    db_session.refresh(ticket)

    assert ticket.status == "CLASSIFICATION_BLOCKED"
    assert ticket.classification_attempts == 3
    assert ticket.category is None
    assert ticket.next_retry_at is None

    # Verify LLM was never called
    assert fake_llm.calls == 0


# --------------------------------------------------
# TEST 3: Temporary LLM failure
# --------------------------------------------------

class FailingFakeLLMClient:

    def classify_ticket(self, subject: str, message: str):

        raise LLMTemporaryError(
            "Simulated temporary API failure"
        )


def test_retry_worker_handles_temporary_failure(db_session):

    fake_llm = FailingFakeLLMClient()

    processor = TicketProcessor(llm_client=fake_llm)

    worker = RetryWorker(
        db=db_session,
        processor=processor
    )

    ticket = Ticket(
        id="TKT-TEST003",
        customer_name="Test Customer",
        email="test@example.com",
        subject="Payment issue",
        message="Payment was deducted but order failed.",
        status="CLASSIFICATION_FAILED",
        classification_attempts=1
    )

    db_session.add(ticket)
    db_session.commit()

    worker.process_ticket(ticket)

    db_session.refresh(ticket)

    # Verify retry handling
    assert ticket.status == "CLASSIFICATION_FAILED"
    assert ticket.classification_attempts == 2
    assert ticket.last_error == "Simulated temporary API failure"
    assert ticket.next_retry_at is not None

    # Verify observability on failure
    assert ticket.last_attempt_started_at is not None
    assert ticket.last_attempt_completed_at is not None
    assert ticket.last_attempt_duration_ms is not None
    assert ticket.last_attempt_duration_ms >= 0
    assert ticket.next_retry_at > datetime.now(timezone.utc).replace(tzinfo=None)
# --------------------------------------------------
# TEST 4: Configuration error
# --------------------------------------------------

class ConfigurationErrorFakeLLMClient:

    def classify_ticket(self, subject: str, message: str):

        raise LLMConfigurationError(
            "Invalid OpenAI API key"
        )


def test_retry_worker_blocks_configuration_error(db_session):

    fake_llm = ConfigurationErrorFakeLLMClient()

    processor = TicketProcessor(llm_client=fake_llm)

    worker = RetryWorker(
        db=db_session,
        processor=processor
    )

    ticket = Ticket(
        id="TKT-TEST004",
        customer_name="Test Customer",
        email="test@example.com",
        subject="Payment issue",
        message="My payment was deducted.",
        status="CLASSIFICATION_FAILED",
        classification_attempts=1
    )

    db_session.add(ticket)
    db_session.commit()

    worker.process_ticket(ticket)

    db_session.refresh(ticket)

    # Verify configuration error handling
    assert ticket.status == "CLASSIFICATION_BLOCKED"
    assert ticket.classification_attempts == 2
    assert ticket.last_error == "Invalid OpenAI API key"

    # Verify it is not eligible for automatic retry
    assert ticket.status not in [
        "RECEIVED",
        "CLASSIFICATION_FAILED"
    ]

    # Verify observability
    assert ticket.last_attempt_started_at is not None
    assert ticket.last_attempt_completed_at is not None
    assert ticket.last_attempt_duration_ms is not None
    assert ticket.next_retry_at is None


# --------------------------------------------------
# TEST 5: Prevent duplicate processing
# --------------------------------------------------

def test_worker_does_not_process_already_claimed_ticket(db_session):

    fake_response = TicketClassification(
        category=TicketCategory.PAYMENT,
        priority=TicketPriority.HIGH,
        sentiment=TicketSentiment.FRUSTRATED,
        requires_human=True,
        reason="Duplicate payment"
    )

    class CountingFakeLLMClient:

        def __init__(self):
            self.calls = 0

        def classify_ticket(self, subject, message):

            self.calls += 1

            return LLMResult(
                classification=fake_response,
                input_tokens=100,
                output_tokens=30,
                total_tokens=130
            )

    fake_llm = CountingFakeLLMClient()

    processor = TicketProcessor(llm_client=fake_llm)

    ticket = Ticket(
        id="TKT-ATOMIC001",
        customer_name="Test Customer",
        email="test@example.com",
        subject="Payment issue",
        message="Payment deducted twice.",
        status="CLASSIFYING",
        classification_attempts=1
    )

    db_session.add(ticket)
    db_session.commit()

    worker = RetryWorker(
        db=db_session,
        processor=processor
    )

    worker.process_ticket(ticket)

    db_session.refresh(ticket)

    assert ticket.status == "CLASSIFYING"
    assert fake_llm.calls == 0
