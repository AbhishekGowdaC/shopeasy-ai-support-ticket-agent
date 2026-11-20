
import pytest

from app.agent.fake_llm_client import FakeLLMClient
from app.agent.ticket_processor import TicketProcessor

from app.agent.exceptions import LLMTemporaryError

from app.schemas.classification import (
    TicketClassification,
    TicketCategory,
    TicketPriority,
    TicketSentiment
)


def test_process_payment_ticket():

    fake_response = TicketClassification(
        category=TicketCategory.PAYMENT,
        priority=TicketPriority.HIGH,
        sentiment=TicketSentiment.FRUSTRATED,
        requires_human=True,
        reason="Duplicate payment reported."
    )

    fake_client = FakeLLMClient(fake_response)

    processor = TicketProcessor(fake_client)

    result = processor.process_ticket(
        subject="Duplicate payment",
        message="I was charged twice."
    )

    # Verify classification
    assert result.classification.category == TicketCategory.PAYMENT
    assert result.classification.priority == TicketPriority.HIGH
    assert result.classification.sentiment == TicketSentiment.FRUSTRATED

    assert result.classification.requires_human is True

    # Verify token usage
    assert result.input_tokens == 100
    assert result.output_tokens == 30
    assert result.total_tokens == 130


def test_process_shipping_ticket():

    fake_response = TicketClassification(
        category=TicketCategory.SHIPPING,
        priority=TicketPriority.MEDIUM,
        sentiment=TicketSentiment.CONFUSED,
        requires_human=False,
        reason="Customer wants delivery information."
    )

    fake_client = FakeLLMClient(fake_response)

    processor = TicketProcessor(fake_client)

    result = processor.process_ticket(
        subject="Where is my order?",
        message="My order has not arrived yet."
    )

    # Verify classification
    assert result.classification.category == TicketCategory.SHIPPING
    assert result.classification.priority == TicketPriority.MEDIUM
    assert result.classification.sentiment == TicketSentiment.CONFUSED

    assert result.classification.requires_human is False

    # Verify token usage
    assert result.input_tokens == 100
    assert result.output_tokens == 30
    assert result.total_tokens == 130


class FailingFakeLLMClient:

    def classify_ticket(self, subject, message):
        raise LLMTemporaryError("Simulated API failure")


def test_processor_propagates_llm_failure():

    fake_client = FailingFakeLLMClient()

    processor = TicketProcessor(fake_client)

    with pytest.raises(LLMTemporaryError):
        processor.process_ticket(
            subject="Payment failed",
            message="My payment was deducted."
        )
