
import re
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


class BM25Retriever:

    def __init__(self, chunks: list[str]):
        if not chunks:
            raise ValueError("Chunks cannot be empty")

        self.chunks = chunks

        tokenized_chunks = [
            tokenize(chunk)
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(tokenized_chunks)

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:

        if not query.strip():
            return []

        if top_k <= 0:
            raise ValueError("top_k must be positive")

        tokenized_query = tokenize(query)

        scores = self.bm25.get_scores(tokenized_query)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True
        )

        results = []

        for index in ranked_indices[:top_k]:
            results.append({
                "chunk": self.chunks[index],
                "score": float(scores[index])
            })

        return results
