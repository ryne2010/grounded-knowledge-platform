from __future__ import annotations

import json
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
    classification: str
    retention: str
    tags_json: str
    content_sha256: str | None
    content_bytes: int
    num_chunks: int
    doc_version: int
    created_at: int
    updated_at: int

    @property
    def tags(self) -> list[str]:
        try:
            v = json.loads(self.tags_json or "[]")
            if isinstance(v, list):
                return [str(x) for x in v if str(x).strip()]
        except Exception:
            pass
        return []

    def to_dict(self) -> dict[str, object]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "source": self.source,
            "classification": self.classification,
            "retention": self.retention,
            "tags": self.tags,
            "content_sha256": self.content_sha256,
            "content_bytes": self.content_bytes,
            "num_chunks": self.num_chunks,
            "doc_version": self.doc_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    idx: int
    text: str


@dataclass(frozen=True)
class IngestEvent:
    event_id: str
    doc_id: str
    doc_version: int
    ingested_at: int
    content_sha256: str
    prev_content_sha256: str | None
    changed: int
    num_chunks: int
    embedding_backend: str
    embeddings_model: str
    embedding_dim: int
    chunk_size_chars: int
    chunk_overlap_chars: int
    notes: str | None

    @property
    def changed_bool(self) -> bool:
        return bool(self.changed)

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "doc_id": self.doc_id,
            "doc_version": self.doc_version,
            "ingested_at": self.ingested_at,
            "content_sha256": self.content_sha256,
            "prev_content_sha256": self.prev_content_sha256,
            "changed": self.changed_bool,
            "num_chunks": self.num_chunks,
            "embedding_backend": self.embedding_backend,
            "embeddings_model": self.embeddings_model,
            "embedding_dim": self.embedding_dim,
            "chunk_size_chars": self.chunk_size_chars,
            "chunk_overlap_chars": self.chunk_overlap_chars,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class IngestEventView:
    """A joined view of ingest events with doc metadata for UI/ops."""

    event_id: str
    doc_id: str
    doc_title: str
    doc_source: str
    classification: str
    retention: str
    tags_json: str

    doc_version: int
    ingested_at: int
    content_sha256: str
    prev_content_sha256: str | None
    changed: int
    num_chunks: int

    embedding_backend: str
    embeddings_model: str
    embedding_dim: int
    chunk_size_chars: int
    chunk_overlap_chars: int

    notes: str | None

    @property
    def tags(self) -> list[str]:
        try:
            v = json.loads(self.tags_json or "[]")
            if isinstance(v, list):
                return [str(x) for x in v if str(x).strip()]
        except Exception:
            pass
        return []

    @property
    def changed_bool(self) -> bool:
        return bool(self.changed)

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "doc_id": self.doc_id,
            "doc_title": self.doc_title,
            "doc_source": self.doc_source,
            "classification": self.classification,
            "retention": self.retention,
            "tags": self.tags,
            "doc_version": self.doc_version,
            "ingested_at": self.ingested_at,
            "content_sha256": self.content_sha256,
            "prev_content_sha256": self.prev_content_sha256,
            "changed": self.changed_bool,
            "num_chunks": self.num_chunks,
            "embedding_backend": self.embedding_backend,
            "embeddings_model": self.embeddings_model,
            "embedding_dim": self.embedding_dim,
            "chunk_size_chars": self.chunk_size_chars,
            "chunk_overlap_chars": self.chunk_overlap_chars,
            "notes": self.notes,
        }


def _ensure_parent_dir(sqlite_path: str) -> None:
    Path(os.path.dirname(sqlite_path) or ".").mkdir(parents=True, exist_ok=True)


@contextmanager
def connect(sqlite_path: str) -> Iterator[sqlite3.Connection]:
    _ensure_parent_dir(sqlite_path)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        # Safer defaults
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        conn.close()


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        cur = conn.execute(f"PRAGMA table_info({table})")
        return {str(r["name"]) for r in cur.fetchall()}
    except sqlite3.OperationalError:
        return set()


