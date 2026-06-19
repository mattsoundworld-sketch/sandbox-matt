from pathlib import Path

from libraries.ai_stack import InMemoryRetriever, Message, MockModelClient, dump_jsonl, load_jsonl


def test_jsonl_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl"
    records = [{"id": 1, "topic": "json"}, {"id": 2, "topic": "parquet"}]

    dump_jsonl(path, records)
    loaded = load_jsonl(path)

    assert loaded == records


def test_retriever_ranks_matching_documents() -> None:
    retriever = InMemoryRetriever(
        documents=[
            "JSONL is good for eval fixtures",
            "Parquet is efficient for analytics",
            "Use Polars and DuckDB together",
        ]
    )

    results = retriever.search("eval fixtures", top_k=2)

    assert len(results) >= 1
    assert "eval fixtures" in results[0].content.lower()


def test_mock_client_logs_run(tmp_path: Path) -> None:
    output = tmp_path / "runs.jsonl"
    client = MockModelClient(provider="mock", model="echo-v1")

    response = client.run_and_log(
        [Message(role="user", content="What is JSONL used for?")],
        output,
    )

    assert response.provider == "mock"
    assert output.exists()
    rows = load_jsonl(output)
    assert len(rows) == 1
    assert "response" in rows[0]
