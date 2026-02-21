from __future__ import annotations

import importlib
import os

from fastapi.testclient import TestClient


_ENV_KEYS = [
    "SQLITE_PATH",
    "PUBLIC_DEMO_MODE",
    "AUTH_MODE",
    "ALLOW_UPLOADS",
    "BOOTSTRAP_DEMO_CORPUS",
    "RATE_LIMIT_ENABLED",
    "MAX_QUERY_PAYLOAD_BYTES",
]


def _reload_app(sqlite_path: str, *, max_query_payload_bytes: int) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "none"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"
    os.environ["RATE_LIMIT_ENABLED"] = "0"
    os.environ["MAX_QUERY_PAYLOAD_BYTES"] = str(max_query_payload_bytes)

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


def _restore_env(before: dict[str, str | None]) -> None:
    for key, value in before.items():
        if value is None:
            os.environ.pop(key, None)
            continue
        os.environ[key] = value


def test_query_payload_limit_enforced(tmp_path):
    before = {k: os.environ.get(k) for k in _ENV_KEYS}
    try:
        main = _reload_app(str(tmp_path / "payload_limit.sqlite"), max_query_payload_bytes=256)
        client = TestClient(main.app)
        large_question = "x" * 2048

        resp = client.post("/api/query", json={"question": large_question, "top_k": 3})
        assert resp.status_code == 413, resp.text
        assert "Payload too large" in resp.text
    finally:
        _restore_env(before)


def test_query_stream_payload_limit_enforced(tmp_path):
    before = {k: os.environ.get(k) for k in _ENV_KEYS}
    try:
        main = _reload_app(str(tmp_path / "payload_limit_stream.sqlite"), max_query_payload_bytes=256)
        client = TestClient(main.app)
        large_question = "x" * 2048

        resp = client.post("/api/query/stream", json={"question": large_question, "top_k": 3})
        assert resp.status_code == 413, resp.text
        assert "Payload too large" in resp.text
    finally:
        _restore_env(before)


def test_meta_reports_query_payload_limit(tmp_path):
    before = {k: os.environ.get(k) for k in _ENV_KEYS}
    try:
        main = _reload_app(str(tmp_path / "payload_limit_meta.sqlite"), max_query_payload_bytes=16384)
        client = TestClient(main.app)

        meta = client.get("/api/meta")
        assert meta.status_code == 200, meta.text
        assert meta.json()["max_query_payload_bytes"] == 16384
    finally:
        _restore_env(before)
