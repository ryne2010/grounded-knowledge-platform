import sqlite3

import pytest

from app.storage import Chunk, init_db, insert_chunks


def test_fts_backfill_rebuilds_when_chunks_exist(tmp_path):
    """If a DB already has chunks before FTS is created, init_db should rebuild the index."""

    db_path = tmp_path / "t.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Simulate an older schema: docs + chunks exist, but chunks_fts does not.
    conn.execute("CREATE TABLE docs (doc_id TEXT PRIMARY KEY, title TEXT NOT NULL, source TEXT NOT NULL)")
    conn.execute(
        "CREATE TABLE chunks (chunk_id TEXT PRIMARY KEY, doc_id TEXT NOT NULL, idx INTEGER NOT NULL, text TEXT NOT NULL)"
    )
    conn.execute("INSERT INTO docs(doc_id, title, source) VALUES ('d1', 'Doc 1', 'unit-test')")
    conn.execute("INSERT INTO chunks(chunk_id, doc_id, idx, text) VALUES ('c1', 'd1', 0, 'hello world')")
    conn.commit()

    # Upgrade/init.
    init_db(conn)

    # Some SQLite builds may not include FTS5; skip in that case.
    try:
        n_fts = int(conn.execute("SELECT COUNT(1) AS n FROM chunks_fts").fetchone()["n"])
    except sqlite3.OperationalError:
        pytest.skip("SQLite FTS5 not available")

    assert n_fts == 1

    # And the index should be queryable.
    rows = conn.execute("SELECT chunk_id FROM chunks_fts WHERE chunks_fts MATCH ?", ("hello",)).fetchall()
    assert rows, "expected at least one FTS match"
    assert rows[0]["chunk_id"] == "c1"


def test_fts_triggers_use_rowid_and_stay_consistent(tmp_path):
    """Insert+delete should keep FTS row counts in sync with chunks."""

    db_path = tmp_path / "t2.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    init_db(conn)

    # If FTS isn't available, this test isn't meaningful.
    try:
        conn.execute("SELECT 1 FROM chunks_fts LIMIT 1").fetchone()
    except sqlite3.OperationalError:
        pytest.skip("SQLite FTS5 not available")

    conn.execute("INSERT INTO docs(doc_id, title, source) VALUES ('d1', 'Doc 1', 'unit-test')")
    conn.execute("INSERT INTO chunks(chunk_id, doc_id, idx, text) VALUES ('c1', 'd1', 0, 'alpha beta')")
    conn.execute("INSERT INTO chunks(chunk_id, doc_id, idx, text) VALUES ('c2', 'd1', 1, 'gamma delta')")
    conn.commit()

    n_chunks = int(conn.execute("SELECT COUNT(1) AS n FROM chunks").fetchone()["n"])
    n_fts = int(conn.execute("SELECT COUNT(1) AS n FROM chunks_fts").fetchone()["n"])
    assert n_fts == n_chunks

    # Delete a chunk; triggers should delete from FTS.
    conn.execute("DELETE FROM chunks WHERE chunk_id='c1'")
    conn.commit()

    n_chunks2 = int(conn.execute("SELECT COUNT(1) AS n FROM chunks").fetchone()["n"])
    n_fts2 = int(conn.execute("SELECT COUNT(1) AS n FROM chunks_fts").fetchone()["n"])
    assert n_fts2 == n_chunks2


def test_insert_chunks_does_not_double_populate_fts(tmp_path):
    """insert_chunks should rely on triggers and not create duplicate FTS rows."""

    db_path = tmp_path / "t3.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    init_db(conn)

    # If FTS isn't available, this test isn't meaningful.
    try:
        conn.execute("SELECT 1 FROM chunks_fts LIMIT 1").fetchone()
    except sqlite3.OperationalError:
        pytest.skip("SQLite FTS5 not available")

    conn.execute("INSERT INTO docs(doc_id, title, source) VALUES ('d1', 'Doc 1', 'unit-test')")
    chunks = [
        Chunk(chunk_id="c1", doc_id="d1", idx=0, text="alpha beta"),
        Chunk(chunk_id="c2", doc_id="d1", idx=1, text="gamma delta"),
    ]
    insert_chunks(conn, chunks)
    conn.commit()

    n_chunks = int(conn.execute("SELECT COUNT(1) AS n FROM chunks").fetchone()["n"])
    n_fts = int(conn.execute("SELECT COUNT(1) AS n FROM chunks_fts").fetchone()["n"])
    assert n_fts == n_chunks
