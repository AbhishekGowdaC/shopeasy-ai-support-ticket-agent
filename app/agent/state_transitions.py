
from app.agent.states import AgentState


# Define permitted state transitions
ALLOWED_TRANSITIONS = {

    AgentState.RECEIVED: [
        AgentState.CLASSIFYING,
        AgentState.FAILED
    ],

    AgentState.CLASSIFYING: [
        AgentState.CLASSIFIED,
        AgentState.NEEDS_HUMAN_REVIEW,
        AgentState.FAILED
    ],

    AgentState.CLASSIFIED: [
        AgentState.RETRIEVING_INFORMATION,
        AgentState.NEEDS_HUMAN_REVIEW,
        AgentState.COMPLETED,
        AgentState.FAILED
    ],

    AgentState.RETRIEVING_INFORMATION: [
        AgentState.TOOL_EXECUTION,
        AgentState.RESPONSE_GENERATION,
        AgentState.NEEDS_HUMAN_REVIEW,
        AgentState.FAILED
    ],

    AgentState.TOOL_EXECUTION: [
        AgentState.RETRIEVING_INFORMATION,
        AgentState.RESPONSE_GENERATION,
        AgentState.FAILED
    ],

    AgentState.RESPONSE_GENERATION: [
        AgentState.COMPLETED,
        AgentState.NEEDS_HUMAN_REVIEW,
        AgentState.FAILED
    ],

    AgentState.NEEDS_HUMAN_REVIEW: [],
    AgentState.COMPLETED: [],
    AgentState.FAILED: []
}


# Validate state transitions
def validate_transition(current_state, next_state):

    allowed = ALLOWED_TRANSITIONS.get(current_state, [])

    if next_state not in allowed:
        raise ValueError(
            f"Invalid transition: {current_state} -> {next_state}"
        )

    return True


def get_next_state(classification):

    if classification.requires_human:
        return AgentState.NEEDS_HUMAN_REVIEW

    if classification.category == "SHIPPING":
        return AgentState.RETRIEVING_INFORMATION

    if classification.category in ["RETURN", "REFUND"]:
        return AgentState.NEEDS_HUMAN_REVIEW

    return AgentState.RETRIEVING_INFORMATION
