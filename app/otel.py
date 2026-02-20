from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

from .config import settings

logger = logging.getLogger(__name__)

_OTEL_READY = False
_OTEL_SETUP_ATTEMPTED = False
_TRACER: Any = None
_HTTP_COUNTER: Any = None
_HTTP_LATENCY_MS: Any = None
_RETRIEVAL_LATENCY_MS: Any = None
_GENERATION_LATENCY_MS: Any = None
_SAFETY_LATENCY_MS: Any = None


def otel_enabled() -> bool:
    return bool(settings.otel_enabled) and _OTEL_READY


def setup_otel(app: Any) -> bool:
    """Configure FastAPI tracing when OTEL is enabled.

    Design goals:
    - near-zero overhead when OTEL is disabled
    - no hard dependency on otel packages for local demo mode
    - Cloud Run friendly OTLP endpoint override
    """

    global _OTEL_READY, _OTEL_SETUP_ATTEMPTED, _TRACER
    global _HTTP_COUNTER, _HTTP_LATENCY_MS, _RETRIEVAL_LATENCY_MS, _GENERATION_LATENCY_MS, _SAFETY_LATENCY_MS
    if _OTEL_SETUP_ATTEMPTED:
        return _OTEL_READY
    _OTEL_SETUP_ATTEMPTED = True

    if not settings.otel_enabled:
        return False

    try:
        from opentelemetry import metrics as otel_metrics  # type: ignore[import-not-found]
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore[import-not-found]
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore[import-not-found]
        from opentelemetry.sdk.metrics import MeterProvider  # type: ignore[import-not-found]
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader  # type: ignore[import-not-found]
        from opentelemetry.sdk.resources import Resource  # type: ignore[import-not-found]
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore[import-not-found]
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore[import-not-found]
    except Exception as e:  # pragma: no cover
        logger.warning("OTEL enabled but dependencies missing; tracing disabled. error=%s", e)
        return False

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)

    endpoint = settings.otel_exporter_otlp_endpoint
    if endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    else:
        # Keep setup valid even if no exporter endpoint is configured.
        # Operators can still wire endpoint later via env vars.
        logger.info("OTEL enabled without OTLP endpoint; spans will stay local to process")

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    _TRACER = trace.get_tracer("gkp")

    # Metrics are best-effort; tracing should still work if metric setup fails.
    try:
        metric_readers: list[Any] = []
        if endpoint:
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import (  # type: ignore[import-not-found]
                OTLPMetricExporter,
            )

            metric_readers.append(PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint)))
        meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
        otel_metrics.set_meter_provider(meter_provider)
        meter = otel_metrics.get_meter("gkp")
        _HTTP_COUNTER = meter.create_counter(
            name="gkp.http.server.requests",
            unit="1",
            description="HTTP requests handled by the API",
        )
        _HTTP_LATENCY_MS = meter.create_histogram(
            name="gkp.http.server.duration_ms",
            unit="ms",
            description="HTTP request latency in milliseconds",
        )
        _RETRIEVAL_LATENCY_MS = meter.create_histogram(
            name="gkp.query.retrieval.duration_ms",
            unit="ms",
            description="Retrieval stage latency in milliseconds",
        )
        _GENERATION_LATENCY_MS = meter.create_histogram(
            name="gkp.query.generation.duration_ms",
            unit="ms",
            description="Answer generation latency in milliseconds",
        )
        _SAFETY_LATENCY_MS = meter.create_histogram(
            name="gkp.query.safety_scan.duration_ms",
            unit="ms",
            description="Prompt-injection scan latency in milliseconds",
        )
    except Exception as e:  # pragma: no cover
        logger.warning("OTEL metric setup failed; continuing with tracing only. error=%s", e)

    _OTEL_READY = True
    return True


@contextmanager
def span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[Any]:
    """Start a tracing span when OTEL is active; otherwise no-op."""

    if not _OTEL_READY or _TRACER is None:
        yield None
        return

    with _TRACER.start_as_current_span(name) as s:
        if attributes:
            for k, v in attributes.items():
                if v is None:
                    continue
                # Guard against non-serializable values.
                if isinstance(v, (str, bool, int, float)):
                    s.set_attribute(k, v)
                else:
                    s.set_attribute(k, str(v))
        yield s


def _attrs(attrs: dict[str, Any] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not attrs:
        return out
    for k, v in attrs.items():
        if v is None:
            continue
        out[str(k)] = v if isinstance(v, (str, bool, int, float)) else str(v)
    return out


def record_http_request_metric(*, method: str, path: str, status_code: int, latency_ms: float) -> None:
    if not _OTEL_READY:
        return
    attrs = _attrs({"http.method": method, "http.route": path, "http.status_code": int(status_code)})
    if _HTTP_COUNTER is not None:
        _HTTP_COUNTER.add(1, attributes=attrs)
    if _HTTP_LATENCY_MS is not None:
        _HTTP_LATENCY_MS.record(float(latency_ms), attributes=attrs)


def record_retrieval_metric(*, latency_ms: float, top_k: int, backend: str) -> None:
    if not _OTEL_READY or _RETRIEVAL_LATENCY_MS is None:
        return
    _RETRIEVAL_LATENCY_MS.record(
        float(latency_ms),
        attributes=_attrs({"retrieval.top_k": int(top_k), "retrieval.backend": backend}),
    )


def record_generation_metric(*, latency_ms: float, provider: str, streaming: bool) -> None:
    if not _OTEL_READY or _GENERATION_LATENCY_MS is None:
        return
    _GENERATION_LATENCY_MS.record(
        float(latency_ms),
        attributes=_attrs({"llm.provider": provider, "llm.streaming": bool(streaming)}),
    )


def record_safety_scan_metric(*, latency_ms: float) -> None:
    if not _OTEL_READY or _SAFETY_LATENCY_MS is None:
        return
    _SAFETY_LATENCY_MS.record(float(latency_ms), attributes={})
