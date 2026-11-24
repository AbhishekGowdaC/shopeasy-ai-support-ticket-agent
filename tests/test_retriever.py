
import pytest

from app.knowledge_base.retriever import BM25Retriever


def test_retrieve_relevant_chunk():
    chunks = [
        "Customers can return eligible products in good condition.",
        "Approved refunds are processed within 5 to 7 business days.",
        "Customers can reset their account password using email."
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.retrieve(
        "refund processed",
        top_k=1
    )

    assert len(results) == 1
    assert "refund" in results[0]["chunk"].lower()


def test_retrieve_top_k():
    chunks = [
        "Refunds take 5 to 7 days.",
        "Refunds require product inspection.",
        "Customers can return products within 10 days."
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.retrieve("refund", top_k=2)

    assert len(results) == 2


def test_empty_query():
    retriever = BM25Retriever(["Refund policy information"])

    assert retriever.retrieve("") == []


def test_empty_chunks():
    with pytest.raises(ValueError):
        BM25Retriever([])


def test_invalid_top_k():
    retriever = BM25Retriever(["Refund policy information"])

    with pytest.raises(ValueError):
        retriever.retrieve("refund", top_k=0)
