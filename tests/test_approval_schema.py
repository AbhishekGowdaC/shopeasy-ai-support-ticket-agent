
import pytest

from pydantic import ValidationError
from app.schemas.approval import (
    ApprovalCreate,
    ApprovalDecision,
)


def test_valid_approval_request():
    approval = ApprovalCreate(
        ticket_id="TICKET-101",
        action_type="REFUND",
        amount=15000
    )

    assert approval.amount == 15000


def test_invalid_refund_amount():
    with pytest.raises(ValidationError):
        ApprovalCreate(
            ticket_id="TICKET-101",
            action_type="REFUND",
            amount=-500
        )


def test_valid_approval_decision():
    decision = ApprovalDecision(
        status="APPROVED",
        reason="Refund verified against order."
    )

    assert decision.status == "APPROVED"


def test_invalid_approval_status():
    with pytest.raises(ValidationError):
        ApprovalDecision(
            status="WAITING",
            reason="Refund verified against order."
        )
