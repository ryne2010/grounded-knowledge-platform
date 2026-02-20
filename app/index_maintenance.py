from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass

import numpy as np

from .config import settings
from .embeddings import Embedder, HASH_EMBEDDER_VERSION
from .storage import get_meta, set_meta

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IndexSignature:
    embeddings_backend: str
    embeddings_model: str
    embedding_dim: int
    hash_embedder_version: int
    chunk_size_chars: int
    chunk_overlap_chars: int

    def to_meta(self) -> dict[str, str]:
        return {
            "index.embeddings_backend": self.embeddings_backend,
            "index.embeddings_model": self.embeddings_model,
            "index.embedding_dim": str(self.embedding_dim),
            "index.hash_embedder_version": str(self.hash_embedder_version),
            "index.chunk_size_chars": str(self.chunk_size_chars),
            "index.chunk_overlap_chars": str(self.chunk_overlap_chars),
        }

    @staticmethod
    def from_meta(meta: dict[str, str]) -> "IndexSignature":
        return IndexSignature(
            embeddings_backend=meta.get("index.embeddings_backend", ""),
            embeddings_model=meta.get("index.embeddings_model", ""),
            embedding_dim=int(meta.get("index.embedding_dim", "0") or 0),
            hash_embedder_version=int(meta.get("index.hash_embedder_version", "0") or 0),
            chunk_size_chars=int(meta.get("index.chunk_size_chars", "0") or 0),
            chunk_overlap_chars=int(meta.get("index.chunk_overlap_chars", "0") or 0),
        )


def _current_signature(embedder: Embedder) -> IndexSignature:
    backend = settings.embeddings_backend
    model = settings.embeddings_model
    dim = int(getattr(embedder, "dim", 0) or 0)
    hash_ver = HASH_EMBEDDER_VERSION if backend == "hash" else 0
    return IndexSignature(
        embeddings_backend=backend,
        embeddings_model=model,
        embedding_dim=dim,
        hash_embedder_version=hash_ver,
        chunk_size_chars=int(settings.chunk_size_chars),
        chunk_overlap_chars=int(settings.chunk_overlap_chars),
    )


def _load_signature(conn: sqlite3.Connection) -> IndexSignature | None:
    keys = [
        "index.embeddings_backend",
        "index.embeddings_model",
        "index.embedding_dim",
        "index.hash_embedder_version",
        "index.chunk_size_chars",
        "index.chunk_overlap_chars",
    ]
    meta: dict[str, str] = {}
    for k in keys:
        v = get_meta(conn, k)
        if v is not None:
            meta[k] = v
    if not meta:
        return None
    return IndexSignature.from_meta(meta)


def _write_signature(conn: sqlite3.Connection, sig: IndexSignature) -> None:
    for k, v in sig.to_meta().items():
        set_meta(conn, k, v)


def _count_chunks(conn: sqlite3.Connection) -> int:
    cur = conn.execute("SELECT COUNT(1) AS n FROM chunks")
    row = cur.fetchone()
    return int(row["n"]) if row is not None else 0


def _rebuild_all_embeddings(conn: sqlite3.Connection, embedder: Embedder) -> int:
    """Recompute embeddings for all chunks currently in the DB.

    Returns the number of embeddings written.
    """

    # Clear existing vectors first so we don't end up in a partial-mismatch state.
    conn.execute("DELETE FROM embeddings")

    cur = conn.execute("SELECT chunk_id, text FROM chunks ORDER BY doc_id, idx")

    batch_size = 256
    written = 0
    while True:
        batch_rows = cur.fetchmany(batch_size)
        if not batch_rows:
            break
        chunk_ids = [str(r["chunk_id"]) for r in batch_rows]
        texts = [str(r["text"]) for r in batch_rows]
        embs = embedder.embed(texts)
        if embs.size == 0:
            continue
        dim = int(embs.shape[1])
        payload = [(cid, dim, vec.astype(np.float32).tobytes()) for cid, vec in zip(chunk_ids, embs, strict=True)]
        conn.executemany("INSERT INTO embeddings(chunk_id, dim, vec) VALUES(?, ?, ?)", payload)
        written += len(payload)

    return written


def ensure_index_compatible(conn: sqlite3.Connection, embedder: Embedder) -> bool:
    """Ensure the persisted SQLite index matches the current runtime settings.

    Why this exists:
    - The project persists embeddings in SQLite.
    - If you change EMBEDDINGS_BACKEND / EMBEDDINGS_MODEL / EMBEDDING_DIM (or the hash algorithm)
      and keep the same DB file, retrieval quality collapses because query vectors and stored vectors
      are no longer comparable.

    Strategy:
    - Store an "index signature" in the `meta` table.
    - On mismatch, rebuild embeddings in-place from the stored chunk texts.

    Returns True if a rebuild/cleanup happened.
    """

    current = _current_signature(embedder)
    stored = _load_signature(conn)

    # If DB is empty, just record the signature.
    if _count_chunks(conn) == 0:
        _write_signature(conn, current)
        return False

    def embedding_sig(s: IndexSignature) -> tuple[object, ...]:
        return (
            s.embeddings_backend,
            s.embeddings_model,
            s.embedding_dim,
            s.hash_embedder_version,
        )

    def chunking_sig(s: IndexSignature) -> tuple[object, ...]:
        return (s.chunk_size_chars, s.chunk_overlap_chars)

    # Embeddings disabled: ensure table is empty + record signature.
    if current.embeddings_backend == "none":
        cur = conn.execute("SELECT COUNT(1) AS n FROM embeddings")
        row = cur.fetchone()
        n = int(row["n"]) if row is not None else 0
        if n:
            logger.info("Embeddings disabled; clearing %s stored embedding rows", n)
            conn.execute("DELETE FROM embeddings")
        _write_signature(conn, current)
        return bool(n)

    # Missing signature: treat as mismatch (older DB).
    if stored is None:
        logger.info("Index signature missing; rebuilding embeddings for compatibility")
        written = _rebuild_all_embeddings(conn, embedder)
        _write_signature(conn, current)
        logger.info("Rebuilt %s embeddings (signature initialized)", written)
        return True

    if embedding_sig(stored) != embedding_sig(current):
        logger.warning(
            "Index signature mismatch; rebuilding embeddings. stored=%s current=%s",
            stored,
            current,
        )
        written = _rebuild_all_embeddings(conn, embedder)
        _write_signature(conn, current)
        logger.info("Rebuilt %s embeddings (signature updated)", written)
        return True

    # Chunking configuration changed. Chunks are stored as text already, so we don't rebuild embeddings
    # here — but we DO update the signature so diagnostics reflect the current runtime settings.
    if chunking_sig(stored) != chunking_sig(current):
        logger.info("Chunking settings changed; updating index signature (no embedding rebuild)")
        _write_signature(conn, current)

    return False
