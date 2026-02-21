from __future__ import annotations

import base64
import binascii
import json
import logging
import re
import time
import uuid
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .answering import get_answerer
from .auth import AuthContext, AuthError, effective_auth_mode, require_role, resolve_auth_context
from .bootstrap import bootstrap_demo_corpus
from .config import settings
from .eval import run_eval
from .ingestion import ingest_file, ingest_text
from .metadata import CLASSIFICATIONS, RETENTIONS, normalize_classification, normalize_retention, normalize_tags
from .otel import (
    record_generation_metric,
    record_http_request_metric,
    record_retrieval_metric,
    record_safety_scan_metric,
    setup_otel,
    span,
)
from .observability import (
    Timer,
    configure_logging,
    log_http_request,
    parse_cloud_trace_context,
    request_id_from_headers,
)
from .ratelimit import SlidingWindowRateLimiter
from .retrieval import RetrievedChunk, invalidate_cache, retrieve
from .safety import detect_prompt_injection
from .storage import (
    complete_ingestion_run,
    connect,
    create_ingestion_run,
    delete_doc,
    get_chunk,
    get_doc,
    get_ingestion_run,
    get_meta,
    init_db,
    insert_audit_event,
    list_audit_events,
    list_ingest_events_for_run,
    update_doc_metadata,
    list_ingestion_runs,
    list_all_chunks_for_doc,
    list_chunks_for_doc,
    list_docs,
    list_ingest_events,
    list_recent_ingest_events,
)

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "then",
    "else",
    "when",
    "while",
    "to",
    "of",
    "for",
    "in",
    "on",
    "at",
    "by",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "from",
    "up",
    "down",
    "out",
    "over",
    "under",
    "again",
    "further",
    "once",
    "here",
    "there",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "can",
    "will",
    "just",
    "should",
    "could",
    "would",
    "may",
    "might",
    "must",
    "do",
    "does",
    "did",
    "doing",
    "done",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "me",
    "him",
    "her",
    "us",
    "them",
    "my",
    "your",
    "yours",
    "his",
    "hers",
    "its",
    "our",
    "their",
    "what",
    "which",
    "who",
    "whom",
    "whose",
    "where",
    "when",
    "why",
    "how",
    "tell",
    "show",
    "explain",
    "describe",
    "list",
    "give",
    "summarize",
    "summarise",
    "define",
    "meaning",
    "mean",
    "means",
    "stand",
    "stands",
    "refers",
    "refer",
    "related",
    "relation",
    "relate",
    "about",
    "information",
    "info",
    "source",
    "sources",
    "provided",
    "provide",
    "using",
    "use",
    "used",
    "usage",
    "vs",
    "versus",
    "example",
    "examples",
    "please",
    "thanks",
    "thank",
}

_RELATIONSHIP_TERMS = {
    "related",
    "relationship",
    "relate",
    "between",
    "compare",
    "comparison",
    "difference",
    "different",
    "vs",
    "versus",
    "associate",
    "associated",
    "link",
    "linked",
    "connection",
    "connected",
}


# ---- Security headers ----
_CSP_STRICT = (
    "default-src 'self'; img-src 'self' data:; connect-src 'self'; "
    "script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
)

_CSP_SWAGGER = (
    # Swagger UI needs inline/eval for its bundled scripts/styles.
    "default-src 'self'; img-src 'self' data:; connect-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; "
    "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
)


def _csp_for_path(path: str) -> str:
    p = path or ""
    # Swagger/Redoc need a looser CSP (inline/eval) to run correctly.
    if p.startswith(("/api/swagger", "/api/redoc", "/api/openapi")):
        return _CSP_SWAGGER
    return _CSP_STRICT


def _term_variants(term: str) -> list[str]:
    variants = [term]
    if term.endswith("ies") and len(term) > 4:
        variants.append(f"{term[:-3]}y")
    if term.endswith("es") and len(term) > 4:
        variants.append(term[:-2])
    if term.endswith("s") and len(term) > 3:
        variants.append(term[:-1])
    return variants


def _extract_key_terms(question: str) -> list[str]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(question or "")]
    terms = []
    for t in tokens:
        if t in _STOPWORDS:
            continue
        if len(t) < 3:
            continue
        if not any(ch.isalpha() for ch in t):
            continue
        terms.append(t)
    return terms


def _is_relationship_question(question: str) -> bool:
    tokens = {t.lower() for t in _TOKEN_RE.findall(question or "")}
    return any(t in _RELATIONSHIP_TERMS for t in tokens)


def _is_unrelated_question(question: str, retrieved: list[Any]) -> bool:
    terms = _extract_key_terms(question)
    if not terms:
        return False
    text = " ".join(r.text for r in retrieved[: settings.max_context_chunks]).lower()
    if not text:
        return True
    hits = 0
    for term in terms:
        if any(v in text for v in _term_variants(term)):
            hits += 1

    if hits == 0:
        return True

    if _is_relationship_question(question) and len(terms) >= 2:
        return hits < len(terms)

    if len(terms) <= 2:
        return hits < 1

    return (hits / len(terms)) < 0.6


APP_DIR = Path(__file__).resolve().parent
WEB_DIR = (APP_DIR.parent / "web").resolve()
DIST_DIR = (WEB_DIR / "dist").resolve()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """FastAPI lifespan.

    FastAPI deprecated `@app.on_event("startup")` in favor of lifespan handlers.
    We keep startup logic here so it runs for both TestClient and production.
    """

    # Ensure DB schema exists and (optionally) bootstrap a demo corpus.
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
    bootstrap_demo_corpus()

    yield


app = FastAPI(
    title="Grounded Knowledge Platform",
    version=settings.version,
    docs_url="/api/swagger",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure JSON logging early so Cloud Run/Cloud Logging parses fields.
configure_logging()
setup_otel(app)

logger = logging.getLogger("gkp")

# Lightweight compression for JSON responses and static assets.
app.add_middleware(GZipMiddleware, minimum_size=1000)

_limiter = SlidingWindowRateLimiter(
    window_s=settings.rate_limit_window_s,
    max_requests=settings.rate_limit_max_requests,
)


def _should_rate_limit(path: str) -> bool:
    """Decide whether to apply rate limiting for a given path.

    In public demo mode we default to limiting the expensive `/api/query` endpoint,
    but allow operators to expand the limiter to all API routes.
    """

    p = path or ""
    scope = (settings.rate_limit_scope or "query").strip().lower()
    if scope == "api":
        if not p.startswith("/api/"):
            return False
        # Don't rate limit API docs; they can be chatty (assets + schema fetches).
        if p.startswith(("/api/swagger", "/api/redoc", "/api/openapi")):
            return False
        return True

    # Default: only the query endpoint.
    return p == "/api/query"


def _log_auth_denied(*, request_id: str, path: str, status: int, reason: str) -> None:
    """Emit a dedicated auth-denied event for security/audit filtering."""

    logger.warning(
        json.dumps(
            {
                "severity": "WARNING",
                "event": "auth.denied",
                "request_id": request_id,
                "path": path,
                "status": int(status),
                "reason": reason,
                "auth_mode": effective_auth_mode(),
            },
            ensure_ascii=False,
        )
    )


def _auth_denied_reason_from_response(request: Request, status: int, response: Any) -> str:
    state_reason = getattr(request.state, "auth_denied_reason", None)
    if isinstance(state_reason, str) and state_reason.strip():
        return state_reason.strip()

    body = getattr(response, "body", None)
    if isinstance(body, (bytes, bytearray)) and body:
        try:
            payload = json.loads(body.decode("utf-8"))
            detail = payload.get("detail")
            if isinstance(detail, str) and detail.strip():
                return detail.strip()
        except Exception:
            pass

    return "Unauthorized" if int(status) == 401 else "Forbidden"


@app.middleware("http")
async def _request_middleware(request: Request, call_next):
    """Attach request ID, enforce demo safety controls, emit structured logs."""

    timer = Timer()
    rid = request_id_from_headers({k.lower(): v for k, v in request.headers.items()})
    request.state.request_id = rid

    # Prefer X-Forwarded-For in managed environments (Cloud Run).
    xff = request.headers.get("x-forwarded-for")
    remote_ip = (xff.split(",")[0].strip() if xff else None) or (request.client.host if request.client else "unknown")
    user_agent = request.headers.get("user-agent", "")

    # Cloud Trace correlation (if present).
    trace_id, span_id = parse_cloud_trace_context({k.lower(): v for k, v in request.headers.items()})

    # ---- Auth context (if enabled) ----
    try:
        auth_ctx = resolve_auth_context(request)
    except AuthError as ae:
        latency_ms = timer.ms()
        _log_auth_denied(
            request_id=rid,
            path=request.url.path,
            status=int(ae.status_code),
            reason=str(ae.detail),
        )
        record_http_request_metric(
            method=request.method,
            path=request.url.path,
            status_code=int(ae.status_code),
            latency_ms=latency_ms,
        )
        log_http_request(
            request_id=rid,
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            status=int(ae.status_code),
            latency_ms=latency_ms,
            remote_ip=remote_ip,
            user_agent=user_agent,
            trace_id=trace_id,
            span_id=span_id,
            error_type="AuthError",
            severity="WARNING",
        )
        return JSONResponse(
            status_code=ae.status_code,
            content={"detail": ae.detail},
            headers={"X-Request-Id": rid},
        )
    request.state.auth_context = auth_ctx
    request.state.principal = auth_ctx.principal
    request.state.role = auth_ctx.role

    # ---- Rate limiting (defense-in-depth) ----
    # In demo mode this is enabled by default; private deployments can opt in via RATE_LIMIT_ENABLED=1.
    if settings.rate_limit_enabled and _should_rate_limit(request.url.path):
        if not _limiter.allow(remote_ip):
            latency_ms = timer.ms()
            record_http_request_metric(
                method=request.method,
                path=request.url.path,
                status_code=429,
                latency_ms=latency_ms,
            )
            log_http_request(
                request_id=rid,
                method=request.method,
                url=str(request.url),
                path=request.url.path,
                status=429,
                latency_ms=latency_ms,
                remote_ip=remote_ip,
                user_agent=user_agent,
                trace_id=trace_id,
                span_id=span_id,
                limited=True,
                severity="WARNING",
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"X-Request-Id": rid},
            )

    # ---- Normal request execution ----
    try:
        response = await call_next(request)
    except HTTPException as he:
        latency_ms = timer.ms()
        if int(he.status_code) in {401, 403}:
            _log_auth_denied(
                request_id=rid,
                path=request.url.path,
                status=int(he.status_code),
                reason=str(he.detail),
            )
        record_http_request_metric(
            method=request.method,
            path=request.url.path,
            status_code=int(he.status_code),
            latency_ms=latency_ms,
        )
        log_http_request(
            request_id=rid,
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            status=int(he.status_code),
            latency_ms=latency_ms,
            remote_ip=remote_ip,
            user_agent=user_agent,
            trace_id=trace_id,
            span_id=span_id,
            error_type="HTTPException",
            severity="WARNING" if he.status_code < 500 else "ERROR",
        )
        raise
    except Exception as e:
        latency_ms = timer.ms()
        record_http_request_metric(
            method=request.method,
            path=request.url.path,
            status_code=500,
            latency_ms=latency_ms,
        )
        log_http_request(
            request_id=rid,
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            status=500,
            latency_ms=latency_ms,
            remote_ip=remote_ip,
            user_agent=user_agent,
            trace_id=trace_id,
            span_id=span_id,
            error_type=type(e).__name__,
            severity="ERROR",
        )
        raise

    # Attach request ID for client correlation.
    response.headers["X-Request-Id"] = rid

    # Basic security headers (safe defaults for a SPA + JSON API).
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=()",
    )
    response.headers.setdefault("Content-Security-Policy", _csp_for_path(request.url.path))

    # Only set HSTS when we're actually behind HTTPS.
    if request.headers.get("x-forwarded-proto") == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

    # Avoid caching API responses in browsers/proxies.
    # (Useful for private deployments where responses may contain sensitive snippets.)
    if request.url.path.startswith("/api/") or request.url.path in ("/health", "/ready"):
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("Pragma", "no-cache")

    latency_ms = timer.ms()
    status_code = int(response.status_code)
    if status_code in {401, 403}:
        _log_auth_denied(
            request_id=rid,
            path=request.url.path,
            status=status_code,
            reason=_auth_denied_reason_from_response(request, status_code, response),
        )
    record_http_request_metric(
        method=request.method,
        path=request.url.path,
        status_code=status_code,
        latency_ms=latency_ms,
    )
    log_http_request(
        request_id=rid,
        method=request.method,
        url=str(request.url),
        path=request.url.path,
        status=status_code,
        latency_ms=latency_ms,
        remote_ip=remote_ip,
        user_agent=user_agent,
        trace_id=trace_id,
        span_id=span_id,
        severity="INFO",
    )
    return response


