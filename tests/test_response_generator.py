
from types import SimpleNamespace

import pytest

from app.agent.response_generator import ResponseGenerator


class FakeResponses:

    def create(self, **kwargs):
        return SimpleNamespace(
            output_text=(
                "Your order ORD1001 has been shipped. "
                "Expected delivery: November 27, 2026."
            )
        )


class FakeOpenAIClient:

    def __init__(self):
        self.responses = FakeResponses()


def test_generate_customer_response():

    generator = ResponseGenerator(
        client=FakeOpenAIClient(),
        model="gpt-4.1-mini"
    )

    result = generator.generate_response(
        question="Where is my order ORD1001?",
        context=(
            "Order ORD1001 is shipped. "
            "Expected delivery is November 27, 2026."
        )
    )

    assert "ORD1001" in result
    assert "shipped" in result


def test_empty_question():

    generator = ResponseGenerator(
        client=FakeOpenAIClient(),
        model="gpt-4.1-mini"
    )

    with pytest.raises(ValueError):
        generator.generate_response(
            question="",
            context="Order is shipped"
        )


def test_empty_context():

    generator = ResponseGenerator(
        client=FakeOpenAIClient(),
        model="gpt-4.1-mini"
    )

    with pytest.raises(ValueError):
        generator.generate_response(
            question="Where is my order?",
            context=""
        )


def test_empty_llm_response():

    class EmptyResponses:

        def create(self, **kwargs):
            return SimpleNamespace(output_text="")

    class EmptyClient:
        responses = EmptyResponses()

    generator = ResponseGenerator(
        client=EmptyClient(),
        model="gpt-4.1-mini"
    )

    with pytest.raises(RuntimeError):
        generator.generate_response(
            question="Where is my order?",
            context="Order is shipped"
        )
