from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

from .config import settings

logger = logging.getLogger(__name__)

_OTEL_READY = False
_OTEL_SETUP_ATTEMPTED = False
_TRACER: Any = None


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
    if _OTEL_SETUP_ATTEMPTED:
        return _OTEL_READY
    _OTEL_SETUP_ATTEMPTED = True

    if not settings.otel_enabled:
        return False

    try:
        from opentelemetry import trace  # type: ignore[import-not-found]
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore[import-not-found]
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore[import-not-found]
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
