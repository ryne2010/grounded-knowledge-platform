import importlib
import os


def _reload_for_db(sqlite_path: str):
    os.environ["SQLITE_PATH"] = sqlite_path
    import app.config as config

    importlib.reload(config)

    import app.storage as storage

    importlib.reload(storage)

    import app.ingestion as ingestion

    importlib.reload(ingestion)

    return ingestion, storage


def test_ingest_records_lineage_event(tmp_path):
    db = tmp_path / "idx.sqlite"
    ingestion, storage = _reload_for_db(str(db))

    with storage.connect(str(db)) as conn:
        storage.init_db(conn)

    res = ingestion.ingest_text(title="Title", source="src", text="Hello world")

    with storage.connect(str(db)) as conn:
        d = storage.get_doc(conn, res.doc_id)
        assert d is not None
        assert d.doc_version >= 1

        events = storage.list_ingest_events(conn, res.doc_id)
        assert len(events) >= 1
        assert events[0].doc_id == res.doc_id
        assert events[0].doc_version == d.doc_version
