from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path

from .base import RepoCitation, RepoCounts


class SQLiteRepository:
    def __init__(self, sqlite_path: str) -> None:
        self.sqlite_path = sqlite_path
        Path(Path(sqlite_path).parent).mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_schema(self) -> None:
        from app.storage import init_db

        with self._connect() as conn:
            init_db(conn)

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
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")

        now = int(time.time())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO docs (
                    doc_id, title, source, classification, retention, tags_json,
                    content_sha256, content_bytes, num_chunks, doc_version, created_at, updated_at
                ) VALUES (?, ?, ?, 'internal', 'indefinite', '[]', ?, ?, ?, 1, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    title=excluded.title,
                    source=excluded.source,
                    content_sha256=excluded.content_sha256,
                    content_bytes=excluded.content_bytes,
                    num_chunks=excluded.num_chunks,
                    doc_version=docs.doc_version + 1,
                    updated_at=excluded.updated_at
                """,
                (
                    doc_id,
                    title,
                    source,
                    content_sha256,
                    sum(len(c.encode("utf-8")) for c in chunks),
                    len(chunks),
                    now,
                    now,
                ),
            )
            conn.execute(
                "DELETE FROM embeddings WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id=?)", (doc_id,)
            )
            conn.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
            conn.execute("DELETE FROM ingest_events WHERE doc_id=?", (doc_id,))

            for idx, text in enumerate(chunks):
                chunk_id = f"{doc_id}__{idx:05d}"
                conn.execute(
                    "INSERT INTO chunks (chunk_id, doc_id, idx, text) VALUES (?, ?, ?, ?)",
                    (chunk_id, doc_id, idx, text),
                )
                conn.execute(
                    "INSERT INTO embeddings (chunk_id, dim, vec) VALUES (?, ?, ?)",
                    (chunk_id, embedding_dim, embeddings[idx]),
                )

            conn.execute(
                """
                INSERT INTO ingest_events (
                    event_id, doc_id, doc_version, ingested_at, content_sha256,
                    prev_content_sha256, changed, num_chunks,
                    embedding_backend, embeddings_model, embedding_dim,
                    chunk_size_chars, chunk_overlap_chars, notes
                ) VALUES (?, ?, 1, ?, ?, NULL, 1, ?, 'hash', 'hash', ?, 1200, 200, 'sqlite-repo')
                """,
                (str(uuid.uuid4()), doc_id, now, content_sha256, len(chunks), embedding_dim),
            )
            conn.commit()

    def query_citations(self, question: str, *, top_k: int = 3) -> list[RepoCitation]:
        tokens = [t.strip().lower() for t in question.split() if t.strip()]
        if not tokens:
            return []

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT chunk_id, doc_id, idx, text
                FROM chunks
                ORDER BY idx ASC
                """,
            ).fetchall()

        scored: list[tuple[int, RepoCitation]] = []
        for r in rows:
            text = str(r["text"] or "")
            hay = text.lower()
            score = sum(1 for t in tokens if t in hay)
            if score <= 0:
                continue
            scored.append(
                (
                    score,
                    RepoCitation(
                        chunk_id=str(r["chunk_id"]),
                        doc_id=str(r["doc_id"]),
                        idx=int(r["idx"]),
                        quote=text[:300],
                    ),
                )
            )
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[: max(1, int(top_k))]]

    def delete_doc(self, doc_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM docs WHERE doc_id=?", (doc_id,))
            conn.commit()

    def counts(self) -> RepoCounts:
        with self._connect() as conn:
            docs = int(conn.execute("SELECT COUNT(1) AS n FROM docs").fetchone()["n"])
            chunks = int(conn.execute("SELECT COUNT(1) AS n FROM chunks").fetchone()["n"])
            emb = int(conn.execute("SELECT COUNT(1) AS n FROM embeddings").fetchone()["n"])
            events = int(conn.execute("SELECT COUNT(1) AS n FROM ingest_events").fetchone()["n"])
        return RepoCounts(docs=docs, chunks=chunks, embeddings=emb, ingest_events=events)