def _ensure_column(conn: sqlite3.Connection, table: str, col: str, col_def: str) -> None:
    cols = _existing_columns(conn, table)
    if col in cols:
        return
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
    except sqlite3.OperationalError:
        # Table may not exist yet or column add not supported in this context.
        return


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize (and lightly migrate) the SQLite schema.

    This project is intentionally simple (SQLite + single-process cache). To keep upgrades safe,
    `init_db` includes basic forward-only migrations for additive schema changes.
    """

    # --- Base tables (latest schema) ---
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS docs (
            doc_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            classification TEXT NOT NULL DEFAULT 'public',
            retention TEXT NOT NULL DEFAULT 'indefinite',
            tags_json TEXT NOT NULL DEFAULT '[]',
            content_sha256 TEXT,
            content_bytes INTEGER NOT NULL DEFAULT 0,
            num_chunks INTEGER NOT NULL DEFAULT 0,
            doc_version INTEGER NOT NULL DEFAULT 1,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
            updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
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
            FOREIGN KEY(doc_id) REFERENCES docs(doc_id) ON DELETE CASCADE
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            chunk_id TEXT PRIMARY KEY,
            dim INTEGER NOT NULL,
            vec BLOB NOT NULL,
            FOREIGN KEY(chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ingest_events (
            event_id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            doc_version INTEGER NOT NULL,
            ingested_at INTEGER NOT NULL,
            content_sha256 TEXT NOT NULL,
            prev_content_sha256 TEXT,
            changed INTEGER NOT NULL,
            num_chunks INTEGER NOT NULL,
            embedding_backend TEXT NOT NULL,
            embeddings_model TEXT NOT NULL,
            embedding_dim INTEGER NOT NULL,
            chunk_size_chars INTEGER NOT NULL,
            chunk_overlap_chars INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY(doc_id) REFERENCES docs(doc_id) ON DELETE CASCADE
        );
        """
    )

    # --- Key/value metadata (for index compatibility + lightweight migrations) ---
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )

    # --- Forward migrations for older DBs ---
    def _cols(table: str) -> set[str]:
        cur = conn.execute(f"PRAGMA table_info({table})")
        return {r["name"] for r in cur.fetchall()}

    if "docs" in {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}:
        cols = _cols("docs")
        # Additive columns (safe to add with defaults).
        if "classification" not in cols:
            conn.execute("ALTER TABLE docs ADD COLUMN classification TEXT NOT NULL DEFAULT 'public'")
        if "retention" not in cols:
            conn.execute("ALTER TABLE docs ADD COLUMN retention TEXT NOT NULL DEFAULT 'indefinite'")
        if "tags_json" not in cols:
            conn.execute("ALTER TABLE docs ADD COLUMN tags_json TEXT NOT NULL DEFAULT '[]'")
        if "content_sha256" not in cols:
            conn.execute("ALTER TABLE docs ADD COLUMN content_sha256 TEXT")
        if "content_bytes" not in cols:
            conn.execute("ALTER TABLE docs ADD COLUMN content_bytes INTEGER NOT NULL DEFAULT 0")
        if "num_chunks" not in cols:
            conn.execute("ALTER TABLE docs ADD COLUMN num_chunks INTEGER NOT NULL DEFAULT 0")
        if "doc_version" not in cols:
            conn.execute("ALTER TABLE docs ADD COLUMN doc_version INTEGER NOT NULL DEFAULT 1")
        if "created_at" not in cols:
            conn.execute("ALTER TABLE docs ADD COLUMN created_at INTEGER NOT NULL DEFAULT 0")
        if "updated_at" not in cols:
            conn.execute("ALTER TABLE docs ADD COLUMN updated_at INTEGER NOT NULL DEFAULT 0")

        # Backfill updated_at if it looks unset.
        try:
            conn.execute("UPDATE docs SET updated_at = created_at WHERE updated_at = 0 AND created_at != 0")
        except Exception:
            pass

    # --- Indexes ---
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_idx ON chunks(doc_id, idx)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_doc ON ingest_events(doc_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_doc_ver ON ingest_events(doc_id, doc_version)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_updated_at ON docs(updated_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_title ON docs(title)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_source ON docs(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_content_sha ON docs(content_sha256)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_classification ON docs(classification)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_retention ON docs(retention)")

    # --- Full-text search (optional) ---
    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(chunk_id, text, content='chunks', content_rowid='rowid', tokenize='porter');
            """
        )

        # Ensure triggers are correct.
        #
        # IMPORTANT: In external-content mode, the FTS rowid MUST match the content
        # table rowid, otherwise deletes/updates can leave stale index entries and
        # queries can return NULL/incorrect columns.
        # Version bump notes:
        # - v2: remove legacy double-population of FTS rows (prevents duplicate chunk_ids)
        expected_ver = "2"
        current_ver = get_meta(conn, "fts.schema_version")

        if current_ver != expected_ver:
            # Upgrade path: force-recreate triggers to fix older versions.
            conn.execute("DROP TRIGGER IF EXISTS chunks_ai")
            conn.execute("DROP TRIGGER IF EXISTS chunks_ad")
            conn.execute("DROP TRIGGER IF EXISTS chunks_au")
            conn.execute(
                """
                CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
                    INSERT INTO chunks_fts(rowid, chunk_id, text) VALUES (new.rowid, new.chunk_id, new.text);
                END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
                    INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, text) VALUES('delete', old.rowid, old.chunk_id, old.text);
                END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN
                    INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, text) VALUES('delete', old.rowid, old.chunk_id, old.text);
                    INSERT INTO chunks_fts(rowid, chunk_id, text) VALUES (new.rowid, new.chunk_id, new.text);
                END;
                """
            )
        else:
            # Normal path: keep init cheap on hot paths.
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                    INSERT INTO chunks_fts(rowid, chunk_id, text) VALUES (new.rowid, new.chunk_id, new.text);
                END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                    INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, text) VALUES('delete', old.rowid, old.chunk_id, old.text);
                END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                    INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, text) VALUES('delete', old.rowid, old.chunk_id, old.text);
                    INSERT INTO chunks_fts(rowid, chunk_id, text) VALUES (new.rowid, new.chunk_id, new.text);
                END;
                """
            )

        # Backfill / rebuild the FTS index when upgrading an older DB.
        #
        # When `chunks_fts` is created after rows already exist in `chunks`, triggers
        # won't retroactively populate the FTS index. Without a rebuild, lexical
        # retrieval and UI search appear broken even though FTS is enabled.
        needs_rebuild = current_ver != expected_ver
        if needs_rebuild:
            rebuilt_ok = False
            try:
                conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
                rebuilt_ok = True
            except Exception:
                # If the SQLite build lacks FTS5 support or rebuild fails, fall back.
                pass
            if rebuilt_ok:
                set_meta(conn, "fts.schema_version", expected_ver)
    except sqlite3.OperationalError:
        # FTS5 not available; lexical retrieval will fall back to rank_bm25
        pass

    conn.commit()


