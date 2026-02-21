from __future__ import annotations

import importlib
import json
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
    "CITATIONS_REQUIRED",
    "RATE_LIMIT_ENABLED",
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


def _reload_app(sqlite_path: str, *, public_demo_mode: bool, citations_required: bool = True) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "1" if public_demo_mode else "0"
    os.environ["AUTH_MODE"] = "api_key"
    os.environ["API_KEYS_JSON"] = '{"reader-key":"reader","admin-key":"admin"}'
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["ALLOW_DOC_DELETE"] = "1"
    os.environ["ALLOW_CHUNK_VIEW"] = "1"
    os.environ["ALLOW_EVAL"] = "1"
    os.environ["CITATIONS_REQUIRED"] = "1" if citations_required else "0"
    os.environ["RATE_LIMIT_ENABLED"] = "0"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"

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


def _parse_sse(body: str) -> list[tuple[str, object]]:
    events: list[tuple[str, object]] = []
    for block in body.strip().split("\n\n"):
        if not block.strip():
            continue
        event_name = "message"
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_lines.append(line.split(":", 1)[1].strip())
        raw = "\n".join(data_lines)
        data: object
        try:
            data = json.loads(raw) if raw else {}
        except Exception:
            data = raw
        events.append((event_name, data))
    return events


def test_public_demo_mode_forces_safe_invariants(tmp_path):
    main = _reload_app(str(tmp_path / "demo_mode.sqlite"), public_demo_mode=True, citations_required=False)
    client = TestClient(main.app)

    meta_res = client.get("/api/meta")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert meta["public_demo_mode"] is True
    assert meta["auth_mode"] == "none"
    assert meta["uploads_enabled"] is False
    assert meta["doc_delete_enabled"] is False
    assert meta["chunk_view_enabled"] is False
    assert meta["eval_enabled"] is False
    assert meta["citations_required"] is True
    assert meta["rate_limit_enabled"] is True

    ingest_res = client.post("/api/ingest/text", json={"title": "t", "source": "s", "text": "demo"})
    assert ingest_res.status_code == 403

    delete_res = client.delete("/api/docs/does-not-exist")
    assert delete_res.status_code == 403

    chunks_res = client.get("/api/docs/does-not-exist/chunks")
    assert chunks_res.status_code == 403

    eval_res = client.post("/api/eval/run", json={"golden_path": "data/eval/golden.jsonl", "k": 5})
    assert eval_res.status_code == 403


def test_citations_required_forces_refusal_in_query_and_stream(tmp_path):
    main = _reload_app(str(tmp_path / "citations_required.sqlite"), public_demo_mode=False, citations_required=True)
    client = TestClient(main.app)

    class _UncitedAnswerer:
        name = "uncited"

        def answer(self, question: str, context):
            from app.llm.base import Answer

            return Answer(text=f"Uncited answer for: {question}", citations=[], refused=False, provider="uncited")

    main.get_answerer = lambda: _UncitedAnswerer()

    ingest = client.post(
        "/api/ingest/text",
        json={
            "title": "Citations Doc",
            "source": "unit-test",
            "text": "Cloud Run can scale to zero based on traffic.",
        },
        headers={"X-API-Key": "admin-key"},
    )
    assert ingest.status_code == 200, ingest.text

    query = client.post(
        "/api/query",
        json={"question": "What can Cloud Run do?"},
        headers={"X-API-Key": "reader-key"},
    )
    assert query.status_code == 200, query.text
    query_body = query.json()
    assert query_body["refused"] is True
    assert query_body["refusal_reason"] == "insufficient_evidence"
    assert query_body["citations"] == []

    with client.stream(
        "POST",
        "/api/query/stream",
        json={"question": "What can Cloud Run do?"},
        headers={"X-API-Key": "reader-key"},
    ) as stream_res:
        assert stream_res.status_code == 200
        stream_body = stream_res.read().decode("utf-8")

    events = _parse_sse(stream_body)
    done = events[-1][1]
    assert isinstance(done, dict)
    assert done.get("refused") is True
    assert done.get("refusal_reason") == "insufficient_evidence"

    citations_payload = [payload for event_name, payload in events if event_name == "citations"][-1]
    assert citations_payload == []
