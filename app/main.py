
import threading
from uuid import uuid4
from functools import lru_cache
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import (
    Base,
    engine,
    SessionLocal,
    get_db
)

from app.schemas.ticket import TicketCreate

from app.agent.openai_client import OpenAIClient
from app.agent.ticket_processor import TicketProcessor
from app.agent.llm_client import LLMClient
from app.agent.recovery import recover_stuck_tickets
from app.agent.worker_runner import run_worker_loop

from app.database.models import Ticket, Approval
from app.schemas.approval import ApprovalCreate, ApprovalResponse
from datetime import datetime, timezone
from fastapi import Header
from app.schemas.approval import ApprovalDecision
from sqlalchemy.exc import IntegrityError

from app.database.models import Refund
from app.schemas.approval import RefundResponse

Base.metadata.create_all(bind=engine)

stop_event = threading.Event()
worker_thread = None


@lru_cache
def get_ticket_processor() -> TicketProcessor:
    llm_client: LLMClient = OpenAIClient()
    return TicketProcessor(llm_client)


# Application startup and shutdown lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_thread

    print("ShopEasy starting...")

    # Step 1: Recover interrupted tickets
    db = SessionLocal()

    try:
        recovered_count = recover_stuck_tickets(db)

        print(
            f"Recovery completed. "
            f"Tickets recovered: {recovered_count}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    # Step 2: Initialize the shared processor
    processor = get_ticket_processor()

    # Step 3: Start the background worker
    stop_event.clear()

    worker_thread = threading.Thread(
        target=run_worker_loop,
        args=(stop_event, processor),
        daemon=True
    )

    worker_thread.start()

    print("Background worker started.")

    yield

    # Step 4: Stop the background worker
    print("ShopEasy shutting down...")

    stop_event.set()

    if worker_thread is not None:
        worker_thread.join(timeout=10)

    print("Background worker stopped.")


app = FastAPI(
    title="ShopEasy Support Agent",
    description="AI-powered support ticket triage system",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
def home():
    return {
        "message": "ShopEasy Support Agent API is running"
    }


# Create ticket - background processing

@app.post(
    "/tickets",
    status_code=status.HTTP_202_ACCEPTED
)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db)
):

    ticket_id = f"TKT-{uuid4().hex[:8].upper()}"

    new_ticket = Ticket(
        id=ticket_id,
        customer_name=ticket.customer_name,
        email=str(ticket.email),
        order_id=ticket.order_id,
        subject=ticket.subject,
        message=ticket.message,
        status="RECEIVED"
    )

    # Save ticket first
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    # Return initial acknowledgement
    return {
        "message": "Ticket received successfully. Processing in background.",
        "ticket_id": new_ticket.id,
        "status": new_ticket.status
    }


@app.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db)
):

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return {
        "ticket_id": ticket.id,
        "customer_name": ticket.customer_name,
        "email": ticket.email,
        "order_id": ticket.order_id,
        "subject": ticket.subject,
        "message": ticket.message,
        "status": ticket.status,
        "category": ticket.category,
        "priority": ticket.priority,
        "created_at": ticket.created_at,
        "llm_usage": {
        "input_tokens": ticket.llm_input_tokens,
        "output_tokens": ticket.llm_output_tokens,
        "total_tokens": ticket.llm_total_tokens
    }
    }


@app.post(
    "/approvals",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED
)
def create_approval(
    approval_data: ApprovalCreate,
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == approval_data.ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if approval_data.action_type.value == "REFUND":
        if approval_data.amount is None:
            raise HTTPException(
                status_code=400,
                detail="Refund amount is required"
            )

    # 3. Create the approval record
    new_approval = Approval(
        id=str(uuid4()),
        ticket_id=approval_data.ticket_id,
        action_type=approval_data.action_type.value,
        amount=approval_data.amount,
        status="PENDING"
    )

    # 4. Save to database
    try:
        db.add(new_approval)
        db.commit()
        db.refresh(new_approval)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create approval request"
        )

    # 5. Return the created approval
    return new_approval



@app.post(
    "/approvals/{approval_id}/decision",
    response_model=ApprovalResponse
)
def decide_approval(
    approval_id: str,
    decision: ApprovalDecision,
    db: Session = Depends(get_db),
    admin_user: str = Header(..., alias="X-Admin-User")
):
    # 1. A decision cannot be PENDING
    if decision.status.value == "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Decision must be APPROVED or REJECTED"
        )

    # 2. Check whether the approval exists
    approval = db.query(Approval).filter(
        Approval.id == approval_id
    ).first()

    if not approval:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found"
        )

    # 3. Only pending requests can be reviewed
    if approval.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="Approval has already been reviewed"
        )

    # 4. Atomically update only if still PENDING
    updated_count = db.query(Approval).filter(
        Approval.id == approval_id,
        Approval.status == "PENDING"
    ).update(
        {
            Approval.status: decision.status.value,
            Approval.reviewed_by: admin_user,
            Approval.reviewed_at: datetime.now(timezone.utc),
            Approval.reason: decision.reason
        },
        synchronize_session=False
    )

    if updated_count != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Approval has already been reviewed"
        )

    # 5. Save the decision
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save approval decision"
        )

    # 6. Return updated approval
    updated_approval = db.query(Approval).filter(
        Approval.id == approval_id
    ).first()

    return updated_approval

@app.post(
    "/approvals/{approval_id}/execute",
    response_model=RefundResponse
)
def execute_refund(
    approval_id: str,
    db: Session = Depends(get_db)
):
    # 1. Find the approval
    approval = db.query(Approval).filter(
        Approval.id == approval_id
    ).first()

    if not approval:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found"
        )

    # 2. Check approval status
    if approval.status != "APPROVED":
        raise HTTPException(
            status_code=400,
            detail="Refund requires an approved request"
        )

    if approval.action_type != "REFUND" or approval.amount is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid refund approval"
        )

    # 3. Generate a stable idempotency key
    idempotency_key = f"refund-{approval.id}"

    # 4. Check whether this refund already exists
    existing_refund = db.query(Refund).filter(
        Refund.idempotency_key == idempotency_key
    ).first()

    if existing_refund:
        return existing_refund

    # 5. Create refund record
    new_refund = Refund(
        id=str(uuid4()),
        approval_id=approval.id,
        amount=approval.amount,
        idempotency_key=idempotency_key,
        status="COMPLETED"
    )

    try:
        db.add(new_refund)
        db.commit()
        db.refresh(new_refund)

        return new_refund

    except IntegrityError:
        db.rollback()

        # Another request may have created this refund first.
        existing_refund = db.query(Refund).filter(
            Refund.idempotency_key == idempotency_key
        ).first()

        if existing_refund:
            return existing_refund

        raise HTTPException(
            status_code=409,
            detail="Refund could not be created due to a database conflict"
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Refund execution failed"
        )