def upsert_doc(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    title: str,
    source: str,
    classification: str = "public",
    retention: str = "indefinite",
    tags_json: str = "[]",
    content_sha256: str | None = None,
    content_bytes: int = 0,
    num_chunks: int = 0,
    doc_version: int = 1,
) -> None:
    now = int(time.time())
    conn.execute(
        """
        INSERT INTO docs (
          doc_id, title, source,
          classification, retention, tags_json,
          content_sha256, content_bytes, num_chunks, doc_version,
          created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(doc_id) DO UPDATE SET
          title=excluded.title,
          source=excluded.source,
          classification=excluded.classification,
          retention=excluded.retention,
          tags_json=excluded.tags_json,
          content_sha256=excluded.content_sha256,
          content_bytes=excluded.content_bytes,
          num_chunks=excluded.num_chunks,
          doc_version=excluded.doc_version,
          updated_at=excluded.updated_at;
        """,
        (
            doc_id,
            title,
            source,
            classification,
            retention,
            tags_json,
            content_sha256,
            int(content_bytes),
            int(num_chunks),
            int(doc_version),
            now,
            now,
        ),
    )


def update_doc_metadata(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    title: str | None = None,
    source: str | None = None,
    classification: str | None = None,
    retention: str | None = None,
    tags_json: str | None = None,
) -> None:
    """Update doc metadata without altering content timestamps.

    IMPORTANT:
      - This intentionally does **not** touch `updated_at` so that retention policies
        continue to reflect the last *content ingest* time.
      - If you want auditability, add an explicit audit table/event (see TASK_AUTH / TASK_OTEL).
    """

    sets: list[str] = []
    params: list[object] = []

    if title is not None:
        sets.append("title=?")
        params.append(title)
    if source is not None:
        sets.append("source=?")
        params.append(source)
    if classification is not None:
        sets.append("classification=?")
        params.append(classification)
    if retention is not None:
        sets.append("retention=?")
        params.append(retention)
    if tags_json is not None:
        sets.append("tags_json=?")
        params.append(tags_json)

    if not sets:
        return

    params.append(doc_id)
    conn.execute(f"UPDATE docs SET {', '.join(sets)} WHERE doc_id=?", params)


