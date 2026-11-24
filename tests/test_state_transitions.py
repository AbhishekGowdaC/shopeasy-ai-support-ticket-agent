from app.agent.states import AgentState
from app.agent.state_transitions import get_next_state


def test_shipping_ticket_routes_to_retrieval():

    class FakeClassification:
        requires_human = False
        category = "SHIPPING"

    result = get_next_state(FakeClassification())

    assert result == AgentState.RETRIEVING_INFORMATION


def test_human_review_ticket_routes_correctly():

    class FakeClassification:
        requires_human = True
        category = "PAYMENT"

    result = get_next_state(FakeClassification())

    assert result == AgentState.NEEDS_HUMAN_REVIEW



    