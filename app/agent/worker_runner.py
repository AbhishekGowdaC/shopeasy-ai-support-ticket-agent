
import logging
import threading

from app.database.database import SessionLocal
from app.agent.retry_worker import RetryWorker
from app.agent.ticket_processor import TicketProcessor

logger = logging.getLogger(__name__)


def process_pending_tickets_once(
    processor: TicketProcessor
):
    """
    Creates a fresh database session and
    processes eligible tickets.
    """

    db = SessionLocal()

    try:
        worker = RetryWorker(
            db=db,
            processor=processor
        )

        worker.retry_failed_tickets()

    except Exception:
        logger.exception(
            "Error while processing pending tickets"
        )

    finally:
        db.close()


def run_worker_loop(
    stop_event: threading.Event,
    processor: TicketProcessor,
    poll_interval: int = 3
):
    """
    Continuously checks SQLite for pending tickets.
    """

    logger.info("Background worker started")

    while not stop_event.is_set():

        process_pending_tickets_once(processor)

        # Wait before checking the database again.
        # Can stop immediately when shutdown is requested.
        stop_event.wait(poll_interval)

    logger.info("Background worker stopped")
