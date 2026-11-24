
import pytest

from app.knowledge_base.chunker import chunk_text


def test_chunk_text_returns_multiple_chunks():
    text = "A" * 1000

    chunks = chunk_text(text, chunk_size=500, overlap=50)

    assert len(chunks) == 3


def test_chunk_overlap():
    text = "A" * 1000

    chunks = chunk_text(text, chunk_size=500, overlap=50)

    assert chunks[0][-50:] == chunks[1][:50]


def test_empty_text():
    assert chunk_text("") == []


def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("Hello", chunk_size=0)


def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("Hello", chunk_size=100, overlap=100)
