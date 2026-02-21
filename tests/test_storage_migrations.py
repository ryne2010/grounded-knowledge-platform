import sqlite3
from pathlib import Path

from app.storage import connect, init_db


def test_init_db_migrates_older_docs_schema(tmp_path: Path):
    db_path = tmp_path / "old.sqlite"

    # Simulate a very old schema (docs table without newer columns).
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE docs (
            doc_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        "INSERT INTO docs(doc_id, title, source, created_at) VALUES(?, ?, ?, ?)",
        ("doc1", "Title", "Source", 1700000000),
    )
    conn.commit()
    conn.close()

    with connect(str(db_path)) as c:
        init_db(c)
        cols = {r["name"] for r in c.execute("PRAGMA table_info(docs)").fetchall()}

    # Newer columns should be present after migration.
    assert "classification" in cols
    assert "retention" in cols
    assert "tags_json" in cols
    assert "content_sha256" in cols
    assert "content_bytes" in cols
    assert "num_chunks" in cols
    assert "doc_version" in cols
    assert "updated_at" in cols


def test_init_db_migrates_ingest_events_schema(tmp_path: Path):
    db_path = tmp_path / "old_events.sqlite"

    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE docs (
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
            created_at INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE ingest_events (
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
            notes TEXT
        );
        """
    )
    conn.commit()
    conn.close()

    with connect(str(db_path)) as c:
        init_db(c)
        cols = {r["name"] for r in c.execute("PRAGMA table_info(ingest_events)").fetchall()}
        run_tables = {
            str(r["name"])
            for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingestion_runs'").fetchall()
        }
        run_cols = {r["name"] for r in c.execute("PRAGMA table_info(ingestion_runs)").fetchall()}

    assert "schema_fingerprint" in cols
    assert "contract_sha256" in cols
    assert "validation_status" in cols
    assert "validation_errors_json" in cols
    assert "schema_drifted" in cols
    assert "run_id" in cols
    assert "ingestion_runs" in run_tables
    assert "status" in run_cols
    assert "errors_json" in run_cols
