from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any, Mapping, Optional, Tuple


def configure_logging() -> None:
    """Configure application logging.

    We intentionally emit **JSON lines** so GCP Cloud Logging parses them into
    `jsonPayload` fields automatically.

    This keeps the demo lightweight (no extra logging dependencies) while still
    enabling structured filtering by request_id, latency, status, etc.
    """

    level_name = os.getenv("LOG_LEVEL", "INFO").upper().strip()
    level = getattr(logging, level_name, logging.INFO)

    # Configure a dedicated logger so Uvicorn's logging config doesn't clobber
    # our JSON formatting.
    logger = logging.getLogger("gkp")
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))

    # Replace handlers so repeated imports don't duplicate logs.
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False


def parse_cloud_trace_context(headers: Mapping[str, str]) -> Tuple[Optional[str], Optional[str]]:
    """Parse the Cloud Trace header.

    Cloud Run (and other GCP services) often forward `X-Cloud-Trace-Context`:
    "TRACE_ID/SPAN_ID;o=TRACE_TRUE".
    """

    raw = headers.get("x-cloud-trace-context")
    if not raw:
        return None, None

    parts = raw.split("/")
    trace_id = parts[0].strip() if parts and parts[0].strip() else None
    span_id: Optional[str] = None
    if len(parts) > 1:
        span_part = parts[1].split(";")[0].strip()
        span_id = span_part or None
    return trace_id, span_id


def _cloud_trace_resource(trace_id: Optional[str]) -> Optional[str]:
    """Return a trace resource name for Cloud Logging, if possible."""

    if not trace_id:
        return None
    project = (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT")
        or os.getenv("PROJECT_ID")
        or ""
    ).strip()
    if not project:
        return None
    return f"projects/{project}/traces/{trace_id}"


def request_id_from_headers(headers: Mapping[str, str]) -> str:
    """Determine a request ID.

    Preference order:
      1) X-Request-Id (reverse proxies)
      2) X-Correlation-Id (some enterprise setups)
      3) generated UUID4
    """

    rid = headers.get("x-request-id") or headers.get("x-correlation-id")
    return (rid.strip() if rid else "") or str(uuid.uuid4())


def log_http_request(
    *,
    request_id: str,
    method: str,
    url: str,
    path: str,
    status: int,
    latency_ms: float,
    remote_ip: str,
    user_agent: str,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    limited: bool = False,
    error_type: Optional[str] = None,
    severity: str = "INFO",
) -> None:
    """Emit a Cloud Logging-friendly structured request log."""

    logger = logging.getLogger("gkp")

    payload: dict[str, Any] = {
        "severity": severity,
        "message": "http_request",
        "service": os.getenv("K_SERVICE", "grounded-knowledge-platform"),
        "revision": os.getenv("K_REVISION", ""),
        "request_id": request_id,
        "path": path,
        "limited": limited,
        "latency_ms": round(latency_ms, 2),
        "httpRequest": {
            "requestMethod": method,
            "requestUrl": url,
            "status": status,
            # Cloud Logging expects a duration string, e.g. "0.123s".
            "latency": f"{latency_ms / 1000.0:.3f}s",
            "remoteIp": remote_ip,
            "userAgent": user_agent,
        },
    }

    if error_type:
        payload["error_type"] = error_type

    # If we can determine a GCP trace ID, include it so request logs correlate.
    trace = _cloud_trace_resource(trace_id)
    if trace:
        payload["logging.googleapis.com/trace"] = trace
    if span_id:
        payload["logging.googleapis.com/spanId"] = span_id

    logger.info(json.dumps(payload, ensure_ascii=False))


class Timer:
    """Tiny helper for timing blocks."""

    def __init__(self) -> None:
        self._t0 = time.perf_counter()

    def ms(self) -> float:
        return (time.perf_counter() - self._t0) * 1000.0
