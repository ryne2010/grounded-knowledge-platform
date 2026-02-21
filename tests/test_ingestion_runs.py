from __future__ import annotations

import importlib
import os
from pathlib import Path

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


def _reload_app(sqlite_path: str) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "api_key"
    os.environ["API_KEYS_JSON"] = '{"reader-key":"reader","admin-key":"admin"}'
    os.environ["ALLOW_CONNECTORS"] = "1"
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


def _patch_gcs_sync(monkeypatch: pytest.MonkeyPatch, *, files: dict[str, tuple[int, str]]) -> None:
    import app.connectors.gcs as gcs

    monkeypatch.setattr(gcs, "_get_access_token", lambda _client: "token")
    monkeypatch.setattr(
        gcs,
        "list_objects",
        lambda **_kwargs: [
            gcs.GCSObject(name=name, size=size, updated="2026-02-21T00:00:00Z", generation="1")
            for name, (size, _content) in files.items()
        ],
    )

    def _fake_download(*, bucket: str, name: str, dest_path: Path, client, token: str) -> None:
        _ = bucket
        _ = client
        _ = token
        _size, content = files[name]
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(content, encoding="utf-8")

    monkeypatch.setattr(gcs, "download_object_to_file", _fake_download)


def test_gcs_sync_creates_ingestion_run_with_summary_and_detail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    main = _reload_app(str(tmp_path / "ingestion_runs_success.sqlite"))
    _patch_gcs_sync(
        monkeypatch,
        files={
            "knowledge/a.txt": (32, "alpha"),
            "knowledge/skip.png": (99, "not-used"),
        },
    )
    client = TestClient(main.app)

    sync_res = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "admin-key"},
        json={"bucket": "demo-bucket", "prefix": "knowledge/", "max_objects": 10, "dry_run": False},
    )
    assert sync_res.status_code == 200, sync_res.text
    sync_body = sync_res.json()
    run_id = str(sync_body["run_id"])

    assert sync_body["scanned"] == 2
    assert sync_body["skipped_unsupported"] == 1
    assert sync_body["ingested"] == 1
    assert sync_body["changed"] == 1

    list_res = client.get("/api/ingestion-runs", headers={"X-API-Key": "reader-key"})
    assert list_res.status_code == 200, list_res.text
    listed = next(r for r in list_res.json()["runs"] if r["run_id"] == run_id)
    assert listed["status"] == "succeeded"
    assert listed["objects_scanned"] == 2
    assert listed["docs_changed"] == 1
    assert listed["docs_unchanged"] == 0
    assert listed["event_count"] == 1
    assert str(listed["principal"]).startswith("api_key:")

    detail_res = client.get(f"/api/ingestion-runs/{run_id}", headers={"X-API-Key": "reader-key"})
    assert detail_res.status_code == 200, detail_res.text
    detail = detail_res.json()
    assert detail["run"]["run_id"] == run_id
    assert len(detail["events"]) == 1
    assert detail["events"][0]["run_id"] == run_id


def test_failed_sync_records_failed_run_with_actionable_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    main = _reload_app(str(tmp_path / "ingestion_runs_failed.sqlite"))
    client = TestClient(main.app)

    import app.connectors.gcs as gcs

    monkeypatch.setattr(gcs, "_get_access_token", lambda _client: "token")

    def _raise_list(**_kwargs):
        raise RuntimeError("GCS list failed: 500 upstream timeout")

    monkeypatch.setattr(gcs, "list_objects", _raise_list)

    sync_res = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "admin-key"},
        json={"bucket": "demo-bucket", "prefix": "knowledge/", "max_objects": 10, "dry_run": False},
    )
    assert sync_res.status_code == 400
    assert "upstream timeout" in sync_res.text

    runs_res = client.get("/api/ingestion-runs?limit=1", headers={"X-API-Key": "reader-key"})
    assert runs_res.status_code == 200, runs_res.text
    run = runs_res.json()["runs"][0]
    assert run["status"] == "failed"
    assert any("upstream timeout" in err for err in run["errors"])


def test_rerun_same_sync_is_idempotent_for_docs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    main = _reload_app(str(tmp_path / "ingestion_runs_idempotent.sqlite"))
    _patch_gcs_sync(
        monkeypatch,
        files={
            "knowledge/a.txt": (18, "same-content"),
        },
    )
    client = TestClient(main.app)

    run1 = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "admin-key"},
        json={"bucket": "demo-bucket", "prefix": "knowledge/", "max_objects": 10, "dry_run": False},
    )
    assert run1.status_code == 200, run1.text

    run2 = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "admin-key"},
        json={"bucket": "demo-bucket", "prefix": "knowledge/", "max_objects": 10, "dry_run": False},
    )
    assert run2.status_code == 200, run2.text
    run2_id = str(run2.json()["run_id"])

    docs_res = client.get("/api/docs", headers={"X-API-Key": "reader-key"})
    assert docs_res.status_code == 200, docs_res.text
    assert len(docs_res.json()["docs"]) == 1

    detail_res = client.get(f"/api/ingestion-runs/{run2_id}", headers={"X-API-Key": "reader-key"})
    assert detail_res.status_code == 200, detail_res.text
    run_summary = detail_res.json()["run"]
    assert run_summary["status"] == "succeeded"
    assert run_summary["docs_changed"] == 0
    assert run_summary["docs_unchanged"] >= 1
