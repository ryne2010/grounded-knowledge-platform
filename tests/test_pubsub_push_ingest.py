from __future__ import annotations

import base64
import importlib
import json
import os
from pathlib import Path
from typing import Any

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


def _patch_gcs_download(monkeypatch: pytest.MonkeyPatch, *, files: dict[str, str]) -> None:
    import app.connectors.gcs as gcs

    monkeypatch.setattr(gcs, "_get_access_token", lambda _client: "token")

    def _fake_download(*, bucket: str, name: str, dest_path: Path, client, token: str) -> None:
        _ = bucket
        _ = client
        _ = token
        content = files[name]
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(content, encoding="utf-8")

    monkeypatch.setattr(gcs, "download_object_to_file", _fake_download)


def _attrs_payload(*, message_id: str, bucket: str, object_name: str, event_type: str = "OBJECT_FINALIZE") -> dict[str, Any]:
    return {
        "message": {
            "messageId": message_id,
            "attributes": {
                "eventType": event_type,
                "bucketId": bucket,
                "objectId": object_name,
                "objectGeneration": "1",
                "objectSize": "12",
            },
        },
        "subscription": "projects/demo/subscriptions/gkp-ingest-events-push",
    }


def _data_payload(*, message_id: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "message": {
            "messageId": message_id,
            "data": base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8"),
        },
        "subscription": "projects/demo/subscriptions/gkp-ingest-events-push",
    }


def test_pubsub_notify_ingests_object_and_is_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    main = _reload_app(str(tmp_path / "pubsub_notify.sqlite"), public_demo_mode=False, allow_connectors=True)
    _patch_gcs_download(monkeypatch, files={"knowledge/a.txt": "alpha"})
    client = TestClient(main.app)

    payload1 = _attrs_payload(message_id="msg-1", bucket="demo-bucket", object_name="knowledge/a.txt")
    res1 = client.post("/api/connectors/gcs/notify", headers={"X-API-Key": "admin-key"}, json=payload1)
    assert res1.status_code == 202, res1.text
    body1 = res1.json()
    run1 = str(body1["run_id"])
    assert body1["result"] == "changed"

    payload2 = _attrs_payload(message_id="msg-2", bucket="demo-bucket", object_name="knowledge/a.txt")
    res2 = client.post("/api/connectors/gcs/notify", headers={"X-API-Key": "admin-key"}, json=payload2)
    assert res2.status_code == 202, res2.text
    body2 = res2.json()
    run2 = str(body2["run_id"])
    assert body2["result"] == "unchanged"

    docs = client.get("/api/docs", headers={"X-API-Key": "reader-key"})
    assert docs.status_code == 200, docs.text
    assert len(docs.json()["docs"]) == 1

    runs_res = client.get("/api/ingestion-runs?limit=10", headers={"X-API-Key": "reader-key"})
    assert runs_res.status_code == 200, runs_res.text
    runs = runs_res.json()["runs"]
    run1_summary = next(r for r in runs if r["run_id"] == run1)
    run2_summary = next(r for r in runs if r["run_id"] == run2)
    assert run1_summary["docs_changed"] == 1
    assert run1_summary["docs_unchanged"] == 0
    assert run2_summary["docs_changed"] == 0
    assert run2_summary["docs_unchanged"] == 1


def test_pubsub_notify_parses_base64_message_data_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    main = _reload_app(str(tmp_path / "pubsub_notify_data.sqlite"), public_demo_mode=False, allow_connectors=True)
    _patch_gcs_download(monkeypatch, files={"knowledge/b.txt": "bravo"})
    client = TestClient(main.app)

    payload = _data_payload(
        message_id="msg-data",
        data={
            "eventType": "OBJECT_FINALIZE",
            "bucket": "demo-bucket",
            "name": "knowledge/b.txt",
            "generation": "7",
            "size": "5",
        },
    )
    res = client.post("/api/connectors/gcs/notify", headers={"X-API-Key": "admin-key"}, json=payload)
    assert res.status_code == 202, res.text
    assert res.json()["gcs_uri"] == "gs://demo-bucket/knowledge/b.txt"


def test_pubsub_notify_is_not_reachable_when_demo_or_connectors_disabled(tmp_path: Path) -> None:
    demo_main = _reload_app(str(tmp_path / "pubsub_demo.sqlite"), public_demo_mode=True, allow_connectors=True)
    demo_client = TestClient(demo_main.app)
    demo_res = demo_client.post(
        "/api/connectors/gcs/notify",
        json=_attrs_payload(message_id="m", bucket="demo-bucket", object_name="knowledge/a.txt"),
    )
    assert demo_res.status_code == 404

    disabled_main = _reload_app(str(tmp_path / "pubsub_disabled.sqlite"), public_demo_mode=False, allow_connectors=False)
    disabled_client = TestClient(disabled_main.app)
    disabled_res = disabled_client.post(
        "/api/connectors/gcs/notify",
        headers={"X-API-Key": "admin-key"},
        json=_attrs_payload(message_id="m2", bucket="demo-bucket", object_name="knowledge/a.txt"),
    )
    assert disabled_res.status_code == 404


def test_pubsub_notify_requires_admin_auth_when_enabled(tmp_path: Path) -> None:
    main = _reload_app(str(tmp_path / "pubsub_auth.sqlite"), public_demo_mode=False, allow_connectors=True)
    client = TestClient(main.app)

    res = client.post(
        "/api/connectors/gcs/notify",
        headers={"X-API-Key": "reader-key"},
        json=_attrs_payload(message_id="m-auth", bucket="demo-bucket", object_name="knowledge/a.txt"),
    )
    assert res.status_code == 403
    assert "admin role required" in res.text


def test_pubsub_notify_rejects_invalid_payload(tmp_path: Path) -> None:
    main = _reload_app(str(tmp_path / "pubsub_invalid.sqlite"), public_demo_mode=False, allow_connectors=True)
    client = TestClient(main.app)

    res = client.post("/api/connectors/gcs/notify", headers={"X-API-Key": "admin-key"}, json={"foo": "bar"})
    assert res.status_code == 400
