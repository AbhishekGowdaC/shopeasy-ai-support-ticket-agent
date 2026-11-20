
from app.agent.fake_llm_client import FakeLLMClient

from app.schemas.classification import (
    TicketClassification,
    TicketCategory,
    TicketPriority,
    TicketSentiment
)


def test_fake_llm_returns_shipping_classification():

    response = TicketClassification(
        category=TicketCategory.SHIPPING,
        priority=TicketPriority.MEDIUM,
        sentiment=TicketSentiment.CONFUSED,
        requires_human=False,
        reason="Delivery status question."
    )

    client = FakeLLMClient(response)

    result = client.classify_ticket(
        "Where is my order?",
        "My order has not arrived."
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
