import importlib
import os


def _reload_for_db(sqlite_path: str):
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["ALLOW_CHUNK_VIEW"] = "1"
    os.environ["SQLITE_PATH"] = sqlite_path

    import app.config as config

    importlib.reload(config)

    import app.storage as storage

    importlib.reload(storage)

    import app.ingestion as ingestion

    importlib.reload(ingestion)

    return ingestion, storage


def test_ingest_csv_file(tmp_path):
    db = tmp_path / "idx.sqlite"
    ingestion, storage = _reload_for_db(str(db))

    with storage.connect(str(db)) as conn:
        storage.init_db(conn)

    csv_path = tmp_path / "people.csv"
    csv_path.write_text("name,age\nAlice,30\nBob,40\n", encoding="utf-8")

    res = ingestion.ingest_file(
        csv_path,
        title="People",
        source="unit-test",
        classification="internal",
        retention="90d",
        tags=["csv", "test"],
        notes="seed",
    )

    assert res.doc_id
    assert res.num_chunks >= 1
    assert res.changed is True

    with storage.connect(str(db)) as conn:
        doc = storage.get_doc(conn, res.doc_id)
        assert doc is not None
        assert doc.title == "People"
        assert doc.classification == "internal"
        assert doc.retention == "90d"
        assert "csv" in doc.tags

        events = storage.list_ingest_events(conn, res.doc_id, limit=1)
        assert events
        assert "csv" in (events[0].notes or "")
