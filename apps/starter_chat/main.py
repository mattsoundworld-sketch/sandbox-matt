from __future__ import annotations

from pathlib import Path

from libraries.ai_stack import InMemoryRetriever, Message, MockModelClient


def run() -> None:
    retriever = InMemoryRetriever(
        documents=[
            "Use Polars and DuckDB for local analytics workflows.",
            "JSONL is useful for eval datasets and prompt regression records.",
            "Ollama enables local model experiments without cloud calls.",
        ]
    )

    query = "How should I store eval datasets?"
    hits = retriever.search(query)

    context = "\n".join(f"- {item.content}" for item in hits) or "- No relevant context"
    messages = [
        Message(role="system", content="Answer with practical recommendations."),
        Message(role="user", content=f"Question: {query}\nContext:\n{context}"),
    ]

    client = MockModelClient()
    result = client.run_and_log(messages, Path("data/processed/starter_chat_runs.jsonl"))

    print(result.text)


if __name__ == "__main__":
    run()
