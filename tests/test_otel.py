from __future__ import annotations

import importlib
import os

import pytest
from fastapi.testclient import TestClient

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
except Exception:  # pragma: no cover
    pytest.skip("OpenTelemetry packages are not installed", allow_module_level=True)


def _reload_app(sqlite_path: str) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "none"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"
    os.environ["OTEL_ENABLED"] = "1"
    os.environ["OTEL_SERVICE_NAME"] = "gkp-test"
    os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
    os.environ.pop("OTEL_TRACES_EXPORTER", None)
    os.environ.pop("K_SERVICE", None)

    import app.config as config
    import app.ingestion as ingestion
    import app.main as main
    import app.otel as otel
    import app.retrieval as retrieval
    import app.storage as storage

    importlib.reload(config)
    importlib.reload(storage)
    importlib.reload(otel)
    importlib.reload(ingestion)
    importlib.reload(retrieval)
    importlib.reload(main)
    return main


def test_trace_exporter_mode_resolution():
    os.environ["OTEL_ENABLED"] = "1"
    os.environ["OTEL_SERVICE_NAME"] = "gkp-test"
    os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
    os.environ["OTEL_TRACES_EXPORTER"] = "auto"
    os.environ.pop("K_SERVICE", None)

    import app.config as config
    import app.otel as otel

    importlib.reload(config)
    importlib.reload(otel)
    assert otel._resolve_trace_exporter_mode() == "none"

    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://collector:4318/v1/traces"
    importlib.reload(config)
    importlib.reload(otel)
    assert otel._resolve_trace_exporter_mode() == "otlp"

    os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
    os.environ["K_SERVICE"] = "gkp-stage"
    importlib.reload(config)
    importlib.reload(otel)
    assert otel._resolve_trace_exporter_mode() == "gcp_trace"


def test_query_request_emits_key_spans_and_preserves_request_id(tmp_path):
    main = _reload_app(str(tmp_path / "otel.sqlite"))

    exporter = InMemorySpanExporter()
    provider = trace.get_tracer_provider()
    if not hasattr(provider, "add_span_processor"):
        pytest.skip("Tracer provider does not support span processors in this environment")
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    client = TestClient(main.app)
    ingest = client.post(
        "/api/ingest/text",
        json={
            "title": "OTEL Doc",
            "source": "unit-test",
            "text": "Cloud Run is a serverless runtime for containers.",
        },
    )
    assert ingest.status_code == 200, ingest.text

    rid = "req-otel-123"
    query = client.post(
        "/api/query",
        headers={"X-Request-Id": rid},
        json={"question": "What is Cloud Run?", "top_k": 3},
    )
    assert query.status_code == 200, query.text
    assert query.headers.get("x-request-id") == rid

    names = {s.name for s in exporter.get_finished_spans()}
    assert "safety.prompt_injection_scan" in names
    assert "retrieval.retrieve" in names
    assert "generation.answer" in names


def test_query_request_logs_include_trace_and_span_ids_without_incoming_trace_header(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    main = _reload_app(str(tmp_path / "otel_logs.sqlite"))
    captured_logs: list[dict[str, object]] = []

    def _capture_log_http_request(**kwargs):
        captured_logs.append(dict(kwargs))

    monkeypatch.setattr(main, "log_http_request", _capture_log_http_request)

    client = TestClient(main.app)
    ingest = client.post(
        "/api/ingest/text",
        json={
            "title": "OTEL Log Doc",
            "source": "unit-test",
            "text": "Cloud Trace correlation should include trace ids when OTEL is enabled.",
        },
    )
    assert ingest.status_code == 200, ingest.text

    rid = "req-otel-log-456"
    query = client.post(
        "/api/query",
        headers={"X-Request-Id": rid},
        json={"question": "What does Cloud Trace correlation include?", "top_k": 3},
    )
    assert query.status_code == 200, query.text
    assert query.headers.get("x-request-id") == rid

    query_logs = [entry for entry in captured_logs if entry.get("path") == "/api/query"]
    assert query_logs, "expected at least one structured log for /api/query"

    latest = query_logs[-1]
    assert latest.get("request_id") == rid
    trace_id = latest.get("trace_id")
    span_id = latest.get("span_id")
    assert isinstance(trace_id, str) and len(trace_id) == 32
    assert isinstance(span_id, str) and len(span_id) == 16
