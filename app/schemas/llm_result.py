from dataclasses import dataclass

from app.schemas.classification import TicketClassification


@dataclass
class LLMResult:

    classification: TicketClassification

    input_tokens: int = 0

    output_tokens: int = 0

    total_tokens: int = 0