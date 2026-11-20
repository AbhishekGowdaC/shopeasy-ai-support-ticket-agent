
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

from app.database.models import Ticket
from app.schemas.ticket import TicketCreate

from app.agent.openai_client import OpenAIClient
from app.agent.ticket_processor import TicketProcessor
from app.agent.llm_client import LLMClient
from app.agent.recovery import recover_stuck_tickets
from app.agent.worker_runner import run_worker_loop


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
