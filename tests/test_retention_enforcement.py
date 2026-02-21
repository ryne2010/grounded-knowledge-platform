from __future__ import annotations

import importlib
import os
import time

import pytest
from fastapi.testclient import TestClient


def _reload_app(sqlite_path: str) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "none"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"
    os.environ["RATE_LIMIT_ENABLED"] = "0"
    os.environ.pop("DATABASE_URL", None)

    import app.config as config
    import app.ingestion as ingestion
    import app.main as main
    import app.retrieval as retrieval
    import app.storage as storage

    importlib.reload(config)
    importlib.reload(storage)
    importlib.reload(ingestion)
    importlib.reload(retrieval)
    importlib.reload(main)
    return main


def _reload_cli(sqlite_path: str, *, public_demo_mode: bool) -> tuple[object, object]:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "1" if public_demo_mode else "0"
    os.environ.pop("DATABASE_URL", None)

    import app.cli as cli
    import app.config as config
    import app.storage as storage

    importlib.reload(config)
    importlib.reload(storage)
    importlib.reload(cli)
    return cli, storage


def test_expired_retention_doc_is_not_retrievable(tmp_path) -> None:
    main = _reload_app(str(tmp_path / "retention_enforcement.sqlite"))
    client = TestClient(main.app)

    ingest = client.post(
        "/api/ingest/text",
        json={
            "title": "Expiring Doc",
            "source": "unit-test",
            "retention": "30d",
            "text": "Cloud Run supports managed containers and scales to zero.",
        },
    )
    assert ingest.status_code == 200, ingest.text
    doc_id = str(ingest.json()["doc_id"])

    now = int(time.time())
    old_ts = now - (31 * 24 * 60 * 60)
    with main.connect(main.settings.sqlite_path) as conn:
        main.init_db(conn)
        conn.execute("UPDATE docs SET updated_at=? WHERE doc_id=?", (old_ts, doc_id))
        conn.commit()

    query = client.post("/api/query", json={"question": "What supports managed containers?", "top_k": 3})
    assert query.status_code == 200, query.text
    body = query.json()
    assert body["refused"] is True
    assert body["refusal_reason"] == "insufficient_evidence"
    assert body["citations"] == []


def test_retention_sweep_cli_summary_and_apply(tmp_path, capsys) -> None:
    db_path = tmp_path / "retention_sweep.sqlite"
    cli, storage = _reload_cli(str(db_path), public_demo_mode=False)

    now = int(time.time())
    with storage.connect(str(db_path)) as conn:
        storage.init_db(conn)
        storage.upsert_doc(
            conn,
            doc_id="d1",
            title="Expired Doc",
            source="unit-test",
            classification="public",
            retention="30d",
            tags_json="[]",
            content_sha256="0" * 64,
            content_bytes=1,
            num_chunks=0,
            doc_version=1,
        )
        storage.upsert_doc(
            conn,
            doc_id="d2",
            title="Active Doc",
            source="unit-test",
            classification="public",
            retention="indefinite",
            tags_json="[]",
            content_sha256="1" * 64,
            content_bytes=1,
            num_chunks=0,
            doc_version=1,
        )
        conn.execute("UPDATE docs SET updated_at=? WHERE doc_id=?", (now - (31 * 24 * 60 * 60), "d1"))
        conn.execute("UPDATE docs SET updated_at=? WHERE doc_id=?", (now - (31 * 24 * 60 * 60), "d2"))
        conn.commit()

    cli.cmd_retention_sweep(apply=False, now=now)
    out = capsys.readouterr().out
    assert "Retention sweep mode=dry-run" in out
    assert "doc_id=d1" in out
    assert "Would delete 1 doc(s)." in out

    cli.cmd_retention_sweep(apply=True, now=now)
    out = capsys.readouterr().out
    assert "Retention sweep mode=apply" in out
    assert "Deleted 1 doc(s)." in out

    with storage.connect(str(db_path)) as conn:
        storage.init_db(conn)
        docs = storage.list_docs(conn)
    assert {d.doc_id for d in docs} == {"d2"}


def test_retention_sweep_disabled_in_public_demo(tmp_path) -> None:
    cli, _ = _reload_cli(str(tmp_path / "retention_sweep_demo.sqlite"), public_demo_mode=True)
    with pytest.raises(SystemExit, match="PUBLIC_DEMO_MODE"):
        cli.cmd_retention_sweep(apply=False, now=int(time.time()))
