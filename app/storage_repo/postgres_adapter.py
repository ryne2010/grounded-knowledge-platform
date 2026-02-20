from __future__ import annotations

import time
import uuid
from importlib import import_module
from pathlib import Path

from .base import RepoCitation, RepoCounts


class PostgresRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self):
        try:
            psycopg = import_module("psycopg")
            rows_mod = import_module("psycopg.rows")
            dict_row = getattr(rows_mod, "dict_row")
        except Exception as e:  # pragma: no cover
            raise RuntimeError("PostgresRepository requires psycopg. Install with `uv sync --extra cloudsql`.") from e
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def init_schema(self) -> None:
        sql_path = Path(__file__).resolve().parents[1] / "migrations" / "postgres" / "001_init.sql"
        sql = sql_path.read_text(encoding="utf-8")
        with self._connect() as conn:
            with conn.cursor() as cur:
                # Execute as one script so procedural blocks (e.g. DO $$ ... $$) remain intact.
                cur.execute(sql)
            conn.commit()

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
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO docs (
                        doc_id, title, source, classification, retention, tags_json,
                        content_sha256, content_bytes, num_chunks, doc_version, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, 'internal', 'indefinite', '[]', %s, %s, %s, 1, %s, %s)
                    ON CONFLICT (doc_id) DO UPDATE SET
                      title = EXCLUDED.title,
                      source = EXCLUDED.source,
                      content_sha256 = EXCLUDED.content_sha256,
                      content_bytes = EXCLUDED.content_bytes,
                      num_chunks = EXCLUDED.num_chunks,
                      doc_version = docs.doc_version + 1,
                      updated_at = EXCLUDED.updated_at
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
                cur.execute("DELETE FROM ingest_events WHERE doc_id = %s", (doc_id,))
                cur.execute("DELETE FROM chunks WHERE doc_id = %s", (doc_id,))

                for idx, text in enumerate(chunks):
                    chunk_id = f"{doc_id}__{idx:05d}"
                    cur.execute(
                        "INSERT INTO chunks (chunk_id, doc_id, idx, text) VALUES (%s, %s, %s, %s)",
                        (chunk_id, doc_id, idx, text),
                    )
                    cur.execute(
                        "INSERT INTO embeddings (chunk_id, dim, vec) VALUES (%s, %s, %s)",
                        (chunk_id, embedding_dim, embeddings[idx]),
                    )

                cur.execute(
                    """
                    INSERT INTO ingest_events (
                      event_id, doc_id, doc_version, ingested_at, content_sha256,
                      prev_content_sha256, changed, num_chunks,
                      embedding_backend, embeddings_model, embedding_dim,
                      chunk_size_chars, chunk_overlap_chars, notes
                    )
                    VALUES (%s, %s, 1, %s, %s, NULL, 1, %s, 'hash', 'hash', %s, 1200, 200, 'postgres-repo')
                    """,
                    (str(uuid.uuid4()), doc_id, now, content_sha256, len(chunks), embedding_dim),
                )
            conn.commit()

    def query_citations(self, question: str, *, top_k: int = 3) -> list[RepoCitation]:
        tokens = [t.strip().lower() for t in question.split() if t.strip()]
        if not tokens:
            return []

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT chunk_id, doc_id, idx, text
                    FROM chunks
                    ORDER BY idx ASC
                    """
                )
                rows = cur.fetchall()

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
            with conn.cursor() as cur:
                cur.execute("DELETE FROM docs WHERE doc_id = %s", (doc_id,))
            conn.commit()

    def counts(self) -> RepoCounts:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(1) AS n FROM docs")
                docs = int(cur.fetchone()["n"])
                cur.execute("SELECT COUNT(1) AS n FROM chunks")
                chunks = int(cur.fetchone()["n"])
                cur.execute("SELECT COUNT(1) AS n FROM embeddings")
                emb = int(cur.fetchone()["n"])
                cur.execute("SELECT COUNT(1) AS n FROM ingest_events")
                events = int(cur.fetchone()["n"])
        return RepoCounts(docs=docs, chunks=chunks, embeddings=emb, ingest_events=events)
