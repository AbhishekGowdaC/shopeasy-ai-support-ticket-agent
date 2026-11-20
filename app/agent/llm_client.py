from typing import Protocol

from app.schemas.llm_result import LLMResult


class LLMClient(Protocol):

    def classify_ticket(
        self,
        subject: str,
        message: str
    ) -> LLMResult:
        ...