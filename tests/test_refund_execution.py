
import pytest

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.database import Base, get_db
from app.database.models import Ticket, Approval, Refund


# --------------------------------------------------
# TEST DATABASE FIXTURE
# --------------------------------------------------

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
# FASTAPI TEST CLIENT
# --------------------------------------------------

@pytest.fixture
def client(db_session):

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --------------------------------------------------
# CREATE TEST APPROVAL
# --------------------------------------------------

@pytest.fixture
def approved_refund(db_session):

    ticket = Ticket(
        id="TKT-REFUND001",
        customer_name="Test Customer",
        email="test@example.com",
        subject="Refund request",
        message="Please refund my order.",
        status="NEEDS_HUMAN_REVIEW"
    )

    approval = Approval(
        id="APP-REFUND001",
        ticket_id="TKT-REFUND001",
        action_type="REFUND",
        amount=20000,
        status="APPROVED",
        reviewed_by="admin-demo",
        reason="Refund verified."
    )

    db_session.add(ticket)
    db_session.add(approval)
    db_session.commit()

    return approval


# --------------------------------------------------
# TEST 1: SUCCESSFUL REFUND EXECUTION
# --------------------------------------------------

def test_execute_approved_refund(
    client,
    db_session,
    approved_refund
):

    response = client.post(
        f"/approvals/{approved_refund.id}/execute"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["approval_id"] == approved_refund.id
    assert Decimal(data["amount"]) == Decimal("20000.00")
    assert data["status"] == "COMPLETED"

    # Verify database record
    refund = db_session.query(Refund).filter(
        Refund.approval_id == approved_refund.id
    ).first()

    assert refund is not None
    assert refund.status == "COMPLETED"


# --------------------------------------------------
# TEST 2: PREVENT DUPLICATE REFUND EXECUTION
# --------------------------------------------------

def test_duplicate_refund_execution(
    client,
    db_session,
    approved_refund
):

    first_response = client.post(
        f"/approvals/{approved_refund.id}/execute"
    )

    second_response = client.post(
        f"/approvals/{approved_refund.id}/execute"
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    # Both requests return the same refund
    assert first_data["id"] == second_data["id"]

    # Only one refund record exists
    refund_count = db_session.query(Refund).filter(
        Refund.approval_id == approved_refund.id
    ).count()

    assert refund_count == 1


# --------------------------------------------------
# TEST 3: PENDING APPROVAL CANNOT BE EXECUTED
# --------------------------------------------------

def test_pending_approval_rejected(
    client,
    db_session
):

    ticket = Ticket(
        id="TKT-PENDING001",
        customer_name="Test Customer",
        email="test@example.com",
        subject="Pending refund",
        message="Please refund my order.",
        status="NEEDS_HUMAN_REVIEW"
    )

    approval = Approval(
        id="APP-PENDING001",
        ticket_id=ticket.id,
        action_type="REFUND",
        amount=5000,
        status="PENDING"
    )

    db_session.add_all([ticket, approval])
    db_session.commit()

    response = client.post(
        f"/approvals/{approval.id}/execute"
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Refund requires an approved request"
    )

    assert db_session.query(Refund).count() == 0


# --------------------------------------------------
# TEST 4: REJECTED APPROVAL CANNOT BE EXECUTED
# --------------------------------------------------

def test_rejected_approval_rejected(
    client,
    db_session
):

    ticket = Ticket(
        id="TKT-REJECTED001",
        customer_name="Test Customer",
        email="test@example.com",
        subject="Rejected refund",
        message="Please refund my order.",
        status="NEEDS_HUMAN_REVIEW"
    )

    approval = Approval(
        id="APP-REJECTED001",
        ticket_id=ticket.id,
        action_type="REFUND",
        amount=5000,
        status="REJECTED"
    )

    db_session.add_all([ticket, approval])
    db_session.commit()

    response = client.post(
        f"/approvals/{approval.id}/execute"
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Refund requires an approved request"
    )

    assert db_session.query(Refund).count() == 0


# --------------------------------------------------
# TEST 5: INVALID APPROVAL ID
# --------------------------------------------------

def test_invalid_approval_id(client, db_session):

    response = client.post(
        "/approvals/INVALID-APPROVAL/execute"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Approval request not found"
    )


# --------------------------------------------------
# TEST 6: NON-REFUND APPROVAL CANNOT EXECUTE REFUND
# --------------------------------------------------

def test_non_refund_approval_rejected(
    client,
    db_session
):

    ticket = Ticket(
        id="TKT-CANCEL001",
        customer_name="Test Customer",
        email="test@example.com",
        subject="Cancel order",
        message="Please cancel my order.",
        status="NEEDS_HUMAN_REVIEW"
    )

    approval = Approval(
        id="APP-CANCEL001",
        ticket_id=ticket.id,
        action_type="CANCEL_ORDER",
        amount=None,
        status="APPROVED"
    )

    db_session.add_all([ticket, approval])
    db_session.commit()

    response = client.post(
        f"/approvals/{approval.id}/execute"
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid refund approval"
    )

    assert db_session.query(Refund).count() == 0
