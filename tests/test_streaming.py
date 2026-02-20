from __future__ import annotations

import importlib
import json
import os

from fastapi.testclient import TestClient


def _reload_app(sqlite_path: str, *, citations_required: bool = True) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "none"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"
    os.environ["CITATIONS_REQUIRED"] = "1" if citations_required else "0"

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
        raw_data = "\n".join(data_lines)
        data: object
        try:
            data = json.loads(raw_data) if raw_data else {}
        except Exception:
            data = raw_data
        events.append((event_name, data))
    return events


def test_query_stream_emits_expected_event_frames(tmp_path):
    main = _reload_app(str(tmp_path / "stream_ok.sqlite"), citations_required=True)
    client = TestClient(main.app)

    ingest = client.post(
        "/api/ingest/text",
        json={
            "title": "Stream Doc",
            "source": "unit-test",
            "text": "Cloud Run is a managed container runtime. It scales to zero.",
        },
    )
    assert ingest.status_code == 200, ingest.text

    with client.stream(
        "POST",
        "/api/query/stream",
        json={"question": "What is Cloud Run?", "top_k": 3},
    ) as r:
        assert r.status_code == 200
        body = r.read().decode("utf-8")

    events = _parse_sse(body)
    names = [name for name, _ in events]

    assert "retrieval" in names
    assert "token" in names
    assert "citations" in names
    assert names[-1] == "done"

    done = events[-1][1]
    assert isinstance(done, dict)
    assert done.get("refused") is False

    citations_event = [payload for name, payload in events if name == "citations"][-1]
    assert isinstance(citations_event, list)
    assert len(citations_event) >= 1


def test_query_stream_preserves_citations_required_refusal(tmp_path):
    main = _reload_app(str(tmp_path / "stream_refusal.sqlite"), citations_required=True)
    client = TestClient(main.app)

    with client.stream(
        "POST",
        "/api/query/stream",
        json={"question": "What is the capital of France?", "top_k": 3},
    ) as r:
        assert r.status_code == 200
        body = r.read().decode("utf-8")

    events = _parse_sse(body)
    done = events[-1][1]
    assert isinstance(done, dict)
    assert done.get("refused") is True
    assert done.get("refusal_reason") == "insufficient_evidence"

    citations_event = [payload for name, payload in events if name == "citations"][-1]
    assert citations_event == []
