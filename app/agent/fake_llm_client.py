
from app.schemas.llm_result import LLMResult


class FakeLLMClient:

    def __init__(self, response):
        self.response = response

    def classify_ticket(self, subject, message):

        return LLMResult(
            classification=self.response,
            input_tokens=100,
            output_tokens=30,
            total_tokens=130
        )
