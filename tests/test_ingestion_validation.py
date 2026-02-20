import importlib
import os


def _reload_for_db(sqlite_path: str):
    os.environ["SQLITE_PATH"] = sqlite_path
    # Reload config first, then modules that import settings.
    import app.config as config

    importlib.reload(config)

    import app.storage as storage

    importlib.reload(storage)

    import app.ingestion as ingestion

    importlib.reload(ingestion)

    return ingestion, storage


def test_ingest_text_rejects_invalid_classification(tmp_path):
    db = tmp_path / "idx.sqlite"
    ingestion, storage = _reload_for_db(str(db))

    with storage.connect(str(db)) as conn:
        storage.init_db(conn)

    try:
        ingestion.ingest_text(title="t", source="s", text="x", classification="SECRET")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "Invalid classification" in str(e)


def test_ingest_text_rejects_invalid_retention(tmp_path):
    db = tmp_path / "idx.sqlite"
    ingestion, storage = _reload_for_db(str(db))

    with storage.connect(str(db)) as conn:
        storage.init_db(conn)

    try:
        ingestion.ingest_text(title="t", source="s", text="x", retention="forever")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "Invalid retention" in str(e)
