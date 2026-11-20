
from sqlalchemy.orm import Session

from app.database.models import Ticket


def recover_stuck_tickets(db: Session):

    stuck_tickets = db.query(Ticket).filter(
        Ticket.status == "CLASSIFYING"
    ).all()

    recovered_count = 0

    for ticket in stuck_tickets:

        if ticket.classification_attempts >= 3:
            ticket.status = "CLASSIFICATION_BLOCKED"
            ticket.last_error = (
                "Maximum attempts reached before server recovery"
            )
        else:
            ticket.status = "CLASSIFICATION_FAILED"
            ticket.last_error = (
                "Processing interrupted by server restart"
            )
            ticket.next_retry_at = None

        recovered_count += 1

    db.commit()

    return recovered_count
