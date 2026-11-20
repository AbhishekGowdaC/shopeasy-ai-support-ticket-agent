from app.agent.llm_client import LLMClient
from app.schemas.classification import TicketClassification


class TicketProcessor:

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def process_ticket(self, subject, message):

        return self.llm_client.classify_ticket(
            subject=subject,
            message=message
        )
