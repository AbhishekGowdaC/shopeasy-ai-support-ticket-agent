
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal

class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalAction(str, Enum):
    REFUND = "REFUND"
    CANCEL_ORDER = "CANCEL_ORDER"


class ApprovalCreate(BaseModel):
    ticket_id: str
    action_type: ApprovalAction
    amount: float | None = Field(default=None, gt=0)


class ApprovalDecision(BaseModel):
    status: ApprovalStatus
    reason: str = Field(min_length=5, max_length=300)


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    action_type: ApprovalAction
    amount: float | None
    status: ApprovalStatus
    reviewed_by: str | None
    reason: str | None

class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    approval_id: str
    amount: Decimal
    idempotency_key: str
    status: str