@app.exception_handler(HTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException):
    """Ensure error responses include X-Request-Id and basic security headers."""
    rid = getattr(request.state, "request_id", None)
    headers: dict[str, str] = {}
    if rid:
        headers["X-Request-Id"] = rid
    headers["X-Content-Type-Options"] = "nosniff"
    headers["X-Frame-Options"] = "DENY"
    headers["Referrer-Policy"] = "no-referrer"
    headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    headers["Content-Security-Policy"] = _csp_for_path(request.url.path)
    if request.headers.get("x-forwarded-proto") == "https":
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    if request.url.path.startswith("/api/") or request.url.path in ("/health", "/ready"):
        headers["Cache-Control"] = "no-store"
        headers["Pragma"] = "no-cache"

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    """Return a safe JSON 500 (and keep request correlation + security headers)."""
    rid = getattr(request.state, "request_id", None)
    headers: dict[str, str] = {}
    if rid:
        headers["X-Request-Id"] = rid
    headers["X-Content-Type-Options"] = "nosniff"
    headers["X-Frame-Options"] = "DENY"
    headers["Referrer-Policy"] = "no-referrer"
    headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    headers["Content-Security-Policy"] = _csp_for_path(request.url.path)
    if request.headers.get("x-forwarded-proto") == "https":
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    if request.url.path.startswith("/api/") or request.url.path in ("/health", "/ready"):
        headers["Cache-Control"] = "no-store"
        headers["Pragma"] = "no-cache"

    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"}, headers=headers)


# ---- API models ----
class IngestTextRequest(BaseModel):
    title: str = Field(..., description="Document title")
    source: str = Field(..., description="A source label/URL/path")
    text: str = Field(..., description="Document content")
    doc_id: str | None = Field(None, description="Optional stable id")
    classification: str | None = Field(None, description="public|internal|confidential|restricted")
    retention: str | None = Field(None, description="none|30d|90d|1y|indefinite")
    tags: list[str] | None = Field(None, description="Optional tags")
    notes: str | None = Field(None, description="Optional ingest note")


class GCSSyncRequest(BaseModel):
    bucket: str = Field(..., description="GCS bucket name (no gs:// prefix)")
    prefix: str = Field("", description="Optional prefix under the bucket (folder-like)")
    max_objects: int = Field(200, ge=1, le=5000, description="Max number of objects to scan")
    dry_run: bool = Field(False, description="If true, list what would be ingested but make no DB changes")
    classification: str | None = Field(None, description="public|internal|confidential|restricted")
    retention: str | None = Field(None, description="none|30d|90d|1y|indefinite")
    tags: list[str] | None = Field(None, description="Optional tags to apply to all ingested docs")
    notes: str | None = Field(None, description="Optional ingest notes (applied to all docs)")


_GCS_FINALIZE_EVENT_TYPES = {
    "OBJECT_FINALIZE",
    "OBJECT_FINALIZED",
    "google.cloud.storage.object.v1.finalized",
}


def _first_nonempty_str(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        s = str(value).strip()
        if s:
            return s
    return ""


def _coerce_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _decode_pubsub_message_data(raw_data: str) -> dict[str, Any]:
    data = str(raw_data or "").strip()
    if not data:
        return {}
    try:
        decoded = base64.b64decode(data)
    except binascii.Error as e:
        raise ValueError("Invalid Pub/Sub message.data (base64 decode failed)") from e
    try:
        payload = json.loads(decoded.decode("utf-8"))
    except Exception as e:
        raise ValueError("Invalid Pub/Sub message.data (JSON decode failed)") from e
    if not isinstance(payload, dict):
        raise ValueError("Invalid Pub/Sub message.data (expected JSON object)")
    return payload


def _extract_gcs_notify_payload(body: dict[str, Any]) -> dict[str, Any]:
    message = body.get("message")
    if not isinstance(message, dict):
        raise ValueError("Invalid Pub/Sub push payload: missing `message` object")

    attributes = message.get("attributes")
    attrs = attributes if isinstance(attributes, dict) else {}
    data_payload: dict[str, Any] = {}
    if "data" in message and message.get("data") is not None:
        data_payload = _decode_pubsub_message_data(str(message.get("data")))

    bucket = _first_nonempty_str(
        attrs.get("bucketId"),
        data_payload.get("bucketId"),
        data_payload.get("bucket"),
    )
    object_name = _first_nonempty_str(
        attrs.get("objectId"),
        data_payload.get("objectId"),
        data_payload.get("name"),
    )
    if not bucket or not object_name:
        raise ValueError("Invalid Pub/Sub push payload: bucketId/objectId (or data fallback) required")

    return {
        "message_id": _first_nonempty_str(message.get("messageId"), message.get("message_id")),
        "event_type": _first_nonempty_str(attrs.get("eventType"), data_payload.get("eventType")),
        "bucket": bucket,
        "object_name": object_name,
        "generation": _first_nonempty_str(attrs.get("objectGeneration"), data_payload.get("generation")) or None,
        "size": _coerce_int_or_none(_first_nonempty_str(attrs.get("objectSize"), data_payload.get("size"))),
    }


def _require_private_connectors_admin(request: Request) -> AuthContext:
    # Keep endpoint hidden for demo/disabled deployments.
    if settings.public_demo_mode or not settings.allow_connectors:
        raise HTTPException(status_code=404, detail="Not found")
    return require_role("admin")(request)


_AUDIT_REDACT_KEY_FRAGMENTS = {
    "secret",
    "token",
    "password",
    "api_key",
    "authorization",
    "content",
    "text",
    "quote",
}


def _sanitize_audit_metadata(value: Any, *, key: str | None = None) -> Any:
    if key is not None:
        k = key.strip().lower()
        if any(fragment in k for fragment in _AUDIT_REDACT_KEY_FRAGMENTS):
            return "[redacted]"

    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:500]
    if isinstance(value, list):
        return [_sanitize_audit_metadata(v) for v in value[:100]]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            out[str(k)] = _sanitize_audit_metadata(v, key=str(k))
        return out
    return str(value)


