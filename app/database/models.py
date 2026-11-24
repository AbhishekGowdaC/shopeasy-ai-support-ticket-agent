
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Integer,
    ForeignKey, 
    Float
)

from app.database.database import Base
from sqlalchemy import Numeric, UniqueConstraint

def utc_now():
    return datetime.now(timezone.utc)


class Ticket(Base):

    __tablename__ = "tickets"

    # Unique ticket identifier
    id = Column(
        String,
        primary_key=True,
        index=True
    )

    # Customer information
    customer_name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(254),
        nullable=False
    )

    order_id = Column(
        String(30),
        nullable=True
    )

    # Ticket information
    subject = Column(
        String(150),
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False,
        default="RECEIVED"
    )

    category = Column(
        String(50),
        nullable=True
    )

    priority = Column(
        String(30),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    classification_attempts = Column(
        Integer,
        nullable=False,
        default=0
    )

    last_error = Column(
        Text,
        nullable=True
    )

    next_retry_at = Column(
    DateTime(timezone=True),
    nullable=True
    )

    last_attempt_started_at = Column(
    DateTime(timezone=True),
    nullable=True
    )

    last_attempt_completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    last_attempt_duration_ms = Column(
        Integer,
        nullable=True
    )
    llm_input_tokens = Column(
    Integer,
    nullable=True
    )

    llm_output_tokens = Column(
        Integer,
        nullable=True
    )

    llm_total_tokens = Column(
        Integer,
        nullable=True
    )

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True, index=True)

    ticket_id = Column(
        String,
        ForeignKey("tickets.id"),
        nullable=False,
        index=True
    )

    action_type = Column(String(50), nullable=False)

    amount = Column(Float, nullable=True)

    status = Column(
        String(30),
        nullable=False,
        default="PENDING"
    )

    reviewed_by = Column(String(100), nullable=True)

    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    reason = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String, primary_key=True, index=True)

    approval_id = Column(
        String,
        ForeignKey("approvals.id"),
        nullable=False,
        unique=True
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False
    )

    idempotency_key = Column(
        String(100),
        nullable=False,
        unique=True
    )

    status = Column(
        String(30),
        nullable=False,
        default="COMPLETED"
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
