
from app.agent.orchestrator import AgentOrchestrator
from app.agent.states import AgentState
from app.schemas.llm_result import LLMResult


class FakeClassification:
    requires_human = False
    category = "SHIPPING"


class FakeProcessor:

    def process_ticket(self, subject, message):
        return LLMResult(
            classification=FakeClassification(),
            input_tokens=100,
            output_tokens=30,
            total_tokens=130
        )


def test_order_lookup_integration():

    orchestrator = AgentOrchestrator(FakeProcessor())

    result = orchestrator.run(
        "Order delivery status",
        "Where is my order ORD1001?"
    )

    assert result["state"] == AgentState.RESPONSE_GENERATION

    assert result["tool_result"]["success"] is True

    assert (
        result["tool_result"]["order"]["order_id"]
        == "ORD1001"
    )


def test_missing_order_id_routes_to_review():

    orchestrator = AgentOrchestrator(FakeProcessor())

    result = orchestrator.run(
        "Order delivery status",
        "Where is my order?"
    )

    assert result["state"] == AgentState.NEEDS_HUMAN_REVIEW


def test_unknown_order_returns_not_found():

    orchestrator = AgentOrchestrator(FakeProcessor())

    result = orchestrator.run(
        "Order delivery status",
        "Where is my order ORD9999?"
    )

    assert result["state"] == AgentState.RESPONSE_GENERATION

    assert result["tool_result"]["success"] is False