def get_doc(conn: sqlite3.Connection, doc_id: str) -> Doc | None:
    cur = conn.execute(
        """
        SELECT doc_id, title, source, classification, retention, tags_json,
               content_sha256, content_bytes, num_chunks, doc_version, created_at, updated_at
        FROM docs
        WHERE doc_id=?
        """,
        (doc_id,),
    )
    row = cur.fetchone()
    return Doc(**dict(row)) if row is not None else None


def delete_doc_contents(conn: sqlite3.Connection, doc_id: str) -> None:
    """Remove old chunks/embeddings for re-ingest."""
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


def delete_doc(conn: sqlite3.Connection, doc_id: str) -> None:
    """Delete an entire doc, including chunks, embeddings, and ingest events."""
    delete_doc_contents(conn, doc_id)
    conn.execute("DELETE FROM ingest_events WHERE doc_id=?", (doc_id,))
    conn.execute("DELETE FROM docs WHERE doc_id=?", (doc_id,))


def insert_chunks(conn: sqlite3.Connection, chunks: Iterable[Chunk]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO chunks (chunk_id, doc_id, idx, text) VALUES (?, ?, ?, ?)",
        ((c.chunk_id, c.doc_id, c.idx, c.text) for c in chunks),
    )

    # FTS5 index is maintained via triggers when available; do not write to chunks_fts directly.


def insert_embeddings(conn: sqlite3.Connection, rows: Iterable[tuple[str, int, bytes]]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO embeddings (chunk_id, dim, vec) VALUES (?, ?, ?)",
        rows,
    )


