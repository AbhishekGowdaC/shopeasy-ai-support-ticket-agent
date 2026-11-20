from enum import Enum
from pydantic import BaseModel, Field


class TicketCategory(str, Enum):
    PAYMENT = "PAYMENT"
    SHIPPING = "SHIPPING"
    REFUND = "REFUND"
    RETURN = "RETURN"
    ACCOUNT = "ACCOUNT"
    PRODUCT = "PRODUCT"
    OTHER = "OTHER"

class TicketPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class TicketSentiment(str, Enum):
    CALM = "CALM"
    CONFUSED = "CONFUSED"
    FRUSTRATED = "FRUSTRATED"
    ANGRY = "ANGRY"

class TicketClassification(BaseModel):
    category: TicketCategory
    priority: TicketPriority
    sentiment: TicketSentiment
    requires_human: bool
    reason: str = Field(
        description="Short explanation for the classification"
    )

    