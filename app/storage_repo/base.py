from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RepoCitation:
    chunk_id: str
    doc_id: str
    idx: int
    quote: str


@dataclass(frozen=True)
class RepoCounts:
    docs: int
    chunks: int
    embeddings: int
    ingest_events: int


class StorageRepository(Protocol):
    """Repository interface used to decouple callers from SQLite SQL details."""

    def init_schema(self) -> None: ...

    def ingest_document(
        self,
        *,
        doc_id: str,
        title: str,
        source: str,
        content_sha256: str,
        chunks: list[str],
        embedding_dim: int,
        embeddings: list[bytes],
    ) -> None: ...

    def query_citations(self, question: str, *, top_k: int = 3) -> list[RepoCitation]: ...

    def delete_doc(self, doc_id: str) -> None: ...

    def counts(self) -> RepoCounts: ...