def insert_ingest_event(conn: sqlite3.Connection, e: IngestEvent) -> None:
    conn.execute(
        """
        INSERT INTO ingest_events (
          event_id, doc_id, doc_version, ingested_at,
          content_sha256, prev_content_sha256, changed,
          num_chunks,
          embedding_backend, embeddings_model, embedding_dim,
          chunk_size_chars, chunk_overlap_chars,
          notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            e.event_id,
            e.doc_id,
            int(e.doc_version),
            int(e.ingested_at),
            e.content_sha256,
            e.prev_content_sha256,
            int(e.changed),
            int(e.num_chunks),
            e.embedding_backend,
            e.embeddings_model,
            int(e.embedding_dim),
            int(e.chunk_size_chars),
            int(e.chunk_overlap_chars),
            e.notes,
        ),
    )


def list_ingest_events(conn: sqlite3.Connection, doc_id: str, *, limit: int = 50) -> list[IngestEvent]:
    cur = conn.execute(
        """
        SELECT event_id, doc_id, doc_version, ingested_at,
               content_sha256, prev_content_sha256, changed,
               num_chunks,
               embedding_backend, embeddings_model, embedding_dim,
               chunk_size_chars, chunk_overlap_chars,
               notes
        FROM ingest_events
        WHERE doc_id=?
        ORDER BY ingested_at DESC
        LIMIT ?
        """,
        (doc_id, int(limit)),
    )
    return [IngestEvent(**dict(r)) for r in cur.fetchall()]


def list_recent_ingest_events(
    conn: sqlite3.Connection,
    *,
    limit: int = 100,
    doc_id: str | None = None,
) -> list[IngestEventView]:
    """List recent ingest events across docs (joined with doc metadata).

    This powers the UI's global ingest/audit view and is useful for ops debugging.
    """
    limit = max(1, min(int(limit), 500))
    if doc_id:
        cur = conn.execute(
            """
            SELECT
              e.event_id,
              e.doc_id,
              d.title AS doc_title,
              d.source AS doc_source,
              d.classification,
              d.retention,
              d.tags_json,
              e.doc_version,
              e.ingested_at,
              e.content_sha256,
              e.prev_content_sha256,
              e.changed,
              e.num_chunks,
              e.embedding_backend,
              e.embeddings_model,
              e.embedding_dim,
              e.chunk_size_chars,
              e.chunk_overlap_chars,
              e.notes
            FROM ingest_events e
            JOIN docs d ON d.doc_id = e.doc_id
            WHERE e.doc_id=?
            ORDER BY e.ingested_at DESC
            LIMIT ?
            """,
            (doc_id, limit),
        )
    else:
        cur = conn.execute(
            """
            SELECT
              e.event_id,
              e.doc_id,
              d.title AS doc_title,
              d.source AS doc_source,
              d.classification,
              d.retention,
              d.tags_json,
              e.doc_version,
              e.ingested_at,
              e.content_sha256,
              e.prev_content_sha256,
              e.changed,
              e.num_chunks,
              e.embedding_backend,
              e.embeddings_model,
              e.embedding_dim,
              e.chunk_size_chars,
              e.chunk_overlap_chars,
              e.notes
            FROM ingest_events e
            JOIN docs d ON d.doc_id = e.doc_id
            ORDER BY e.ingested_at DESC
            LIMIT ?
            """,
            (limit,),
        )

    return [IngestEventView(**dict(r)) for r in cur.fetchall()]


def list_docs(conn: sqlite3.Connection) -> list[Doc]:
    cur = conn.execute(
        """
        SELECT doc_id, title, source, classification, retention, tags_json,
               content_sha256, content_bytes, num_chunks, doc_version, created_at, updated_at
        FROM docs
        ORDER BY updated_at DESC
        """
    )
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


def get_chunk(conn: sqlite3.Connection, chunk_id: str) -> Chunk | None:
    cur = conn.execute("SELECT chunk_id, doc_id, idx, text FROM chunks WHERE chunk_id=?", (chunk_id,))
    row = cur.fetchone()
    return Chunk(**dict(row)) if row is not None else None


def list_chunks_for_doc(
    conn: sqlite3.Connection,
    doc_id: str,
    *,
    limit: int = 200,
    offset: int = 0,
) -> list[Chunk]:
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))
    cur = conn.execute(
        "SELECT chunk_id, doc_id, idx, text FROM chunks WHERE doc_id=? ORDER BY idx LIMIT ? OFFSET ?",
        (doc_id, limit, offset),
    )
    return [Chunk(**dict(r)) for r in cur.fetchall()]


def list_all_chunks_for_doc(
    conn: sqlite3.Connection,
    doc_id: str,
    *,
    limit: int = 5000,
) -> list[Chunk]:
    """Return *many* chunks for a doc (used for export/debug).

    This intentionally applies a hard upper bound so an API call can't
    accidentally materialize an unbounded amount of text in memory.
    """

    limit = max(1, min(int(limit), 20000))
    cur = conn.execute(
        "SELECT chunk_id, doc_id, idx, text FROM chunks WHERE doc_id=? ORDER BY idx LIMIT ?",
        (doc_id, limit),
    )
    return [Chunk(**dict(r)) for r in cur.fetchall()]


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    cur = conn.execute("SELECT value FROM meta WHERE key=?", (key,))
    row = cur.fetchone()
    if row is None:
        return None
    return str(row["value"])


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO meta(key, value)
        VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        (key, value),
    )
