
import re

from app.agent.states import AgentState
from app.agent.state_transitions import (
    get_next_state,
    validate_transition
)
from app.tools.tool_registry import execute_tool


class AgentOrchestrator:

    def __init__(self, processor):
        self.processor = processor

    def extract_order_id(self, message: str):
        match = re.search(
            r"\bORD\d+\b",
            message,
            re.IGNORECASE
        )

        return match.group(0).upper() if match else None

    def run(self, subject, message):

        current_state = AgentState.CLASSIFYING

        try:
            # Step 1: Classify ticket
            result = self.processor.process_ticket(
                subject=subject,
                message=message
            )

            classification = result.classification

            # Step 2: Move to next state
            next_state = AgentState.CLASSIFIED

            validate_transition(current_state, next_state)
            current_state = next_state

            next_state = get_next_state(classification)

            validate_transition(current_state, next_state)
            current_state = next_state

            tool_result = None

            # Step 3: Execute order lookup
            if current_state == AgentState.RETRIEVING_INFORMATION:

                order_id = self.extract_order_id(message)

                if order_id:
                    next_state = AgentState.TOOL_EXECUTION

                    validate_transition(current_state, next_state)
                    current_state = next_state

                    tool_result = execute_tool(
                        "get_order_details",
                        {"order_id": order_id}
                    )

                    next_state = AgentState.RESPONSE_GENERATION

                    validate_transition(current_state, next_state)
                    current_state = next_state

                else:
                    next_state = AgentState.NEEDS_HUMAN_REVIEW

                    validate_transition(current_state, next_state)
                    current_state = next_state

            return {
                "state": current_state,
                "classification": classification,
                "tool_result": tool_result,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "total_tokens": result.total_tokens
            }

        except Exception:
            return {
                "state": AgentState.FAILED,
                "error": "Agent processing failed"
            }
