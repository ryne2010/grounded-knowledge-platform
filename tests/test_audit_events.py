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


def _reload_app(sqlite_path: str) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "api_key"
    os.environ["API_KEYS_JSON"] = '{"reader-key":"reader","editor-key":"editor","admin-key":"admin"}'
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


def test_audit_events_admin_only_and_action_time_filters(tmp_path):
    main = _reload_app(str(tmp_path / "audit_filters.sqlite"))
    client = TestClient(main.app)

    ingest = client.post(
        "/api/ingest/text",
        headers={"X-API-Key": "admin-key"},
        json={
            "title": "Metadata Event Doc",
            "source": "unit-test",
            "text": "This text should never appear in audit metadata.",
        },
    )
    assert ingest.status_code == 200, ingest.text
    doc_id = str(ingest.json()["doc_id"])

    update = client.patch(
        f"/api/docs/{doc_id}",
        headers={"X-API-Key": "editor-key", "X-Request-Id": "rid-metadata-1"},
        json={"classification": "internal", "retention": "90d", "tags": ["Policy", "Security"]},
    )
    assert update.status_code == 200, update.text

    forbidden = client.get("/api/audit-events", headers={"X-API-Key": "reader-key"})
    assert forbidden.status_code == 403

    listed = client.get(
        "/api/audit-events",
        headers={"X-API-Key": "admin-key"},
        params={"action": "doc.metadata.updated", "limit": 10},
    )
    assert listed.status_code == 200, listed.text
    events = listed.json()["events"]
    assert len(events) >= 1
    event = events[0]

    assert event["action"] == "doc.metadata.updated"
    assert event["target_type"] == "doc"
    assert event["target_id"] == doc_id
    assert str(event["principal"]).startswith("api_key:")
    assert event["role"] == "editor"
    assert event["request_id"] == "rid-metadata-1"
    assert "text" not in {k.lower() for k in event["metadata"].keys()}

    ts = int(event["occurred_at"])
    none_res = client.get(
        "/api/audit-events",
        headers={"X-API-Key": "admin-key"},
        params={"action": "doc.metadata.updated", "since": ts + 1, "limit": 10},
    )
    assert none_res.status_code == 200, none_res.text
    assert none_res.json()["events"] == []


def test_delete_eval_and_connector_actions_are_audited(tmp_path, monkeypatch: pytest.MonkeyPatch):
    main = _reload_app(str(tmp_path / "audit_write_points.sqlite"))
    client = TestClient(main.app)

    ingest = client.post(
        "/api/ingest/text",
        headers={"X-API-Key": "admin-key"},
        json={
            "title": "Delete Event Doc",
            "source": "unit-test",
            "text": "Do not copy this content into audit logs.",
        },
    )
    assert ingest.status_code == 200, ingest.text
    doc_id = str(ingest.json()["doc_id"])

    class _EvalResult:
        n = 3
        hit_at_k = 0.666
        mrr = 0.555

        def to_dict(self, *, include_details: bool = False):  # noqa: ARG002
            return {"examples": self.n, "hit_at_k": self.hit_at_k, "mrr": self.mrr}

    monkeypatch.setattr(main, "run_eval", lambda _path, k=5, include_details=False: _EvalResult())

    import app.connectors.gcs as gcs

    def _fake_sync_prefix(**kwargs):
        return {
            "run_id": kwargs["run_id"],
            "scanned": 1,
            "skipped_unsupported": 0,
            "ingested": 1,
            "changed": 1,
            "errors": [],
            "results": [{"size": 42}],
        }

    monkeypatch.setattr(gcs, "sync_prefix", _fake_sync_prefix)

    delete_res = client.delete(
        f"/api/docs/{doc_id}",
        headers={"X-API-Key": "admin-key", "X-Request-Id": "rid-delete-1"},
    )
    assert delete_res.status_code == 200, delete_res.text

    eval_res = client.post(
        "/api/eval/run",
        headers={"X-API-Key": "admin-key", "X-Request-Id": "rid-eval-1"},
        json={"golden_path": "data/eval/golden.jsonl", "k": 4, "include_details": False},
    )
    assert eval_res.status_code == 200, eval_res.text

    sync_res = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "admin-key", "X-Request-Id": "rid-sync-1"},
        json={"bucket": "demo-bucket", "prefix": "docs/", "max_objects": 10, "dry_run": False},
    )
    assert sync_res.status_code == 200, sync_res.text
    run_id = str(sync_res.json()["run_id"])

    listed = client.get("/api/audit-events?limit=100", headers={"X-API-Key": "admin-key"})
    assert listed.status_code == 200, listed.text
    events = listed.json()["events"]
    by_action = {e["action"]: e for e in events}

    assert "doc.deleted" in by_action
    assert "eval.run.created" in by_action
    assert "connector.gcs.sync.triggered" in by_action

    delete_event = by_action["doc.deleted"]
    eval_event = by_action["eval.run.created"]
    sync_event = by_action["connector.gcs.sync.triggered"]

    assert delete_event["target_id"] == doc_id
    assert delete_event["request_id"] == "rid-delete-1"
    assert eval_event["request_id"] == "rid-eval-1"
    assert sync_event["request_id"] == "rid-sync-1"
    assert sync_event["target_id"] == run_id

    sensitive_fragments = {"secret", "token", "password", "api_key", "content", "text", "quote"}
    for event in (delete_event, eval_event, sync_event):
        for key in event["metadata"].keys():
            lower = key.lower()
            assert not any(fragment in lower for fragment in sensitive_fragments)

    flattened = str([delete_event["metadata"], eval_event["metadata"], sync_event["metadata"]]).lower()
    assert "do not copy this content" not in flattened
    assert "x-api-key" not in flattened
