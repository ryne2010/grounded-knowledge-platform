from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    doc_id: str
    idx: int
    quote: str


@dataclass(frozen=True)
class Answer:
    text: str
    citations: list[Citation]
    refused: bool = False
    provider: str = "unknown"


class AnswerProvider(Protocol):
    name: str

    def answer(self, question: str, context: list[tuple[str, str, int, str]]) -> Answer:
        """
        context entries are (chunk_id, doc_id, idx, text)
        """
        ...
