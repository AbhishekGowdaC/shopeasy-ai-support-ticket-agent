
from app.agent.states import AgentState
from app.agent.state_transitions import get_next_state


class AgentOrchestrator:

    def __init__(self, processor):
        self.processor = processor

    def run(self, subject, message):

        # Step 1: Start classification
        current_state = AgentState.CLASSIFYING

        try:

            # Step 2: Classify ticket
            result = self.processor.process_ticket(
                subject=subject,
                message=message
            )

            classification = result.classification

            # Step 3: Determine next state
            current_state = get_next_state(classification)

            # Step 4: Return workflow result
            return {
                "state": current_state,
                "classification": classification,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "total_tokens": result.total_tokens
            }

        except Exception:
            current_state = AgentState.FAILED

            return {
                "state": current_state,
                "error": "Agent processing failed"
            }
