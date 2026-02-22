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


def _reload_app(sqlite_path: str, *, public_demo_mode: bool, allow_connectors: bool) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "1" if public_demo_mode else "0"
    os.environ["AUTH_MODE"] = "api_key"
    os.environ["API_KEYS_JSON"] = '{"reader-key":"reader","admin-key":"admin"}'
    os.environ["ALLOW_CONNECTORS"] = "1" if allow_connectors else "0"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["ALLOW_DOC_DELETE"] = "1"
    os.environ["ALLOW_CHUNK_VIEW"] = "1"
    os.environ["ALLOW_EVAL"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"

    import app.auth as auth
    import app.config as config
    import app.connectors.gcs as gcs
    import app.ingestion as ingestion
    import app.main as main
    import app.retrieval as retrieval
    import app.storage as storage

    importlib.reload(config)
    importlib.reload(auth)
    importlib.reload(storage)
    importlib.reload(ingestion)
    importlib.reload(retrieval)
    importlib.reload(gcs)
    importlib.reload(main)
    return main


def test_gcs_sync_is_disabled_in_public_demo_even_if_allow_connectors_is_set(tmp_path):
    main = _reload_app(str(tmp_path / "connectors_demo.sqlite"), public_demo_mode=True, allow_connectors=True)
    client = TestClient(main.app)

    meta = client.get("/api/meta")
    assert meta.status_code == 200, meta.text
    assert meta.json()["public_demo_mode"] is True
    assert meta.json()["connectors_enabled"] is False

    sync_res = client.post("/api/connectors/gcs/sync", json={"bucket": "demo-bucket"})
    assert sync_res.status_code == 403
    assert "Connectors are disabled" in sync_res.text


def test_gcs_sync_requires_admin_role(tmp_path):
    main = _reload_app(str(tmp_path / "connectors_admin.sqlite"), public_demo_mode=False, allow_connectors=True)
    client = TestClient(main.app)

    sync_res = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "reader-key"},
        json={"bucket": "demo-bucket"},
    )
    assert sync_res.status_code == 403
    assert "admin role required" in sync_res.text


def test_gcs_sync_enforces_max_objects_bounds_and_accepts_limits(tmp_path, monkeypatch: pytest.MonkeyPatch):
    main = _reload_app(str(tmp_path / "connectors_bounds.sqlite"), public_demo_mode=False, allow_connectors=True)
    client = TestClient(main.app)

    low = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "admin-key"},
        json={"bucket": "demo-bucket", "max_objects": 0},
    )
    assert low.status_code == 422

    high = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "admin-key"},
        json={"bucket": "demo-bucket", "max_objects": 5001},
    )
    assert high.status_code == 422

    import app.connectors.gcs as gcs

    seen_max_objects: list[int] = []

    def _fake_sync_prefix(**kwargs):
        seen_max_objects.append(int(kwargs["max_objects"]))
        return {
            "run_id": str(kwargs["run_id"]),
            "started_at": 1,
            "finished_at": 2,
            "bucket": str(kwargs["bucket"]),
            "prefix": str(kwargs["prefix"]),
            "dry_run": bool(kwargs["dry_run"]),
            "max_objects": int(kwargs["max_objects"]),
            "scanned": 0,
            "skipped_unsupported": 0,
            "ingested": 0,
            "changed": 0,
            "errors": [],
            "results": [],
        }

    monkeypatch.setattr(gcs, "sync_prefix", _fake_sync_prefix)

    ok_min = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "admin-key"},
        json={"bucket": "demo-bucket", "max_objects": 1},
    )
    assert ok_min.status_code == 200, ok_min.text
    assert ok_min.json()["max_objects"] == 1

    ok_max = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "admin-key"},
        json={"bucket": "demo-bucket", "max_objects": 5000},
    )
    assert ok_max.status_code == 200, ok_max.text
    assert ok_max.json()["max_objects"] == 5000

    assert seen_max_objects == [1, 5000]
