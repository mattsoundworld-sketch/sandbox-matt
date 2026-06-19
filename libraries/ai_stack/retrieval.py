from __future__ import annotations

from .contracts import RetrievalResult


class InMemoryRetriever:
    """Minimal retrieval contract to keep app code decoupled from vector stores."""

    def __init__(self, documents: list[str]) -> None:
        self.documents = documents

    def search(self, query: str, top_k: int = 3) -> list[RetrievalResult]:
        query_terms = set(query.lower().split())
        scored: list[RetrievalResult] = []

        for doc in self.documents:
            doc_terms = set(doc.lower().split())
            overlap = len(query_terms.intersection(doc_terms))
            if overlap == 0:
                continue
            score = overlap / max(len(query_terms), 1)
            scored.append(RetrievalResult(content=doc, score=score, metadata={"source": "in-memory"}))

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]
