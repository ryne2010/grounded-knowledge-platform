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