def _record_audit_event(
    conn: Any,
    *,
    auth_ctx: AuthContext,
    request: Request | None,
    action: str,
    target_type: str,
    target_id: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    metadata_obj = metadata or {}
    metadata_json = json.dumps(_sanitize_audit_metadata(metadata_obj), ensure_ascii=False)
    request_id = getattr(getattr(request, "state", None), "request_id", None) if request is not None else None
    insert_audit_event(
        conn,
        event_id=uuid.uuid4().hex,
        principal=str(auth_ctx.principal),
        role=str(auth_ctx.role),
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata_json,
        request_id=str(request_id) if request_id else None,
    )



class DocUpdateRequest(BaseModel):
    title: str | None = Field(None, description="Optional new title")
    source: str | None = Field(None, description="Optional new source label/URL/path")
    classification: str | None = Field(None, description="public|internal|confidential|restricted")
    retention: str | None = Field(None, description="none|30d|90d|1y|indefinite")
    tags: list[str] | None = Field(None, description="Optional tags")


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    debug: bool = False


class EvalRequest(BaseModel):
    golden_path: str = "data/eval/golden.jsonl"
    k: int = 5
    include_details: bool = False


class ChunkSearchResult(BaseModel):
    chunk_id: str
    doc_id: str
    idx: int
    score: float | None = None
    text_preview: str
    doc_title: str
    doc_source: str
    classification: str
    tags: list[str]


class ChunkSearchResponse(BaseModel):
    query: str
    results: list[ChunkSearchResult]


class TopTagStat(BaseModel):
    tag: str
    count: int


class StatsResponse(BaseModel):
    docs: int
    chunks: int
    embeddings: int
    ingest_events: int
    by_classification: dict[str, int]
    by_retention: dict[str, int]
    top_tags: list[TopTagStat]


class ExpiredDoc(BaseModel):
    doc_id: str
    title: str
    retention: str
    updated_at: int


class ExpiredDocsResponse(BaseModel):
    now: int
    expired: list[ExpiredDoc]


class IngestionRunSummary(BaseModel):
    run_id: str
    started_at: int
    finished_at: int | None = None
    status: str
    trigger_type: str
    trigger_payload: dict[str, object]
    principal: str | None = None
    objects_scanned: int
    docs_changed: int
    docs_unchanged: int
    bytes_processed: int
    errors: list[str]
    event_count: int


class IngestionRunsResponse(BaseModel):
    runs: list[IngestionRunSummary]


class IngestionRunDetailResponse(BaseModel):
    run: IngestionRunSummary
    events: list[dict[str, object]]


class AuditEventItem(BaseModel):
    event_id: str
    occurred_at: int
    principal: str
    role: str
    action: str
    target_type: str
    target_id: str | None = None
    metadata: dict[str, Any]
    request_id: str | None = None


class AuditEventsResponse(BaseModel):
    events: list[AuditEventItem]


# ---- Health ----
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, object]:
    """Readiness probe.

    Checks that the app can open the backing store and run a trivial query.
    Returns 503 if initialization fails.
    """

    try:
        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            conn.execute("SELECT 1").fetchone()
    except Exception as e:
        logger.exception("Readiness probe failed")
        raise HTTPException(status_code=503, detail=f"not ready: {e}") from e

    return {"ready": True, "version": app.version, "public_demo_mode": settings.public_demo_mode}


@app.get("/api/meta")
def meta(_auth: AuthContext = Depends(require_role("reader"))) -> dict[str, object]:
    """Small metadata endpoint for the UI and diagnostics."""
    uploads_enabled = bool(settings.allow_uploads and not settings.public_demo_mode)
    metadata_edit_enabled = bool(uploads_enabled and _auth.role in {"editor", "admin"})
    connectors_enabled = bool(settings.allow_connectors and not settings.public_demo_mode)
    eval_enabled = bool(settings.allow_eval and not settings.public_demo_mode)
    chunk_view_enabled = bool(settings.allow_chunk_view and not settings.public_demo_mode)
    doc_delete_enabled = bool(settings.allow_doc_delete and not settings.public_demo_mode)

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        doc_count = int(conn.execute("SELECT COUNT(1) AS n FROM docs").fetchone()["n"])
        chunk_count = int(conn.execute("SELECT COUNT(1) AS n FROM chunks").fetchone()["n"])
        embedding_rows = int(conn.execute("SELECT COUNT(1) AS n FROM embeddings").fetchone()["n"])

        sig_keys = [
            "index.embeddings_backend",
            "index.embeddings_model",
            "index.embedding_dim",
            "index.hash_embedder_version",
            "index.chunk_size_chars",
            "index.chunk_overlap_chars",
        ]
        index_signature = {k: get_meta(conn, k) for k in sig_keys}

    return {
        "version": app.version,
        "public_demo_mode": settings.public_demo_mode,
        "auth_mode": settings.auth_mode if not settings.public_demo_mode else "none",
        "database_backend": "postgres" if settings.database_url else "sqlite",
        "uploads_enabled": uploads_enabled,
        "metadata_edit_enabled": metadata_edit_enabled,
        "connectors_enabled": connectors_enabled,
        "eval_enabled": eval_enabled,
        "chunk_view_enabled": chunk_view_enabled,
        "doc_delete_enabled": doc_delete_enabled,
        "citations_required": bool(settings.citations_required),
        "rate_limit_enabled": bool(settings.rate_limit_enabled),
        "rate_limit_scope": settings.rate_limit_scope,
        "rate_limit_window_s": settings.rate_limit_window_s,
        "rate_limit_max_requests": settings.rate_limit_max_requests,
        "api_docs_url": "/api/swagger",
        "max_upload_bytes": settings.max_upload_bytes,
        "max_top_k": settings.max_top_k,
        "top_k_default": settings.top_k_default,
        "max_question_chars": settings.max_question_chars,
        "llm_provider": settings.effective_llm_provider,
        "embeddings_backend": settings.embeddings_backend,
        "ocr_enabled": settings.ocr_enabled,
        "stats": {
            "docs": doc_count,
            "chunks": chunk_count,
            "embeddings": embedding_rows,
        },
        "index_signature": index_signature,
        "doc_classifications": list(CLASSIFICATIONS),
        "doc_retentions": list(RETENTIONS),
    }


@app.get("/api/stats", response_model=StatsResponse)
def stats_api(_auth: Any = Depends(require_role("reader"))) -> StatsResponse:
    """Index-level statistics for dashboards and diagnostics."""

    with connect(settings.sqlite_path) as conn:
        init_db(conn)

        docs = int(conn.execute("SELECT COUNT(1) AS n FROM docs").fetchone()["n"])
        chunks = int(conn.execute("SELECT COUNT(1) AS n FROM chunks").fetchone()["n"])
        embeddings = int(conn.execute("SELECT COUNT(1) AS n FROM embeddings").fetchone()["n"])
        ingest_events = int(conn.execute("SELECT COUNT(1) AS n FROM ingest_events").fetchone()["n"])

        by_classification: dict[str, int] = {}
        cur = conn.execute("SELECT classification, COUNT(1) AS n FROM docs GROUP BY classification")
        for r in cur.fetchall():
            by_classification[str(r["classification"])] = int(r["n"])

        by_retention: dict[str, int] = {}
        cur = conn.execute("SELECT retention, COUNT(1) AS n FROM docs GROUP BY retention")
        for r in cur.fetchall():
            by_retention[str(r["retention"])] = int(r["n"])

        # Tags are stored as JSON text; SQLite json1 is not always available,
        # so compute in Python.
        tag_counts: dict[str, int] = {}
        cur = conn.execute("SELECT tags_json FROM docs")
        for r in cur.fetchall():
            try:
                tags = json.loads(r["tags_json"] or "[]")
            except Exception:
                tags = []
            if not isinstance(tags, list):
                continue
            for t in tags:
                k = str(t).strip().lower()
                if not k:
                    continue
                tag_counts[k] = tag_counts.get(k, 0) + 1

        top_tags = [
            TopTagStat(tag=t, count=c) for t, c in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:25]
        ]

    return StatsResponse(
        docs=docs,
        chunks=chunks,
        embeddings=embeddings,
        ingest_events=ingest_events,
        by_classification=by_classification,
        by_retention=by_retention,
        top_tags=top_tags,
    )


# ---- Maintenance (safe read-only helpers) ----
@app.get("/api/maintenance/retention/expired", response_model=ExpiredDocsResponse)
def maintenance_retention_expired(
    now: int | None = None, _auth: Any = Depends(require_role("reader"))
) -> ExpiredDocsResponse:
    """List documents whose retention policy has expired.

    This endpoint is intentionally **read-only** (no deletes). It powers the UI
    maintenance page and helps operators confirm what would be purged.

    For actual deletes, use the CLI:
      - `uv run python -m app.cli purge-expired` (dry-run)
      - `uv run python -m app.cli purge-expired --apply`
    """

    now_i = int(now) if now is not None else int(time.time())
    from .maintenance import find_expired_docs

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        expired = find_expired_docs(conn, now=now_i)

    return ExpiredDocsResponse(
        now=now_i,
        expired=[
            ExpiredDoc(
                doc_id=d.doc_id,
                title=d.title,
                retention=str(d.retention),
                updated_at=int(d.updated_at),
            )
            for d in expired
        ],
    )


