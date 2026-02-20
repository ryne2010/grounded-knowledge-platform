from __future__ import annotations

import importlib
import os

from fastapi.testclient import TestClient


def _reload_app(sqlite_path: str) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "none"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"
    os.environ["OTEL_ENABLED"] = "0"

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


def test_query_path_records_http_and_stage_metrics(tmp_path):
    main = _reload_app(str(tmp_path / "metrics.sqlite"))
    client = TestClient(main.app)

    metric_calls: dict[str, list[dict[str, object]]] = {
        "http": [],
        "safety": [],
        "retrieval": [],
        "generation": [],
    }

    def _http_metric(**kwargs):
        metric_calls["http"].append(dict(kwargs))

    def _safety_metric(**kwargs):
        metric_calls["safety"].append(dict(kwargs))

    def _retrieval_metric(**kwargs):
        metric_calls["retrieval"].append(dict(kwargs))

    def _generation_metric(**kwargs):
        metric_calls["generation"].append(dict(kwargs))

    main.record_http_request_metric = _http_metric
    main.record_safety_scan_metric = _safety_metric
    main.record_retrieval_metric = _retrieval_metric
    main.record_generation_metric = _generation_metric

    ingest = client.post(
        "/api/ingest/text",
        json={
            "title": "Metric Doc",
            "source": "unit-test",
            "text": "Cloud Run is a managed runtime that scales to zero.",
        },
    )
    assert ingest.status_code == 200, ingest.text

    query = client.post("/api/query", json={"question": "What is Cloud Run?", "top_k": 3})
    assert query.status_code == 200, query.text
    assert query.json().get("refused") is False

    assert any(call.get("path") == "/api/query" for call in metric_calls["http"])
    assert len(metric_calls["safety"]) >= 1
    assert len(metric_calls["retrieval"]) >= 1
    assert len(metric_calls["generation"]) >= 1
