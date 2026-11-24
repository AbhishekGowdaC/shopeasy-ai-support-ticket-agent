
from pathlib import Path

import pytest

from app.knowledge_base.document_loader import (
    load_text_file,
    load_documents
)


def test_load_text_file(tmp_path):

    file_path = tmp_path / "policy.txt"

    file_path.write_text(
        "Customers can return products within 10 days.",
        encoding="utf-8"
    )

    document = load_text_file(str(file_path))

    assert document["document_name"] == "policy.txt"
    assert "10 days" in document["content"]


def test_load_multiple_documents(tmp_path):

    (tmp_path / "return.txt").write_text(
        "Return policy",
        encoding="utf-8"
    )

    (tmp_path / "refund.txt").write_text(
        "Refund policy",
        encoding="utf-8"
    )

    documents = load_documents(str(tmp_path))

    assert len(documents) == 2


def test_missing_file():

    with pytest.raises(FileNotFoundError):
        load_text_file("missing.txt")


def test_unsupported_file_format(tmp_path):

    file_path = tmp_path / "policy.pdf"

    file_path.write_text("Fake PDF", encoding="utf-8")

    with pytest.raises(ValueError):
        load_text_file(str(file_path))
