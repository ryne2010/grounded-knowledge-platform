from __future__ import annotations

import os
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


@dataclass(frozen=True)
class Doc:
    doc_id: str
    title: str
    source: str
    created_at: int


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    idx: int
    text: str


def _ensure_parent_dir(sqlite_path: str) -> None:
    Path(os.path.dirname(sqlite_path) or ".").mkdir(parents=True, exist_ok=True)


@contextmanager
def connect(sqlite_path: str) -> Iterator[sqlite3.Connection]:
    _ensure_parent_dir(sqlite_path)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS docs (
          doc_id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          source TEXT NOT NULL,
          created_at INTEGER NOT NULL
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
          chunk_id TEXT PRIMARY KEY,
          doc_id TEXT NOT NULL,
          idx INTEGER NOT NULL,
          text TEXT NOT NULL,
          FOREIGN KEY(doc_id) REFERENCES docs(doc_id)
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
          chunk_id TEXT PRIMARY KEY,
          dim INTEGER NOT NULL,
          vec BLOB NOT NULL,
          FOREIGN KEY(chunk_id) REFERENCES chunks(chunk_id)
        );
        """
    )

    # Full text search (optional depending on sqlite build)
    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
              chunk_id UNINDEXED,
              text,
              tokenize='porter'
            );
            """
        )
    except sqlite3.OperationalError:
        # FTS5 not available; lexical retrieval will fall back to rank_bm25
        pass

    conn.commit()


def upsert_doc(conn: sqlite3.Connection, doc_id: str, title: str, source: str) -> None:
    now = int(time.time())
    conn.execute(
        """
        INSERT INTO docs (doc_id, title, source, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(doc_id) DO UPDATE SET
          title=excluded.title,
          source=excluded.source;
        """,
        (doc_id, title, source, now),
    )


def delete_doc_contents(conn: sqlite3.Connection, doc_id: str) -> None:
    # Remove old chunks/embeddings for re-ingest.
    # We collect chunk_ids first so we can also delete from FTS if present.
    cur = conn.execute("SELECT chunk_id FROM chunks WHERE doc_id=?", (doc_id,))
    chunk_ids = [r["chunk_id"] for r in cur.fetchall()]

    if chunk_ids:
        placeholders = ",".join(["?"] * len(chunk_ids))
        conn.execute(
            f"DELETE FROM embeddings WHERE chunk_id IN ({placeholders})",
            chunk_ids,
        )

        try:
            conn.execute(
                f"DELETE FROM chunks_fts WHERE chunk_id IN ({placeholders})",
                chunk_ids,
            )
        except sqlite3.OperationalError:
            # FTS table may not exist
            pass

    conn.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))


def insert_chunks(conn: sqlite3.Connection, chunks: Iterable[Chunk]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO chunks (chunk_id, doc_id, idx, text) VALUES (?, ?, ?, ?)",
        ((c.chunk_id, c.doc_id, c.idx, c.text) for c in chunks),
    )

    # Keep FTS in sync when available
    try:
        conn.executemany(
            "INSERT OR REPLACE INTO chunks_fts (chunk_id, text) VALUES (?, ?)",
            ((c.chunk_id, c.text) for c in chunks),
        )
    except sqlite3.OperationalError:
        pass


def insert_embeddings(conn: sqlite3.Connection, rows: Iterable[tuple[str, int, bytes]]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO embeddings (chunk_id, dim, vec) VALUES (?, ?, ?)",
        rows,
    )


def list_docs(conn: sqlite3.Connection) -> list[Doc]:
    cur = conn.execute("SELECT doc_id, title, source, created_at FROM docs ORDER BY created_at DESC")
    return [Doc(**dict(r)) for r in cur.fetchall()]


def list_chunks(conn: sqlite3.Connection) -> list[Chunk]:
    cur = conn.execute("SELECT chunk_id, doc_id, idx, text FROM chunks ORDER BY doc_id, idx")
    return [Chunk(**dict(r)) for r in cur.fetchall()]


def get_chunks_by_ids(conn: sqlite3.Connection, chunk_ids: list[str]) -> list[Chunk]:
    if not chunk_ids:
        return []
    placeholders = ",".join(["?"] * len(chunk_ids))
    cur = conn.execute(
        f"SELECT chunk_id, doc_id, idx, text FROM chunks WHERE chunk_id IN ({placeholders})",
        chunk_ids,
    )
    rows = [Chunk(**dict(r)) for r in cur.fetchall()]
    # Preserve requested order
    by_id = {c.chunk_id: c for c in rows}
    return [by_id[cid] for cid in chunk_ids if cid in by_id]


def get_embeddings_by_ids(conn: sqlite3.Connection, chunk_ids: list[str]) -> list[tuple[str, int, bytes]]:
    if not chunk_ids:
        return []
    placeholders = ",".join(["?"] * len(chunk_ids))
    cur = conn.execute(
        f"SELECT chunk_id, dim, vec FROM embeddings WHERE chunk_id IN ({placeholders})",
        chunk_ids,
    )
    rows = [(r["chunk_id"], r["dim"], r["vec"]) for r in cur.fetchall()]
    by_id = {cid: (cid, dim, vec) for cid, dim, vec in rows}
    return [by_id[cid] for cid in chunk_ids if cid in by_id]
