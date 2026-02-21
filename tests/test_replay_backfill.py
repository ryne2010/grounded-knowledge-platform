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


def _reload_modules(sqlite_path: str, *, public_demo_mode: bool = False) -> tuple[object, object, object]:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "1" if public_demo_mode else "0"
    os.environ["AUTH_MODE"] = "api_key"
    os.environ["API_KEYS_JSON"] = '{"reader-key":"reader","editor-key":"editor","admin-key":"admin"}'
    os.environ["ALLOW_CONNECTORS"] = "1"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["ALLOW_DOC_DELETE"] = "1"
    os.environ["ALLOW_CHUNK_VIEW"] = "1"
    os.environ["ALLOW_EVAL"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"

    import app.auth as auth
    import app.cli as cli
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
    importlib.reload(cli)
    importlib.reload(main)
    return main, cli, storage


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


def test_replay_run_is_idempotent_when_not_forced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = str(tmp_path / "replay_run_idempotent.sqlite")
    main, cli, storage = _reload_modules(db)
    _patch_gcs_sync(monkeypatch, files={"knowledge/a.txt": (16, "same-content")})
    client = TestClient(main.app)

    sync_res = client.post(
        "/api/connectors/gcs/sync",
        headers={"X-API-Key": "admin-key"},
        json={"bucket": "demo-bucket", "prefix": "knowledge/", "max_objects": 10, "dry_run": False},
    )
    assert sync_res.status_code == 200, sync_res.text
    sync_body = sync_res.json()
    source_run_id = str(sync_body["run_id"])
    doc_id = str(sync_body["results"][0]["doc_id"])

    with storage.connect(db) as conn:
        storage.init_db(conn)
        before_doc = storage.get_doc(conn, doc_id)
        assert before_doc is not None
        before_events = storage.list_ingest_events(conn, doc_id, limit=20)
        before_chunks = storage.list_all_chunks_for_doc(conn, doc_id, limit=5000)

    cli.cmd_replay_run(run_id=source_run_id, force=False)

    with storage.connect(db) as conn:
        storage.init_db(conn)
        after_doc = storage.get_doc(conn, doc_id)
        assert after_doc is not None
        after_events = storage.list_ingest_events(conn, doc_id, limit=20)
        after_chunks = storage.list_all_chunks_for_doc(conn, doc_id, limit=5000)
        replay_runs = [
            r
            for r in storage.list_ingestion_runs(conn, limit=10)
            if r.trigger_payload.get("mode") == "replay-run" and r.trigger_payload.get("source_run_id") == source_run_id
        ]

    assert after_doc.doc_version == before_doc.doc_version
    assert len(after_events) == len(before_events)
    assert len(after_chunks) == len(before_chunks)
    assert len({c.chunk_id for c in after_chunks}) == len(after_chunks)
    assert replay_runs
    latest_replay_run = replay_runs[0]
    assert latest_replay_run.status == "succeeded"
    assert latest_replay_run.docs_changed == 0
    assert latest_replay_run.docs_unchanged >= 1
    assert latest_replay_run.event_count == 0


def test_replay_doc_force_reprocesses_even_when_content_is_unchanged(tmp_path: Path) -> None:
    db = str(tmp_path / "replay_doc_force.sqlite")
    main, cli, storage = _reload_modules(db)
    client = TestClient(main.app)

    ingest_res = client.post(
        "/api/ingest/text",
        headers={"X-API-Key": "editor-key"},
        json={"title": "Replay Target", "source": "cli:test", "text": "hello replay"},
    )
    assert ingest_res.status_code == 200, ingest_res.text
    doc_id = str(ingest_res.json()["doc_id"])

    with storage.connect(db) as conn:
        storage.init_db(conn)
        before = storage.get_doc(conn, doc_id)
        assert before is not None
        before_version = int(before.doc_version)

    cli.cmd_replay_doc(doc_id=doc_id, force=False)
    with storage.connect(db) as conn:
        storage.init_db(conn)
        after_skip = storage.get_doc(conn, doc_id)
        assert after_skip is not None
        assert int(after_skip.doc_version) == before_version

    cli.cmd_replay_doc(doc_id=doc_id, force=True)
    with storage.connect(db) as conn:
        storage.init_db(conn)
        after_force = storage.get_doc(conn, doc_id)
        assert after_force is not None
        events = storage.list_ingest_events(conn, doc_id, limit=20)
        chunks = storage.list_all_chunks_for_doc(conn, doc_id, limit=5000)

    assert int(after_force.doc_version) == before_version + 1
    assert events[0].changed_bool is False
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_replay_commands_are_blocked_in_public_demo_mode(tmp_path: Path) -> None:
    db = str(tmp_path / "replay_public_demo.sqlite")
    main, cli, _storage = _reload_modules(db, public_demo_mode=True)
    client = TestClient(main.app)

    with pytest.raises(SystemExit):
        cli.cmd_replay_doc(doc_id="some-doc", force=False)
    with pytest.raises(SystemExit):
        cli.cmd_replay_run(run_id="some-run", force=False)

    # No replay API is exposed; public demo remains read-only for replay operations.
    resp = client.post("/api/replay/run")
    assert resp.status_code in {404, 405}
