
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.database.models import Ticket
from app.agent.recovery import recover_stuck_tickets


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


def test_recover_stuck_ticket(db_session):

    ticket = Ticket(
        id="TKT-REC001",
        customer_name="Test Customer",
        email="test@example.com",
        subject="Payment issue",
        message="Payment was deducted but order failed.",
        status="CLASSIFYING",
        classification_attempts=1
    )

    db_session.add(ticket)
    db_session.commit()

    recovered_count = recover_stuck_tickets(db_session)

    db_session.refresh(ticket)

    assert ticket.status == "CLASSIFICATION_FAILED"
    assert ticket.last_error == "Processing interrupted by server restart"
    assert ticket.next_retry_at is None
    assert recovered_count == 1


def test_block_ticket_after_max_attempts(db_session):

    ticket = Ticket(
        id="TKT-REC002",
        customer_name="Test Customer",
        email="test@example.com",
        subject="Payment issue",
        message="Payment was deducted but order failed.",
        status="CLASSIFYING",
        classification_attempts=3
    )

    db_session.add(ticket)
    db_session.commit()

    recovered_count = recover_stuck_tickets(db_session)

    db_session.refresh(ticket)

    assert ticket.status == "CLASSIFICATION_BLOCKED"
    assert ticket.last_error == (
        "Maximum attempts reached before server recovery"
    )
    assert recovered_count == 1


def test_recover_multiple_tickets(db_session):

    ticket1 = Ticket(
        id="TKT-REC003",
        customer_name="Customer One",
        email="one@example.com",
        subject="Payment issue",
        message="Payment failed.",
        status="CLASSIFYING",
        classification_attempts=1
    )

    ticket2 = Ticket(
        id="TKT-REC004",
        customer_name="Customer Two",
        email="two@example.com",
        subject="Shipping issue",
        message="Order not delivered.",
        status="CLASSIFYING",
        classification_attempts=2
    )

    db_session.add_all([ticket1, ticket2])
    db_session.commit()

    recovered_count = recover_stuck_tickets(db_session)

    db_session.refresh(ticket1)
    db_session.refresh(ticket2)

    assert recovered_count == 2
    assert ticket1.status == "CLASSIFICATION_FAILED"
    assert ticket2.status == "CLASSIFICATION_FAILED"
