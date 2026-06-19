from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Message:
    role: str
    content: str


@dataclass(slots=True)
class ModelResponse:
    text: str
    provider: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalResult:
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
