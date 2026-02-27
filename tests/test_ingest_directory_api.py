from __future__ import annotations

import importlib
import os

import pytest
from fastapi.testclient import TestClient


_ENV_KEYS = [
    "SQLITE_PATH",
    "PUBLIC_DEMO_MODE",
    "AUTH_MODE",
    "API_KEYS_JSON",
    "ALLOW_CONNECTORS",
    "ALLOW_UPLOADS",
    "ALLOW_DOC_DELETE",
    "ALLOW_CHUNK_VIEW",
    "ALLOW_EVAL",
    "BOOTSTRAP_DEMO_CORPUS",
    "MAX_UPLOAD_BYTES",
]


@pytest.fixture(autouse=True)
def _restore_env_after_test():
    before = {k: os.environ.get(k) for k in _ENV_KEYS}
    yield
    for key, value in before.items():
        if value is None:
            os.environ.pop(key, None)
            continue
        os.environ[key] = value


def _reload_app(
    sqlite_path: str,
    *,
    public_demo_mode: bool,
    allow_uploads: bool,
    max_upload_bytes: int = 10_000_000,
) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "1" if public_demo_mode else "0"
    os.environ["AUTH_MODE"] = "api_key"
    os.environ["API_KEYS_JSON"] = '{"reader-key":"reader","editor-key":"editor","admin-key":"admin"}'
    os.environ["ALLOW_CONNECTORS"] = "1"
    os.environ["ALLOW_UPLOADS"] = "1" if allow_uploads else "0"
    os.environ["ALLOW_DOC_DELETE"] = "1"
    os.environ["ALLOW_CHUNK_VIEW"] = "1"
    os.environ["ALLOW_EVAL"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"
    os.environ["MAX_UPLOAD_BYTES"] = str(max_upload_bytes)

    import app.auth as auth
    import app.config as config
    import app.ingestion as ingestion
    import app.main as main
    import app.retrieval as retrieval
    import app.storage as storage

    importlib.reload(config)
    importlib.reload(auth)
    importlib.reload(storage)
    importlib.reload(ingestion)
    importlib.reload(retrieval)
    importlib.reload(main)
    return main


def _single_file_upload(path: str, payload: bytes) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [("files", (path, payload, "text/plain"))]


def test_directory_ingest_is_disabled_in_demo_and_when_uploads_disabled(tmp_path):
    demo_main = _reload_app(str(tmp_path / "dir_demo.sqlite"), public_demo_mode=True, allow_uploads=True)
    demo_client = TestClient(demo_main.app)
    demo_res = demo_client.post(
        "/api/ingest/directory",
        files=_single_file_upload("docs/a.txt", b"alpha"),
    )
    assert demo_res.status_code == 403
    assert "Uploads are disabled" in demo_res.text

    disabled_main = _reload_app(str(tmp_path / "dir_disabled.sqlite"), public_demo_mode=False, allow_uploads=False)
    disabled_client = TestClient(disabled_main.app)
    disabled_res = disabled_client.post(
        "/api/ingest/directory",
        headers={"X-API-Key": "editor-key"},
        files=_single_file_upload("docs/a.txt", b"alpha"),
    )
    assert disabled_res.status_code == 403
    assert "Uploads are disabled" in disabled_res.text


def test_directory_ingest_requires_editor_role(tmp_path):
    main = _reload_app(str(tmp_path / "dir_auth.sqlite"), public_demo_mode=False, allow_uploads=True)
    client = TestClient(main.app)

    res = client.post(
        "/api/ingest/directory",
        headers={"X-API-Key": "reader-key"},
        files=_single_file_upload("docs/a.txt", b"alpha"),
    )
    assert res.status_code == 403
    assert "editor role required" in res.text


def test_directory_ingest_requires_at_least_one_file(tmp_path):
    main = _reload_app(str(tmp_path / "dir_empty.sqlite"), public_demo_mode=False, allow_uploads=True)
    client = TestClient(main.app)

    res = client.post("/api/ingest/directory", headers={"X-API-Key": "editor-key"})
    assert res.status_code == 400
    assert "At least one file is required" in res.text


def test_directory_ingest_best_effort_mixed_results(tmp_path):
    main = _reload_app(
        str(tmp_path / "dir_mixed.sqlite"),
        public_demo_mode=False,
        allow_uploads=True,
        max_upload_bytes=8,
    )
    client = TestClient(main.app)

    files = [
        ("files", ("folder/a.txt", b"ok", "text/plain")),
        ("files", ("folder/big.txt", b"this-file-is-too-large", "text/plain")),
        ("files", ("folder/image.png", b"\x89PNG", "image/png")),
    ]
    res = client.post(
        "/api/ingest/directory",
        headers={"X-API-Key": "editor-key"},
        data={"source_prefix": "ui:directory"},
        files=files,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["scanned"] == 3
    assert body["ingested"] == 1
    assert body["changed"] == 1
    assert body["unchanged"] == 0
    assert body["skipped_unsupported"] == 1
    assert len(body["errors"]) >= 1

    by_path = {row["path"]: row for row in body["results"]}
    assert by_path["folder/a.txt"]["action"] == "changed"
    assert by_path["folder/big.txt"]["action"] == "error"
    assert by_path["folder/image.png"]["action"] == "skipped_unsupported"


def test_directory_ingest_is_idempotent_for_unchanged_files(tmp_path):
    main = _reload_app(str(tmp_path / "dir_idempotent.sqlite"), public_demo_mode=False, allow_uploads=True)
    client = TestClient(main.app)

    files = _single_file_upload("knowledge/a.txt", b"same-content")
    res1 = client.post(
        "/api/ingest/directory",
        headers={"X-API-Key": "editor-key"},
        data={"source_prefix": "ui:directory"},
        files=files,
    )
    assert res1.status_code == 200, res1.text
    body1 = res1.json()
    assert body1["changed"] == 1
    assert body1["unchanged"] == 0

    res2 = client.post(
        "/api/ingest/directory",
        headers={"X-API-Key": "editor-key"},
        data={"source_prefix": "ui:directory"},
        files=files,
    )
    assert res2.status_code == 200, res2.text
    body2 = res2.json()
    assert body2["changed"] == 0
    assert body2["unchanged"] == 1
    assert len(body2["results"]) == 1
    assert body2["results"][0]["action"] == "unchanged"

    docs_res = client.get("/api/docs", headers={"X-API-Key": "reader-key"})
    assert docs_res.status_code == 200, docs_res.text
    assert len(docs_res.json()["docs"]) == 1


def test_directory_ingest_creates_run_with_events_and_errors(tmp_path):
    main = _reload_app(
        str(tmp_path / "dir_run.sqlite"),
        public_demo_mode=False,
        allow_uploads=True,
        max_upload_bytes=8,
    )
    client = TestClient(main.app)

    files = [
        ("files", ("knowledge/a.txt", b"ok", "text/plain")),
        ("files", ("knowledge/big.txt", b"this-file-is-too-large", "text/plain")),
    ]
    res = client.post(
        "/api/ingest/directory",
        headers={"X-API-Key": "editor-key"},
        data={"source_prefix": "ui:directory"},
        files=files,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    run_id = str(body["run_id"])
    assert run_id

    detail_res = client.get(f"/api/ingestion-runs/{run_id}", headers={"X-API-Key": "reader-key"})
    assert detail_res.status_code == 200, detail_res.text
    detail = detail_res.json()
    run = detail["run"]
    assert run["trigger_type"] == "ui"
    assert run["trigger_payload"]["mode"] == "directory_upload"
    assert run["event_count"] == 1
    assert len(run["errors"]) >= 1
    assert "big.txt" in run["errors"][0]
    assert len(detail["events"]) == 1