# ---- Docs ----
@app.get("/api/docs")
def docs(_auth: Any = Depends(require_role("reader"))) -> dict[str, Any]:
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        items = list_docs(conn)
    return {"docs": [d.to_dict() for d in items]}


@app.get("/api/docs/{doc_id}")
def doc_detail(doc_id: str, _auth: Any = Depends(require_role("reader"))) -> dict[str, Any]:
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        doc = get_doc(conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Doc not found")
        events = list_ingest_events(conn, doc_id, limit=20)
    return {
        "doc": doc.to_dict(),
        "ingest_events": [e.to_dict() for e in events],
    }


@app.patch("/api/docs/{doc_id}")
def doc_update(
    doc_id: str,
    req: DocUpdateRequest,
    request: Request,
    _auth: AuthContext = Depends(require_role("editor")),
) -> dict[str, Any]:
    """Update doc metadata (title/source/classification/retention/tags).

    This endpoint is intentionally **disabled** in PUBLIC_DEMO_MODE.
    In private deployments it is gated behind ALLOW_UPLOADS=1 (same trust boundary as ingest).
    """

    if settings.public_demo_mode or not settings.allow_uploads:
        raise HTTPException(status_code=403, detail="Doc edit endpoint disabled in this deployment")

    def _clean_required(v: str | None, field: str) -> str | None:
        if v is None:
            return None
        vv = str(v).strip()
        if not vv:
            raise HTTPException(status_code=400, detail=f"{field} must be non-empty")
        return vv

    title = _clean_required(req.title, "title")
    source = _clean_required(req.source, "source")

    classification: str | None = None
    if req.classification is not None:
        if not str(req.classification).strip():
            raise HTTPException(status_code=400, detail="classification must be non-empty")
        try:
            classification = normalize_classification(req.classification)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    retention: str | None = None
    if req.retention is not None:
        if not str(req.retention).strip():
            raise HTTPException(status_code=400, detail="retention must be non-empty")
        try:
            retention = normalize_retention(req.retention)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    tags_json: str | None = None
    if req.tags is not None:
        try:
            tags_json = json.dumps(normalize_tags(req.tags))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid tags: {e}") from e

    changed_fields = [
        field
        for field, value in (
            ("title", title),
            ("source", source),
            ("classification", classification),
            ("retention", retention),
            ("tags", tags_json),
        )
        if value is not None
    ]

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        doc = get_doc(conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Doc not found")

        update_doc_metadata(
            conn,
            doc_id=doc_id,
            title=title,
            source=source,
            classification=classification,
            retention=retention,
            tags_json=tags_json,
        )
        if changed_fields:
            _record_audit_event(
                conn,
                auth_ctx=_auth,
                request=request,
                action="doc.metadata.updated",
                target_type="doc",
                target_id=doc_id,
                metadata={
                    "fields": changed_fields,
                    "classification": classification,
                    "retention": retention,
                    "tags_count": len(req.tags or []) if req.tags is not None else None,
                },
            )
        conn.commit()

        updated = get_doc(conn, doc_id)
        if updated is None:
            raise HTTPException(status_code=404, detail="Doc not found")

    return {"doc": updated.to_dict()}


@app.get("/api/ingest/events")
def list_ingest_events_api(
    limit: int = 100,
    doc_id: str | None = None,
    _auth: Any = Depends(require_role("reader")),
) -> dict[str, Any]:
    """List recent ingest events across docs (audit/lineage view)."""
    limit = max(1, min(int(limit), 500))
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        events = list_recent_ingest_events(conn, limit=limit, doc_id=doc_id)
    return {"events": [e.to_dict() for e in events]}


@app.get("/api/ingestion-runs", response_model=IngestionRunsResponse)
def ingestion_runs_api(limit: int = 100, _auth: Any = Depends(require_role("reader"))) -> IngestionRunsResponse:
    limit = max(1, min(int(limit), 500))
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        runs = list_ingestion_runs(conn, limit=limit)
    return IngestionRunsResponse(runs=[IngestionRunSummary.model_validate(r.to_dict()) for r in runs])


@app.get("/api/ingestion-runs/{run_id}", response_model=IngestionRunDetailResponse)
def ingestion_run_detail_api(run_id: str, _auth: Any = Depends(require_role("reader"))) -> IngestionRunDetailResponse:
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        run = get_ingestion_run(conn, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Ingestion run not found")
        events = list_ingest_events_for_run(conn, run_id, limit=1000)
    return IngestionRunDetailResponse(
        run=IngestionRunSummary.model_validate(run.to_dict()),
        events=[e.to_dict() for e in events],
    )


@app.get("/api/audit-events", response_model=AuditEventsResponse)
def audit_events_api(
    limit: int = 100,
    action: str | None = None,
    since: int | None = None,
    until: int | None = None,
    _auth: AuthContext = Depends(require_role("admin")),
) -> AuditEventsResponse:
    limit = max(1, min(int(limit), 1000))
    if since is not None and until is not None and int(since) > int(until):
        raise HTTPException(status_code=400, detail="since must be <= until")

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        events = list_audit_events(
            conn,
            limit=limit,
            action=action,
            since=int(since) if since is not None else None,
            until=int(until) if until is not None else None,
        )

    return AuditEventsResponse(events=[AuditEventItem.model_validate(e.to_dict()) for e in events])


@app.get("/api/docs/{doc_id}/chunks")
def doc_chunks(
    doc_id: str,
    limit: int = 200,
    offset: int = 0,
    _auth: Any = Depends(require_role("admin")),
) -> dict[str, Any]:
    if settings.public_demo_mode or not settings.allow_chunk_view:
        raise HTTPException(status_code=403, detail="Chunk view is disabled in this deployment")

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        doc = get_doc(conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Doc not found")
        chunks = list_chunks_for_doc(conn, doc_id, limit=limit, offset=offset)

    return {
        "doc": doc.to_dict(),
        "chunks": [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "idx": c.idx,
                "text_preview": c.text[:240],
            }
            for c in chunks
        ],
        "limit": max(1, min(int(limit), 500)),
        "offset": max(0, int(offset)),
    }


@app.get("/api/docs/{doc_id}/text")
def doc_text(doc_id: str, _auth: Any = Depends(require_role("admin"))) -> PlainTextResponse:
    """Export a doc as plain text.

    This is useful for debugging and for copying a document out of the system.
    It is gated behind the same flag as chunk viewing.

    Note: because we store overlapped chunks for retrieval, export attempts to
    *de-overlap* using the latest ingest event's chunk_overlap_chars.
    """

    if settings.public_demo_mode or not settings.allow_chunk_view:
        raise HTTPException(status_code=403, detail="Doc export is disabled in this deployment")

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        doc = get_doc(conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Doc not found")

        events = list_ingest_events(conn, doc_id, limit=1)
        overlap = int(events[0].chunk_overlap_chars) if events else int(settings.chunk_overlap_chars)

        chunks = list_all_chunks_for_doc(conn, doc_id, limit=doc.num_chunks)

    # Reconstruct in a best-effort way.
    out_parts: list[str] = []
    prev_text: str | None = None
    truncated = len(chunks) < doc.num_chunks
    for c in chunks:
        txt = c.text
        if prev_text is not None and overlap > 0:
            prev_tail = prev_text[-overlap:]
            if txt.startswith(prev_tail + "\n"):
                txt = txt[len(prev_tail) + 1 :]
            elif txt.startswith(prev_tail):
                txt = txt[len(prev_tail) :]
                txt = txt.lstrip("\n")
        out_parts.append(txt.strip())
        prev_text = c.text

    body = "\n\n".join([p for p in out_parts if p])
    header_lines = [
        f"Title: {doc.title}",
        f"Doc ID: {doc.doc_id}",
        f"Source: {doc.source}",
        f"Version: {doc.doc_version}",
        f"Classification: {doc.classification}",
        f"Retention: {doc.retention}",
        f"Tags: {', '.join(doc.tags) if doc.tags else ''}",
        f"Export overlap_chars={overlap}",
    ]
    if truncated:
        header_lines.append(f"WARNING: export truncated at {len(chunks)}/{doc.num_chunks} chunks")
    header_lines.append("")

    text = "\n".join(header_lines) + body + "\n"
    return PlainTextResponse(text, media_type="text/plain")


@app.get("/api/chunks/{chunk_id}")
def chunk_detail(chunk_id: str, _auth: Any = Depends(require_role("admin"))) -> dict[str, Any]:
    if settings.public_demo_mode or not settings.allow_chunk_view:
        raise HTTPException(status_code=403, detail="Chunk view is disabled in this deployment")

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        c = get_chunk(conn, chunk_id)
        if c is None:
            raise HTTPException(status_code=404, detail="Chunk not found")
        doc = get_doc(conn, c.doc_id)

    return {
        "chunk": {
            "chunk_id": c.chunk_id,
            "doc_id": c.doc_id,
            "idx": c.idx,
            "text": c.text,
            "doc_title": doc.title if doc else None,
            "doc_source": doc.source if doc else None,
        }
    }


@app.get("/api/search/chunks", response_model=ChunkSearchResponse)
def search_chunks(q: str, limit: int = 20, _auth: Any = Depends(require_role("reader"))) -> ChunkSearchResponse:
    """Lightweight chunk search for the UI.

    - Uses SQLite FTS5 when available.
    - Falls back to a simple lexical overlap score.
    """

    limit = max(1, min(int(limit), 50))
    tokens = [t.lower() for t in _TOKEN_RE.findall(q) if t.lower() not in _STOPWORDS]
    if not tokens:
        return ChunkSearchResponse(query=q, results=[])

    fts_query = " ".join(tokens)

    with connect(settings.sqlite_path) as conn:
        init_db(conn)

        results: list[ChunkSearchResult] = []

        # Prefer FTS5 if available.
        try:
            cur = conn.execute(
                """
                SELECT
                    c.chunk_id,
                    c.doc_id,
                    c.idx,
                    substr(c.text, 1, 240) AS preview,
                    bm25(chunks_fts) AS bm,
                    d.title AS doc_title,
                    d.source AS doc_source,
                    d.classification AS classification,
                    d.tags_json AS tags_json
                FROM chunks_fts
                JOIN chunks c ON chunks_fts.chunk_id = c.chunk_id
                JOIN docs d ON c.doc_id = d.doc_id
                WHERE chunks_fts MATCH ?
                ORDER BY bm
                LIMIT ?
                """,
                (fts_query, limit),
            )
            for r in cur.fetchall():
                try:
                    tags = json.loads(r["tags_json"] or "[]")
                except Exception:
                    tags = []
                # bm25: smaller is better; expose a "higher is better" score.
                bm = float(r["bm"])
                score = -bm
                results.append(
                    ChunkSearchResult(
                        chunk_id=str(r["chunk_id"]),
                        doc_id=str(r["doc_id"]),
                        idx=int(r["idx"]),
                        score=score,
                        text_preview=str(r["preview"] or ""),
                        doc_title=str(r["doc_title"]),
                        doc_source=str(r["doc_source"]),
                        classification=str(r["classification"]),
                        tags=[str(t) for t in tags] if isinstance(tags, list) else [],
                    )
                )

            return ChunkSearchResponse(query=q, results=results)
        except Exception:
            # FTS unavailable; continue to lexical fallback.
            pass

        # Lexical fallback (token overlap).
        cur = conn.execute(
            """
            SELECT c.chunk_id, c.doc_id, c.idx, c.text,
                   d.title AS doc_title, d.source AS doc_source,
                   d.classification AS classification, d.tags_json AS tags_json
            FROM chunks c
            JOIN docs d ON c.doc_id = d.doc_id
            ORDER BY d.updated_at DESC, c.idx ASC
            """
        )
        scored: list[tuple[float, ChunkSearchResult]] = []
        tokset = set(tokens)
        for r in cur.fetchall():
            text = str(r["text"] or "")
            ctoks = {t.lower() for t in _TOKEN_RE.findall(text)}
            overlap = len(tokset & ctoks)
            if overlap == 0:
                continue
            try:
                tags = json.loads(r["tags_json"] or "[]")
            except Exception:
                tags = []
            scored.append(
                (
                    float(overlap),
                    ChunkSearchResult(
                        chunk_id=str(r["chunk_id"]),
                        doc_id=str(r["doc_id"]),
                        idx=int(r["idx"]),
                        score=float(overlap),
                        text_preview=text[:240],
                        doc_title=str(r["doc_title"]),
                        doc_source=str(r["doc_source"]),
                        classification=str(r["classification"]),
                        tags=[str(t) for t in tags] if isinstance(tags, list) else [],
                    ),
                )
            )

        scored.sort(key=lambda x: x[0], reverse=True)
        return ChunkSearchResponse(query=q, results=[r for _, r in scored[:limit]])


@app.delete("/api/docs/{doc_id}")
def delete_doc_api(doc_id: str, request: Request, _auth: AuthContext = Depends(require_role("admin"))) -> dict[str, Any]:
    if settings.public_demo_mode or not settings.allow_doc_delete:
        raise HTTPException(status_code=403, detail="Delete is disabled in this deployment")

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        doc = get_doc(conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Doc not found")
        _record_audit_event(
            conn,
            auth_ctx=_auth,
            request=request,
            action="doc.deleted",
            target_type="doc",
            target_id=doc_id,
            metadata={
                "classification": str(doc.classification),
                "retention": str(doc.retention),
                "doc_version": int(doc.doc_version),
                "num_chunks": int(doc.num_chunks),
            },
        )
        delete_doc(conn, doc_id)
        conn.commit()

    invalidate_cache()
    return {"deleted": True, "doc_id": doc_id}


# ---- Ingest ----
@app.post("/api/ingest/text")
def ingest_text_api(req: IngestTextRequest, _auth: Any = Depends(require_role("editor"))) -> dict[str, Any]:
    if settings.public_demo_mode or not settings.allow_uploads:
        raise HTTPException(status_code=403, detail="Uploads are disabled in this deployment")

    try:
        res = ingest_text(
            title=req.title,
            source=req.source,
            text=req.text,
            doc_id=req.doc_id,
            classification=req.classification,
            retention=req.retention,
            tags=req.tags,
            notes=req.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    invalidate_cache()
    return {
        "doc_id": res.doc_id,
        "doc_version": res.doc_version,
        "changed": res.changed,
        "num_chunks": res.num_chunks,
        "embedding_dim": res.embedding_dim,
        "content_sha256": res.content_sha256,
    }

# ---- Connectors ----
@app.post("/api/connectors/gcs/sync")
def gcs_sync_api(
    req: GCSSyncRequest, request: Request, _auth: AuthContext = Depends(require_role("admin"))
) -> dict[str, Any]:
    """Trigger a one-off sync from a GCS prefix (private deployments only).

    This is intentionally disabled in PUBLIC_DEMO_MODE and when ALLOW_CONNECTORS=0.
    """

    if settings.public_demo_mode or not settings.allow_connectors:
        raise HTTPException(status_code=403, detail="Connectors are disabled in this deployment")

    from .connectors.gcs import sync_prefix

    run_id = uuid.uuid4().hex
    trigger_payload = {
        "bucket": req.bucket,
        "prefix": req.prefix or "",
        "max_objects": int(req.max_objects),
        "dry_run": bool(req.dry_run),
        "classification": req.classification,
        "retention": req.retention,
        "tags": req.tags,
    }
    principal = getattr(_auth, "principal", None)
    scheduler_job_name = (request.headers.get("x-cloudscheduler-jobname") or "").strip()
    is_scheduled_trigger = bool((request.headers.get("x-cloudscheduler") or "").strip() or scheduler_job_name)

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        create_ingestion_run(
            conn,
            run_id=run_id,
            trigger_type="connector",
            trigger_payload_json=json.dumps(trigger_payload, ensure_ascii=False),
            principal=principal,
        )
        _record_audit_event(
            conn,
            auth_ctx=_auth,
            request=request,
            action="connector.gcs.sync.triggered",
            target_type="ingestion_run",
            target_id=run_id,
            metadata={
                "bucket": req.bucket,
                "prefix": req.prefix or "",
                "max_objects": int(req.max_objects),
                "dry_run": bool(req.dry_run),
                "classification": req.classification,
                "retention": req.retention,
                "tags_count": len(req.tags or []),
            },
        )
        conn.commit()

    try:
        res = sync_prefix(
            bucket=req.bucket,
            prefix=req.prefix or "",
            max_objects=req.max_objects,
            dry_run=req.dry_run,
            classification=req.classification,
            retention=req.retention,
            tags=req.tags,
            notes=req.notes,
            run_id=run_id,
        )
        bytes_processed = sum(int(r.get("size") or 0) for r in (res.get("results") or []))
        docs_changed = int(res.get("changed") or 0)
        docs_ingested = int(res.get("ingested") or 0)
        docs_unchanged = max(0, docs_ingested - docs_changed)
        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            complete_ingestion_run(
                conn,
                run_id=run_id,
                status="succeeded",
                objects_scanned=int(res.get("scanned") or 0),
                docs_changed=docs_changed,
                docs_unchanged=docs_unchanged,
                bytes_processed=bytes_processed,
                errors_json=json.dumps(res.get("errors") or [], ensure_ascii=False),
            )
            conn.commit()
    except ValueError as e:
        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            complete_ingestion_run(
                conn,
                run_id=run_id,
                status="failed",
                objects_scanned=0,
                docs_changed=0,
                docs_unchanged=0,
                bytes_processed=0,
                errors_json=json.dumps([str(e)], ensure_ascii=False),
            )
            conn.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            complete_ingestion_run(
                conn,
                run_id=run_id,
                status="failed",
                objects_scanned=0,
                docs_changed=0,
                docs_unchanged=0,
                bytes_processed=0,
                errors_json=json.dumps([str(e)], ensure_ascii=False),
            )
            conn.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            complete_ingestion_run(
                conn,
                run_id=run_id,
                status="failed",
                objects_scanned=0,
                docs_changed=0,
                docs_unchanged=0,
                bytes_processed=0,
                errors_json=json.dumps([str(e)], ensure_ascii=False),
            )
            conn.commit()
        raise

    invalidate_cache()
    if is_scheduled_trigger:
        logger.info(
            json.dumps(
                {
                    "event": "connector.gcs.sync.scheduled",
                    "job_name": scheduler_job_name or "unknown",
                    "bucket": req.bucket,
                    "prefix": req.prefix or "",
                    "run_id": run_id,
                },
                ensure_ascii=False,
            )
        )
    return res


@app.post("/api/connectors/gcs/notify", status_code=202)
def gcs_notify_api(
    body: dict[str, Any],
    _auth: AuthContext = Depends(_require_private_connectors_admin),
) -> dict[str, Any]:
    """Handle a Pub/Sub push envelope for a single GCS object finalize event."""

    from .connectors.gcs import ingest_object

    timer = Timer()
    try:
        event = _extract_gcs_notify_payload(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    message_id = str(event.get("message_id") or "")
    event_type = str(event.get("event_type") or "")
    bucket = str(event["bucket"])
    object_name = str(event["object_name"])
    generation = event.get("generation")
    size = event.get("size")
    gcs_uri = f"gs://{bucket}/{object_name}"

    if event_type and event_type not in _GCS_FINALIZE_EVENT_TYPES:
        logger.info(
            json.dumps(
                {
                    "event": "connector.gcs.notify",
                    "pubsub_message_id": message_id,
                    "gcs_uri": gcs_uri,
                    "result": "ignored_event",
                    "event_type": event_type,
                    "latency_ms": timer.ms(),
                },
                ensure_ascii=False,
            )
        )
        return {
            "accepted": True,
            "run_id": None,
            "pubsub_message_id": message_id,
            "gcs_uri": gcs_uri,
            "result": "ignored_event",
        }

    run_id = uuid.uuid4().hex
    trigger_payload = {
        "source": "pubsub_push",
        "bucket": bucket,
        "object": object_name,
        "generation": generation,
        "message_id": message_id,
        "event_type": event_type or "OBJECT_FINALIZE",
    }
    principal = getattr(_auth, "principal", None)
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        create_ingestion_run(
            conn,
            run_id=run_id,
            trigger_type="connector",
            trigger_payload_json=json.dumps(trigger_payload, ensure_ascii=False),
            principal=principal,
        )
        conn.commit()

    try:
        result = ingest_object(
            bucket=bucket,
            object_name=object_name,
            generation=generation if isinstance(generation, str) else None,
            notes=f"pubsub_message_id={message_id}" if message_id else None,
            run_id=run_id,
            expected_size=size if isinstance(size, int) else None,
        )
        action = str(result.get("action") or "accepted")
        docs_changed = 1 if bool(result.get("changed")) else 0
        docs_unchanged = 1 if action == "unchanged" else 0
        bytes_processed = int(result.get("size") or 0)

        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            complete_ingestion_run(
                conn,
                run_id=run_id,
                status="succeeded",
                objects_scanned=1,
                docs_changed=docs_changed,
                docs_unchanged=docs_unchanged,
                bytes_processed=bytes_processed,
                errors_json="[]",
            )
            conn.commit()
    except ValueError as e:
        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            complete_ingestion_run(
                conn,
                run_id=run_id,
                status="failed",
                objects_scanned=1,
                docs_changed=0,
                docs_unchanged=0,
                bytes_processed=0,
                errors_json=json.dumps([str(e)], ensure_ascii=False),
            )
            conn.commit()
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            complete_ingestion_run(
                conn,
                run_id=run_id,
                status="failed",
                objects_scanned=1,
                docs_changed=0,
                docs_unchanged=0,
                bytes_processed=0,
                errors_json=json.dumps([str(e)], ensure_ascii=False),
            )
            conn.commit()
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            complete_ingestion_run(
                conn,
                run_id=run_id,
                status="failed",
                objects_scanned=1,
                docs_changed=0,
                docs_unchanged=0,
                bytes_processed=0,
                errors_json=json.dumps([str(e)], ensure_ascii=False),
            )
            conn.commit()
        raise

    invalidate_cache()
    logger.info(
        json.dumps(
            {
                "event": "connector.gcs.notify",
                "pubsub_message_id": message_id,
                "gcs_uri": gcs_uri,
                "result": str(result.get("action") or "accepted"),
                "run_id": run_id,
                "latency_ms": timer.ms(),
            },
            ensure_ascii=False,
        )
    )
    return {
        "accepted": True,
        "run_id": run_id,
        "pubsub_message_id": message_id,
        "gcs_uri": gcs_uri,
        "result": str(result.get("action") or "accepted"),
        "changed": bool(result.get("changed")),
        "doc_id": result.get("doc_id"),
    }




@app.post("/api/ingest/file")
async def ingest_file_api(
    file: UploadFile = File(...),
    contract_file: UploadFile | None = File(None),
    title: str | None = Form(None),
    source: str | None = Form(None),
    classification: str | None = Form(None),
    retention: str | None = Form(None),
    tags: str | None = Form(None),
    notes: str | None = Form(None),
    _auth: Any = Depends(require_role("editor")),
) -> dict[str, Any]:
    if settings.public_demo_mode or not settings.allow_uploads:
        raise HTTPException(status_code=403, detail="Uploads are disabled in this deployment")

    orig_name = file.filename or "upload.txt"
    safe_name = Path(orig_name).name
    # Best-effort sanitization (defense-in-depth against weird filenames).
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", safe_name)

    suffix = Path(safe_name).suffix.lower()
    if suffix not in {".txt", ".md", ".pdf", ".csv", ".tsv", ".xlsx", ".xlsm"}:
        raise HTTPException(status_code=400, detail="Only .txt, .md, .pdf, .csv, .tsv, .xlsx, .xlsm supported")

    tmp_dir = Path("/tmp/gkp_uploads")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    contract_bytes: bytes | None = None
    if contract_file is not None:
        raw = await contract_file.read()
        if len(raw) > 64 * 1024:
            raise HTTPException(status_code=400, detail="Contract file too large (max 65536 bytes)")
        contract_bytes = bytes(raw)

    # Unique temp file path (avoid cross-request collisions).
    stem = Path(safe_name).stem
    tmp_path = tmp_dir / f"{stem}_{uuid.uuid4().hex}{suffix}"

    # Stream upload to disk with size limit.
    total = 0
    try:
        with tmp_path.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=413, detail=f"File too large (max {settings.max_upload_bytes} bytes)"
                    )
                f.write(chunk)

        try:
            res = ingest_file(
                tmp_path,
                title=title,
                source=source,
                classification=classification,
                retention=retention,
                tags=tags,
                notes=notes,
                contract_bytes=contract_bytes,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass
    invalidate_cache()
    return {
        "doc_id": res.doc_id,
        "doc_version": res.doc_version,
        "changed": res.changed,
        "num_chunks": res.num_chunks,
        "embedding_dim": res.embedding_dim,
        "content_sha256": res.content_sha256,
    }


# ---- Query ----
_STREAM_SENT_RE = re.compile(r"(?<=[.!?])\s+")


def _sse_event(event: str, data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _stream_text_chunks(text: str) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []
    chunks = [c.strip() for c in _STREAM_SENT_RE.split(raw) if c.strip()]
    if chunks:
        return chunks
    return [raw]


def _load_doc_map(doc_ids: set[str] | None = None) -> dict[str, Any]:
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        docs = list_docs(conn)
    if not doc_ids:
        return {d.doc_id: d for d in docs}
    return {d.doc_id: d for d in docs if d.doc_id in doc_ids}


def _retrieval_debug_payload(retrieved: list[RetrievedChunk], *, include_text: bool) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for r in retrieved:
        item: dict[str, Any] = {
            "chunk_id": r.chunk_id,
            "doc_id": r.doc_id,
            "idx": r.idx,
            "score": r.score,
            "lexical_score": r.lexical_score,
            "vector_score": r.vector_score,
            "text_preview": r.text[:240],
        }
        if include_text:
            item["text"] = r.text
        payload.append(item)
    return payload


def _signal_summary(r: RetrievedChunk) -> str:
    lex = float(r.lexical_score)
    vec = float(r.vector_score)
    if lex >= 0.35 and vec >= 0.35:
        return "keyword + semantic relevance"
    if vec > lex:
        return "semantic relevance"
    if lex > vec:
        return "keyword relevance"
    return "hybrid relevance"


def _refusal_details(refusal_reason: str | None) -> dict[str, Any]:
    reason = str(refusal_reason or "")
    if not reason:
        return {
            "refused": False,
            "code": None,
            "category": None,
            "message": "Answer grounded in cited evidence from the indexed corpus.",
        }
    if reason.startswith("prompt_injection:"):
        return {
            "refused": True,
            "code": reason,
            "category": "safety",
            "message": "The request matched prompt-injection safeguards, so the system refused.",
        }
    if reason == "insufficient_evidence":
        return {
            "refused": True,
            "code": reason,
            "category": "evidence",
            "message": "Retrieved evidence was insufficient or unrelated to safely answer.",
        }
    if reason == "answerer_refused":
        return {
            "refused": True,
            "code": reason,
            "category": "model",
            "message": "The answering model declined to produce an answer.",
        }
    if reason == "internal_error":
        return {
            "refused": True,
            "code": reason,
            "category": "system",
            "message": "The system hit an internal error while answering.",
        }
    return {
        "refused": True,
        "code": reason,
        "category": "unknown",
        "message": "The system refused this request.",
    }


def _build_explain_payload(
    *,
    question: str,
    top_k: int,
    retrieved: list[RetrievedChunk],
    citations_out: list[dict[str, Any]],
    refusal_reason: str | None,
    doc_map: dict[str, Any] | None,
    debug: bool,
) -> dict[str, Any]:
    selected_chunk_ids = {str(c.get("chunk_id", "")) for c in citations_out if c.get("chunk_id")}
    evidence: list[dict[str, Any]] = []
    capped = retrieved[: min(8, len(retrieved))]
    private_detail_enabled = bool(debug) and not bool(settings.public_demo_mode)

    for r in capped:
        d = doc_map.get(r.doc_id) if isinstance(doc_map, dict) else None
        selected = r.chunk_id in selected_chunk_ids
        item: dict[str, Any] = {
            "doc_id": r.doc_id,
            "doc_title": d.title if d else None,
            "doc_source": d.source if d else None,
            "snippet": r.text[:240],
            "selected": selected,
            "why_selected": "used in the final cited answer" if selected else f"high {_signal_summary(r)}",
        }
        if private_detail_enabled:
            item.update(
                {
                    "chunk_id": r.chunk_id,
                    "idx": r.idx,
                    "score": r.score,
                    "lexical_score": r.lexical_score,
                    "vector_score": r.vector_score,
                }
            )
        evidence.append(item)

    return {
        "question": question,
        "evidence_used": evidence,
        "how_retrieval_works": {
            "summary": "Hybrid retrieval combines lexical keyword matching and semantic similarity, then reranks chunks.",
            "top_k": int(top_k),
            "retrieved_chunks": len(retrieved),
            "public_demo_mode": bool(settings.public_demo_mode),
            "debug_details_included": private_detail_enabled,
        },
        "refusal": _refusal_details(refusal_reason),
    }


@app.post("/api/query")
def query_api(req: QueryRequest, _auth: Any = Depends(require_role("reader"))) -> dict[str, Any]:
    """Core query endpoint.

    Staff-grade behaviors:
      - prompt injection / circumvention refusal (defense-in-depth)
      - citations-required grounding (refuse if no evidence)
      - stable response contract (answer/refused/refusal_reason/citations/provider)
    """

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    if len(question) > settings.max_question_chars:
        raise HTTPException(status_code=400, detail=f"Question too long (max {settings.max_question_chars} chars)")

    # Clamp knobs for public demos.
    top_k = max(1, min(int(req.top_k or settings.top_k_default), settings.max_top_k))
    debug = bool(req.debug) and not settings.public_demo_mode
    include_retrieval_text = bool(settings.allow_chunk_view) and not settings.public_demo_mode
    refusal_reason: str | None = None

    # --- Prompt-injection/circumvention detection ---
    safety_start = time.perf_counter()
    with span(
        "safety.prompt_injection_scan",
        attributes={"question_length": len(question), "otel_debug_content": bool(settings.otel_debug_content)},
    ):
        inj = detect_prompt_injection(question)
    record_safety_scan_metric(latency_ms=(time.perf_counter() - safety_start) * 1000.0)
    if inj.is_injection:
        refusal_reason = f"prompt_injection:{','.join(inj.reasons)}"
        return {
            "question": question,
            "answer": "I can’t help with that request. I can only answer questions using the provided sources.",
            "refused": True,
            "refusal_reason": refusal_reason,
            "provider": "policy",
            "citations": [],
            "explain": _build_explain_payload(
                question=question,
                top_k=top_k,
                retrieved=[],
                citations_out=[],
                refusal_reason=refusal_reason,
                doc_map={},
                debug=debug,
            ),
        }

    # --- Retrieve ---
    retrieval_start = time.perf_counter()
    with span(
        "retrieval.retrieve",
        attributes={"top_k": top_k, "embeddings_backend": settings.embeddings_backend},
    ):
        retrieved = retrieve(question, top_k=top_k)
    record_retrieval_metric(
        latency_ms=(time.perf_counter() - retrieval_start) * 1000.0,
        top_k=top_k,
        backend=settings.embeddings_backend,
    )
    context = [(r.chunk_id, r.doc_id, r.idx, r.text) for r in retrieved]

    if not context:
        refusal_reason = "insufficient_evidence"
        out_no_context: dict[str, Any] = {
            "question": question,
            "answer": "I don’t have enough evidence in the indexed sources to answer that.",
            "refused": True,
            "refusal_reason": refusal_reason,
            "provider": "policy",
            "citations": [],
        }
        if debug:
            out_no_context["retrieval"] = _retrieval_debug_payload(retrieved, include_text=include_retrieval_text)
        out_no_context["explain"] = _build_explain_payload(
            question=question,
            top_k=top_k,
            retrieved=retrieved,
            citations_out=[],
            refusal_reason=refusal_reason,
            doc_map={},
            debug=debug,
        )
        return out_no_context

    if _is_unrelated_question(question, retrieved):
        refusal_reason = "insufficient_evidence"
        doc_map = _load_doc_map({r.doc_id for r in retrieved})
        out_unrelated: dict[str, Any] = {
            "question": question,
            "answer": "I don’t have enough evidence in the indexed sources to answer that.",
            "refused": True,
            "refusal_reason": refusal_reason,
            "provider": "policy",
            "citations": [],
        }
        if debug:
            out_unrelated["retrieval"] = _retrieval_debug_payload(retrieved, include_text=include_retrieval_text)
        out_unrelated["explain"] = _build_explain_payload(
            question=question,
            top_k=top_k,
            retrieved=retrieved,
            citations_out=[],
            refusal_reason=refusal_reason,
            doc_map=doc_map,
            debug=debug,
        )
        return out_unrelated

    # --- Answer ---
    answerer = get_answerer()
    generation_start = time.perf_counter()
    with span(
        "generation.answer",
        attributes={
            "provider": getattr(answerer, "name", settings.effective_llm_provider),
            "context_chunks": len(context),
        },
    ):
        ans = answerer.answer(question, context)
    record_generation_metric(
        latency_ms=(time.perf_counter() - generation_start) * 1000.0,
        provider=str(getattr(answerer, "name", settings.effective_llm_provider)),
        streaming=False,
    )

    # Enrich citations with doc metadata.
    citations_out: list[dict[str, Any]] = []
    doc_map = _load_doc_map({r.doc_id for r in retrieved})

    for c in ans.citations or []:
        d = doc_map.get(c.doc_id)
        citations_out.append(
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "idx": c.idx,
                "quote": c.quote,
                "doc_title": d.title if d else None,
                "doc_source": d.source if d else None,
                "doc_version": d.doc_version if d else None,
            }
        )

    # Enforce grounding (citations required).
    # - In PUBLIC_DEMO_MODE this is always on.
    # - In private mode it is controlled by CITATIONS_REQUIRED (default: true).
    if bool(settings.citations_required) and (not bool(getattr(ans, "refused", False))) and not citations_out:
        refusal_reason = "insufficient_evidence"
        out_no_citations: dict[str, Any] = {
            "question": question,
            "answer": "I don’t have enough evidence in the indexed sources to answer that.",
            "refused": True,
            "refusal_reason": refusal_reason,
            "provider": ans.provider,
            "citations": [],
        }
        if debug:
            out_no_citations["retrieval"] = _retrieval_debug_payload(retrieved, include_text=include_retrieval_text)
        out_no_citations["explain"] = _build_explain_payload(
            question=question,
            top_k=top_k,
            retrieved=retrieved,
            citations_out=[],
            refusal_reason=refusal_reason,
            doc_map=doc_map,
            debug=debug,
        )
        return out_no_citations

    refusal_reason = "answerer_refused" if bool(getattr(ans, "refused", False)) else None

    out: dict[str, Any] = {
        "question": question,
        "answer": ans.text,
        "refused": bool(ans.refused),
        "refusal_reason": refusal_reason,
        "provider": ans.provider,
        "citations": citations_out,
        "explain": _build_explain_payload(
            question=question,
            top_k=top_k,
            retrieved=retrieved,
            citations_out=citations_out,
            refusal_reason=refusal_reason,
            doc_map=doc_map,
            debug=debug,
        ),
    }

    if debug:
        out["retrieval"] = _retrieval_debug_payload(retrieved, include_text=include_retrieval_text)

    return out


@app.post("/api/query/stream")
async def query_stream_api(req: QueryRequest, _auth: Any = Depends(require_role("reader"))) -> StreamingResponse:
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    if len(question) > settings.max_question_chars:
        raise HTTPException(status_code=400, detail=f"Question too long (max {settings.max_question_chars} chars)")

    top_k = max(1, min(int(req.top_k or settings.top_k_default), settings.max_top_k))
    debug = bool(req.debug) and not settings.public_demo_mode
    include_retrieval_text = bool(settings.allow_chunk_view) and not settings.public_demo_mode

    async def _events():
        try:
            safety_start = time.perf_counter()
            with span(
                "safety.prompt_injection_scan",
                attributes={"question_length": len(question), "otel_debug_content": bool(settings.otel_debug_content)},
            ):
                inj = detect_prompt_injection(question)
            record_safety_scan_metric(latency_ms=(time.perf_counter() - safety_start) * 1000.0)
            if inj.is_injection:
                refusal_text = "I can’t help with that request. I can only answer questions using the provided sources."
                refusal_reason = f"prompt_injection:{','.join(inj.reasons)}"
                yield _sse_event("token", {"text": refusal_text})
                yield _sse_event("citations", [])
                yield _sse_event(
                    "done",
                    {
                        "question": question,
                        "answer": refusal_text,
                        "refused": True,
                        "refusal_reason": refusal_reason,
                        "provider": "policy",
                        "explain": _build_explain_payload(
                            question=question,
                            top_k=top_k,
                            retrieved=[],
                            citations_out=[],
                            refusal_reason=refusal_reason,
                            doc_map={},
                            debug=debug,
                        ),
                    },
                )
                return

            retrieval_start = time.perf_counter()
            with span(
                "retrieval.retrieve",
                attributes={"top_k": top_k, "embeddings_backend": settings.embeddings_backend},
            ):
                retrieved = retrieve(question, top_k=top_k)
            record_retrieval_metric(
                latency_ms=(time.perf_counter() - retrieval_start) * 1000.0,
                top_k=top_k,
                backend=settings.embeddings_backend,
            )
            retrieval_out = _retrieval_debug_payload(retrieved, include_text=include_retrieval_text)
            yield _sse_event("retrieval", retrieval_out)
            doc_map = _load_doc_map({r.doc_id for r in retrieved}) if retrieved else {}

            if not retrieved or _is_unrelated_question(question, retrieved):
                refusal_text = "I don’t have enough evidence in the indexed sources to answer that."
                refusal_reason = "insufficient_evidence"
                yield _sse_event("token", {"text": refusal_text})
                yield _sse_event("citations", [])
                yield _sse_event(
                    "done",
                    {
                        "question": question,
                        "answer": refusal_text,
                        "refused": True,
                        "refusal_reason": refusal_reason,
                        "provider": "policy",
                        "explain": _build_explain_payload(
                            question=question,
                            top_k=top_k,
                            retrieved=retrieved,
                            citations_out=[],
                            refusal_reason=refusal_reason,
                            doc_map=doc_map,
                            debug=debug,
                        ),
                    },
                )
                return

            context = [(r.chunk_id, r.doc_id, r.idx, r.text) for r in retrieved]
            answerer = get_answerer()

            provider_name = str(getattr(answerer, "name", settings.effective_llm_provider))
            stream_fn = getattr(answerer, "stream_answer", None)
            if callable(stream_fn):
                stream_citations: list[dict[str, Any]] = []
                for r in retrieved[: min(3, len(retrieved))]:
                    d = doc_map.get(r.doc_id)
                    stream_citations.append(
                        {
                            "chunk_id": r.chunk_id,
                            "doc_id": r.doc_id,
                            "idx": r.idx,
                            "quote": r.text[:300],
                            "doc_title": d.title if d else None,
                            "doc_source": d.source if d else None,
                            "doc_version": d.doc_version if d else None,
                        }
                    )

                streamed_parts: list[str] = []
                generation_start = time.perf_counter()
                with span(
                    "generation.answer",
                    attributes={"provider": provider_name, "context_chunks": len(context), "streaming": True},
                ):
                    for piece in stream_fn(question, context):
                        if not piece:
                            continue
                        token_text = str(piece)
                        if not token_text:
                            continue
                        streamed_parts.append(token_text)
                        yield _sse_event("token", {"text": token_text})
                        await asyncio.sleep(0)
                record_generation_metric(
                    latency_ms=(time.perf_counter() - generation_start) * 1000.0,
                    provider=provider_name,
                    streaming=True,
                )

                answer_text = "".join(streamed_parts).strip()
                refused = False
                refusal_reason: str | None = None

                if not answer_text:
                    refused = True
                    refusal_reason = "insufficient_evidence"
                    answer_text = "I don’t have enough evidence in the indexed sources to answer that."
                    stream_citations = []

                if bool(settings.citations_required) and not refused and not stream_citations:
                    refused = True
                    refusal_reason = "insufficient_evidence"
                    answer_text = "I don’t have enough evidence in the indexed sources to answer that."
                    stream_citations = []

                yield _sse_event("citations", stream_citations)
                yield _sse_event(
                    "done",
                    {
                        "question": question,
                        "answer": answer_text,
                        "refused": refused,
                        "refusal_reason": refusal_reason,
                        "provider": provider_name,
                        "explain": _build_explain_payload(
                            question=question,
                            top_k=top_k,
                            retrieved=retrieved,
                            citations_out=stream_citations,
                            refusal_reason=refusal_reason,
                            doc_map=doc_map,
                            debug=debug,
                        ),
                    },
                )
                return

            generation_start = time.perf_counter()
            with span(
                "generation.answer",
                attributes={
                    "provider": provider_name,
                    "context_chunks": len(context),
                    "streaming": False,
                },
            ):
                ans = answerer.answer(question, context)
            record_generation_metric(
                latency_ms=(time.perf_counter() - generation_start) * 1000.0,
                provider=provider_name,
                streaming=False,
            )

            citations_out: list[dict[str, Any]] = []
            for c in ans.citations or []:
                d = doc_map.get(c.doc_id)
                citations_out.append(
                    {
                        "chunk_id": c.chunk_id,
                        "doc_id": c.doc_id,
                        "idx": c.idx,
                        "quote": c.quote,
                        "doc_title": d.title if d else None,
                        "doc_source": d.source if d else None,
                        "doc_version": d.doc_version if d else None,
                    }
                )

            refused = bool(getattr(ans, "refused", False))
            refusal_reason = "answerer_refused" if refused else None
            answer_text = ans.text
            provider = ans.provider

            if bool(settings.citations_required) and not refused and not citations_out:
                refused = True
                refusal_reason = "insufficient_evidence"
                answer_text = "I don’t have enough evidence in the indexed sources to answer that."

            for token in _stream_text_chunks(answer_text):
                yield _sse_event("token", {"text": token})
                await asyncio.sleep(0)

            yield _sse_event("citations", citations_out)
            yield _sse_event(
                "done",
                {
                    "question": question,
                    "answer": answer_text,
                    "refused": refused,
                    "refusal_reason": refusal_reason,
                    "provider": provider,
                    "explain": _build_explain_payload(
                        question=question,
                        top_k=top_k,
                        retrieved=retrieved,
                        citations_out=citations_out,
                        refusal_reason=refusal_reason,
                        doc_map=doc_map,
                        debug=debug,
                    ),
                },
            )
        except Exception as e:
            yield _sse_event("error", {"message": f"{type(e).__name__}: {e}"})
            refusal_reason = "internal_error"
            yield _sse_event(
                "done",
                {
                    "question": question,
                    "answer": "I don’t have enough evidence in the indexed sources to answer that.",
                    "refused": True,
                    "refusal_reason": refusal_reason,
                    "provider": "policy",
                    "explain": _build_explain_payload(
                        question=question,
                        top_k=top_k,
                        retrieved=[],
                        citations_out=[],
                        refusal_reason=refusal_reason,
                        doc_map={},
                        debug=debug,
                    ),
                },
            )

    return StreamingResponse(
        _events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---- Eval ----
@app.post("/api/eval/run")
def eval_api(req: EvalRequest, request: Request, _auth: AuthContext = Depends(require_role("admin"))) -> dict[str, Any]:
    if settings.public_demo_mode or not settings.allow_eval:
        raise HTTPException(status_code=403, detail="Eval endpoint disabled in this deployment")

    eval_run_id = uuid.uuid4().hex
    res = run_eval(req.golden_path, k=req.k, include_details=req.include_details)

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        _record_audit_event(
            conn,
            auth_ctx=_auth,
            request=request,
            action="eval.run.created",
            target_type="eval_run",
            target_id=eval_run_id,
            metadata={
                "golden_path": req.golden_path,
                "k": int(req.k),
                "include_details": bool(req.include_details),
                "examples": int(res.n),
                "hit_at_k": round(float(res.hit_at_k), 6),
                "mrr": round(float(res.mrr), 6),
            },
        )
        conn.commit()
    return res.to_dict(include_details=req.include_details)


# ---- Frontend (React build served by FastAPI) ----
#
# Local dev flow:
#   - run API with `uv run uvicorn app.main:app --reload --port 8080`
#   - run UI with `pnpm dev` in ./web (Vite proxy handles /api/*)
#
# Production flow:
#   - `pnpm build` emits ./web/dist
#   - the API serves ./web/dist as a SPA

if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")


@app.get("/", response_class=HTMLResponse)
def ui_index() -> Any:
    index = DIST_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return HTMLResponse(
        "<h1>Grounded Knowledge Platform</h1>"
        "<p>Frontend not built yet. See README for <code>pnpm dev</code> or <code>pnpm build</code>.</p>"
    )


@app.get("/{path:path}")
def ui_fallback(path: str) -> Any:
    # Don't mask API/Swagger endpoints.
    if path.startswith(("api", "openapi", "redoc", "health")):
        raise HTTPException(status_code=404)

    # Serve file if it exists at dist root (e.g., favicon.svg).
    #
    # SECURITY: Prevent path traversal (e.g. /../../pyproject.toml).
    root = DIST_DIR
    try:
        candidate = (DIST_DIR / path).resolve()
        candidate.relative_to(root)
    except Exception:
        candidate = None

    if candidate and candidate.exists() and candidate.is_file():
        return FileResponse(str(candidate))

    # SPA fallback
    index = DIST_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    raise HTTPException(status_code=404, detail="Frontend not built")
