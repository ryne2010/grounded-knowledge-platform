from __future__ import annotations

import importlib
import json
import os
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.llm.base import Answer, Citation
from app.retrieval import RetrievedChunk


def _reload_app(sqlite_path: str, *, public_demo_mode: bool) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "1" if public_demo_mode else "0"
    os.environ["AUTH_MODE"] = "none"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["ALLOW_CHUNK_VIEW"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"
    os.environ["RATE_LIMIT_ENABLED"] = "0"

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


def _mock_retrieved() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id="chunk-abc",
            doc_id="doc-abc",
            idx=0,
            text="Cloud Run scales to zero and supports managed containers.",
            score=0.91,
            lexical_score=0.73,
            vector_score=0.88,
        )
    ]


def _mock_answerer():
    class _Answerer:
        name = "mock-answerer"

        def answer(self, question: str, context):
            chunk_id, doc_id, idx, text = context[0]
            return Answer(
                text=f"Answer: {question}",
                citations=[Citation(chunk_id=chunk_id, doc_id=doc_id, idx=idx, quote=text[:80])],
                refused=False,
                provider="mock-answerer",
            )

    return _Answerer()


def test_query_explain_hides_private_fields_in_public_demo(tmp_path):
    main = _reload_app(str(tmp_path / "explain_public.sqlite"), public_demo_mode=True)
    main.retrieve = lambda _question, top_k=5: _mock_retrieved()[:top_k]
    main.get_answerer = lambda: _mock_answerer()
    client = TestClient(main.app)

    res = client.post("/api/query", json={"question": "How does Cloud Run scale?", "top_k": 3, "debug": True})
    assert res.status_code == 200, res.text
    body = res.json()
    explain = body["explain"]

    assert explain["how_retrieval_works"]["public_demo_mode"] is True
    assert explain["how_retrieval_works"]["debug_details_included"] is False
    assert explain["refusal"]["refused"] is False
    assert len(explain["evidence_used"]) == 1

    ev = explain["evidence_used"][0]
    assert "chunk_id" not in ev
    assert "score" not in ev
    assert "lexical_score" not in ev
    assert "vector_score" not in ev


def test_query_explain_includes_private_fields_when_debug_enabled(tmp_path):
    main = _reload_app(str(tmp_path / "explain_private.sqlite"), public_demo_mode=False)
    main.retrieve = lambda _question, top_k=5: _mock_retrieved()[:top_k]
    main.get_answerer = lambda: _mock_answerer()
    client = TestClient(main.app)

    res = client.post("/api/query", json={"question": "How does Cloud Run scale?", "top_k": 3, "debug": True})
    assert res.status_code == 200, res.text
    body = res.json()
    explain = body["explain"]

    assert explain["how_retrieval_works"]["public_demo_mode"] is False
    assert explain["how_retrieval_works"]["debug_details_included"] is True
    assert len(explain["evidence_used"]) == 1

    ev = explain["evidence_used"][0]
    assert ev["chunk_id"] == "chunk-abc"
    assert ev["score"] > 0
    assert ev["lexical_score"] > 0
    assert ev["vector_score"] > 0
    assert isinstance(body.get("retrieval"), list)
    assert len(body["retrieval"]) == 1


def test_query_stream_done_includes_explain_and_refusal_category(tmp_path):
    main = _reload_app(str(tmp_path / "explain_stream.sqlite"), public_demo_mode=False)
    main.detect_prompt_injection = lambda _q: SimpleNamespace(is_injection=False, reasons=[])
    main.retrieve = lambda _question, top_k=5: []  # force insufficient evidence refusal
    client = TestClient(main.app)

    with client.stream("POST", "/api/query/stream", json={"question": "How does Cloud Run scale?", "top_k": 3}) as r:
        assert r.status_code == 200
        body = r.read().decode("utf-8")

    events = _parse_sse(body)
    done = events[-1][1]
    assert isinstance(done, dict)
    assert done.get("refusal_reason") == "insufficient_evidence"
    explain = done.get("explain")
    assert isinstance(explain, dict)
    assert explain.get("refusal", {}).get("category") == "evidence"
