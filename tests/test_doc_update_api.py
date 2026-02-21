from __future__ import annotations

import importlib
import os

from fastapi.testclient import TestClient


def _reload_app(sqlite_path: str, *, public_demo_mode: bool, allow_uploads: bool) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "1" if public_demo_mode else "0"
    os.environ["AUTH_MODE"] = "none"
    os.environ["ALLOW_UPLOADS"] = "1" if allow_uploads else "0"
    os.environ.pop("API_KEYS_JSON", None)
    os.environ.pop("API_KEYS", None)
    os.environ.pop("API_KEY", None)

    # Ensure bootstrap doesn't inject demo docs.
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"

    import app.config as config
    import app.ingestion as ingestion
    import app.retrieval as retrieval
    import app.main as main

    importlib.reload(config)
    importlib.reload(ingestion)
    importlib.reload(retrieval)
    importlib.reload(main)
    return main


def test_doc_update_disabled_in_demo(tmp_path):
    main = _reload_app(str(tmp_path / "db.sqlite"), public_demo_mode=True, allow_uploads=True)
    client = TestClient(main.app)
    r = client.patch("/api/docs/does-not-matter", json={"title": "x"})
    assert r.status_code == 403


def test_doc_update_updates_metadata_without_touching_updated_at(tmp_path):
    main = _reload_app(str(tmp_path / "db.sqlite"), public_demo_mode=False, allow_uploads=True)
    client = TestClient(main.app)

    # Ingest a doc
    r = client.post(
        "/api/ingest/text",
        json={
            "title": "Test Doc",
            "source": "unit-test",
            "text": "hello world",
            "classification": "public",
            "retention": "indefinite",
            "tags": ["alpha"],
        },
    )
    assert r.status_code == 200, r.text
    doc_id = r.json()["doc_id"]

    # Capture timestamps
    r2 = client.get(f"/api/docs/{doc_id}")
    assert r2.status_code == 200
    before = r2.json()["doc"]["updated_at"]

    # Update metadata
    r3 = client.patch(
        f"/api/docs/{doc_id}",
        json={
            "title": "Renamed",
            "source": "unit-test",
            "classification": "internal",
            "retention": "90d",
            "tags": ["Hello World", "alpha"],
        },
    )
    assert r3.status_code == 200, r3.text
    doc = r3.json()["doc"]
    assert doc["title"] == "Renamed"
    assert doc["classification"] == "internal"
    assert doc["retention"] == "90d"
    # tag normalization: lowercase + non-alnum -> '-'
    assert doc["tags"] == ["hello-world", "alpha"]

    # Ensure updated_at did not change (retention clock remains tied to content ingest).
    r4 = client.get(f"/api/docs/{doc_id}")
    assert r4.status_code == 200
    after = r4.json()["doc"]["updated_at"]
    assert after == before
