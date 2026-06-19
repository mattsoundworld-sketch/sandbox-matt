from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .contracts import Message, ModelResponse
from .json_contracts import dump_jsonl


class MockModelClient:
    """Simple provider-agnostic client shape for early learning iterations."""

    def __init__(self, provider: str = "mock", model: str = "echo-v1") -> None:
        self.provider = provider
        self.model = model

    def generate(self, messages: list[Message]) -> ModelResponse:
        joined = "\n".join(f"{msg.role}: {msg.content}" for msg in messages)
        return ModelResponse(
            text=f"Echo response based on input:\n{joined}",
            provider=self.provider,
            model=self.model,
            usage={"input_messages": len(messages), "output_tokens": len(joined.split())},
        )

    def run_and_log(self, messages: list[Message], output_path: str | Path) -> ModelResponse:
        response = self.generate(messages)
        payload = {
            "messages": [asdict(item) for item in messages],
            "response": asdict(response),
        }
        dump_jsonl(output_path, [payload])
        return response
