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
    "API_KEYS",
    "API_KEY",
    "ALLOW_UPLOADS",
    "ALLOW_DOC_DELETE",
    "ALLOW_CHUNK_VIEW",
    "ALLOW_EVAL",
    "BOOTSTRAP_DEMO_CORPUS",
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
    public_demo_mode: bool = False,
    auth_mode: str = "api_key",
    api_keys_json: str = '{"reader-key":"reader","admin-key":"admin"}',
    allow_uploads: bool = True,
    allow_doc_delete: bool = True,
) -> object:
    env_overrides = {
        "SQLITE_PATH": sqlite_path,
        "PUBLIC_DEMO_MODE": "1" if public_demo_mode else "0",
        "AUTH_MODE": auth_mode,
        "API_KEYS_JSON": api_keys_json,
        "ALLOW_UPLOADS": "1" if allow_uploads else "0",
        "ALLOW_DOC_DELETE": "1" if allow_doc_delete else "0",
        "ALLOW_CHUNK_VIEW": "1",
        "ALLOW_EVAL": "1",
        "BOOTSTRAP_DEMO_CORPUS": "0",
    }
    for key, value in env_overrides.items():
        os.environ[key] = value

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


def test_api_key_missing_returns_401(tmp_path):
    main = _reload_app(str(tmp_path / "auth_missing.sqlite"))
    client = TestClient(main.app)

    r = client.get("/api/docs")
    assert r.status_code == 401
    assert "Missing API key" in r.text


def test_api_key_invalid_returns_401(tmp_path):
    main = _reload_app(str(tmp_path / "auth_invalid.sqlite"))
    client = TestClient(main.app)

    r = client.get("/api/docs", headers={"X-API-Key": "bad-key"})
    assert r.status_code == 401
    assert "Invalid API key" in r.text


def test_reader_can_read_but_cannot_ingest(tmp_path):
    main = _reload_app(str(tmp_path / "auth_reader.sqlite"))
    client = TestClient(main.app)
    headers = {"X-API-Key": "reader-key"}

    docs_res = client.get("/api/docs", headers=headers)
    assert docs_res.status_code == 200

    ingest_res = client.post(
        "/api/ingest/text",
        headers=headers,
        json={
            "title": "Reader Blocked",
            "source": "unit-test",
            "text": "reader should not ingest",
        },
    )
    assert ingest_res.status_code == 403
    assert "editor role required" in ingest_res.text


def test_admin_can_delete_doc(tmp_path):
    main = _reload_app(str(tmp_path / "auth_admin.sqlite"))
    client = TestClient(main.app)
    admin_headers = {"X-API-Key": "admin-key"}

    ingest = client.post(
        "/api/ingest/text",
        headers=admin_headers,
        json={
            "title": "Delete Me",
            "source": "unit-test",
            "text": "to be deleted",
        },
    )
    assert ingest.status_code == 200, ingest.text
    doc_id = ingest.json()["doc_id"]

    delete_res = client.delete(f"/api/docs/{doc_id}", headers=admin_headers)
    assert delete_res.status_code == 200, delete_res.text
    assert delete_res.json()["deleted"] is True


def test_public_demo_forces_auth_none(tmp_path):
    # Even if AUTH_MODE is set, demo mode must stay anonymous/read-only.
    main = _reload_app(
        str(tmp_path / "auth_demo.sqlite"),
        public_demo_mode=True,
        auth_mode="api_key",
        api_keys_json="",
        allow_uploads=False,
        allow_doc_delete=False,
    )
    client = TestClient(main.app)

    r = client.get("/api/meta")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["public_demo_mode"] is True
    assert data["auth_mode"] == "none"


def test_meta_reports_metadata_edit_enabled_by_role(tmp_path):
    main = _reload_app(
        str(tmp_path / "auth_meta_edit.sqlite"),
        api_keys_json='{"reader-key":"reader","editor-key":"editor","admin-key":"admin"}',
        allow_uploads=True,
    )
    client = TestClient(main.app)

    reader = client.get("/api/meta", headers={"X-API-Key": "reader-key"})
    assert reader.status_code == 200, reader.text
    assert reader.json()["metadata_edit_enabled"] is False

    editor = client.get("/api/meta", headers={"X-API-Key": "editor-key"})
    assert editor.status_code == 200, editor.text
    assert editor.json()["metadata_edit_enabled"] is True

    admin = client.get("/api/meta", headers={"X-API-Key": "admin-key"})
    assert admin.status_code == 200, admin.text
    assert admin.json()["metadata_edit_enabled"] is True


def test_missing_key_logs_structured_auth_denied_event(tmp_path, capsys):
    main = _reload_app(str(tmp_path / "auth_missing_log.sqlite"))
    client = TestClient(main.app)
    _ = capsys.readouterr()

    r = client.get("/api/docs")
    assert r.status_code == 401

    logs = capsys.readouterr().err
    assert '"event": "auth.denied"' in logs
    assert '"path": "/api/docs"' in logs
    assert '"reason": "Missing API key"' in logs


def test_forbidden_role_logs_structured_auth_denied_event(tmp_path, capsys):
    main = _reload_app(str(tmp_path / "auth_forbidden_log.sqlite"))
    client = TestClient(main.app)
    headers = {"X-API-Key": "reader-key"}
    _ = capsys.readouterr()

    ingest_res = client.post(
        "/api/ingest/text",
        headers=headers,
        json={
            "title": "Reader Blocked",
            "source": "unit-test",
            "text": "reader should not ingest",
        },
    )
    assert ingest_res.status_code == 403

    logs = capsys.readouterr().err
    assert '"event": "auth.denied"' in logs
    assert '"path": "/api/ingest/text"' in logs
    assert '"reason": "editor role required"' in logs
