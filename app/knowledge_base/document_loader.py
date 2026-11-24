
from pathlib import Path


def load_text_file(file_path: str) -> dict:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    if path.suffix.lower() != ".txt":
        raise ValueError(
            "Only TXT files are supported currently"
        )

    text = path.read_text(encoding="utf-8")

    return {
        "document_name": path.name,
        "content": text,
        "source": str(path)
    }


def load_documents(directory: str) -> list:

    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(
            f"Directory not found: {directory}"
        )

    documents = []

    for file_path in directory_path.glob("*.txt"):

        document = load_text_file(str(file_path))

        documents.append(document)

    return documents
