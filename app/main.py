from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.responses import JSONResponse
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .bootstrap import bootstrap_demo_corpus
from .answering import get_answerer
from .config import settings
from .eval import run_eval
from .ingestion import ingest_file, ingest_text
from .ratelimit import SlidingWindowRateLimiter
from .retrieval import invalidate_cache, retrieve
from .storage import connect, init_db, list_docs
from .observability import Timer, configure_logging, log_http_request, parse_cloud_trace_context, request_id_from_headers


APP_DIR = Path(__file__).resolve().parent
WEB_DIR = (APP_DIR.parent / "web").resolve()
DIST_DIR = (WEB_DIR / "dist").resolve()

app = FastAPI(title="Grounded Knowledge Platform", version="0.1.0")

# Configure JSON logging early so Cloud Run/Cloud Logging parses fields.
configure_logging()

_limiter = SlidingWindowRateLimiter(window_s=settings.rate_limit_window_s, max_requests=settings.rate_limit_max_requests)


@app.on_event("startup")
def _startup() -> None:
    # Ensure DB schema exists and (optionally) bootstrap a demo corpus.
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
    bootstrap_demo_corpus()


@app.middleware("http")
async def _request_middleware(request: Request, call_next):
    """Attach a request ID, enforce demo safety controls, and emit structured logs."""

    timer = Timer()
    rid = request_id_from_headers({k.lower(): v for k, v in request.headers.items()})
    request.state.request_id = rid

    # Prefer X-Forwarded-For in managed environments (Cloud Run).
    xff = request.headers.get("x-forwarded-for")
    remote_ip = (xff.split(",")[0].strip() if xff else None) or (request.client.host if request.client else "unknown")
    user_agent = request.headers.get("user-agent", "")

    # Cloud Trace correlation (if present).
    trace_id, span_id = parse_cloud_trace_context({k.lower(): v for k, v in request.headers.items()})

    # ---- Demo safety controls (defense-in-depth) ----
    if settings.public_demo_mode and settings.rate_limit_enabled and request.url.path == "/api/query":
        if not _limiter.allow(remote_ip):
            # Return explicitly so we can log and attach request ID.
            latency_ms = timer.ms()
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
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}, headers={"X-Request-Id": rid})

    # ---- Normal request execution ----
    try:
        response = await call_next(request)
    except HTTPException as he:
        # Log and re-raise so FastAPI builds the response.
        latency_ms = timer.ms()
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
    latency_ms = timer.ms()
    log_http_request(
        request_id=rid,
        method=request.method,
        url=str(request.url),
        path=request.url.path,
        status=int(response.status_code),
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
    """Ensure error responses include X-Request-Id for correlation."""

    rid = getattr(request.state, "request_id", None)
    headers = {"X-Request-Id": rid} if rid else None
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    """Return a safe JSON 500 (and keep request correlation)."""

    rid = getattr(request.state, "request_id", None)
    headers = {"X-Request-Id": rid} if rid else None
    # Don't leak internal exception details in a public demo.
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"}, headers=headers)


# Frontend (React) is served from web/dist when present.
# In dev, run `pnpm dev` in ./web and the Vite dev server will proxy API calls.


# ---- API models ----
class IngestTextRequest(BaseModel):
    title: str = Field(..., description="Document title")
    source: str = Field(..., description="A source label/URL/path")
    text: str = Field(..., description="Document content")
    doc_id: str | None = Field(None, description="Optional stable id")


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    debug: bool = False


class EvalRequest(BaseModel):
    golden_path: str = "data/eval/golden.jsonl"
    k: int = 5


# ---- Health ----
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/meta")
def meta() -> dict[str, object]:
    """Small metadata endpoint for the UI and diagnostics."""
    return {
        "public_demo_mode": settings.public_demo_mode,
        "uploads_enabled": bool(settings.allow_uploads and not settings.public_demo_mode),
        "eval_enabled": bool(settings.allow_eval and not settings.public_demo_mode),
        "llm_provider": settings.effective_llm_provider,
        "embeddings_backend": settings.embeddings_backend,
        "ocr_enabled": settings.ocr_enabled,
    }


# ---- Docs ----
@app.get("/api/docs")
def docs() -> dict[str, Any]:
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        items = list_docs(conn)
    return {"docs": [item.__dict__ for item in items]}


# ---- Ingest ----
@app.post("/api/ingest/text")
def ingest_text_api(req: IngestTextRequest) -> dict[str, Any]:
    if not settings.allow_uploads or settings.public_demo_mode:
        raise HTTPException(status_code=403, detail="Uploads are disabled in this deployment")
    res = ingest_text(title=req.title, source=req.source, text=req.text, doc_id=req.doc_id)
    invalidate_cache()
    return {"doc_id": res.doc_id, "num_chunks": res.num_chunks, "embedding_dim": res.embedding_dim}


@app.post("/api/ingest/file")
async def ingest_file_api(file: UploadFile = File(...)) -> dict[str, Any]:
    if not settings.allow_uploads or settings.public_demo_mode:
        raise HTTPException(status_code=403, detail="Uploads are disabled in this deployment")
    suffix = Path(file.filename or "upload.txt").suffix.lower()
    if suffix not in {".txt", ".md", ".pdf"}:
        raise HTTPException(status_code=400, detail="Only .txt, .md, .pdf supported")

    tmp_dir = Path("/tmp/gkp_uploads")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / (file.filename or "upload.txt")

    data = await file.read()
    tmp_path.write_bytes(data)

    res = ingest_file(tmp_path)
    invalidate_cache()
    return {"doc_id": res.doc_id, "num_chunks": res.num_chunks, "embedding_dim": res.embedding_dim}


# ---- Query ----
@app.post("/api/query")
def query_api(req: QueryRequest) -> dict[str, Any]:
    if len(req.question) > settings.max_question_chars:
        raise HTTPException(status_code=400, detail=f"Question too long (max {settings.max_question_chars} chars)")

    # Clamp knobs for public demos.
    top_k = max(1, min(int(req.top_k or settings.top_k_default), settings.max_top_k))
    debug = bool(req.debug) and not settings.public_demo_mode

    retrieved = retrieve(req.question, top_k=top_k)
    context = [(r.chunk_id, r.doc_id, r.idx, r.text) for r in retrieved]
    answerer = get_answerer()
    ans = answerer.answer(req.question, context)

    out: dict[str, Any] = {
        "question": req.question,
        "answer": ans.text,
        "refused": ans.refused,
        "provider": ans.provider,
        "citations": [c.__dict__ for c in ans.citations],
    }

    if debug:
        out["retrieval"] = [
            {
                "chunk_id": r.chunk_id,
                "doc_id": r.doc_id,
                "idx": r.idx,
                "score": r.score,
                "lexical_score": r.lexical_score,
                "vector_score": r.vector_score,
                "text_preview": r.text[:240],
            }
            for r in retrieved
        ]

    return out


# ---- Eval ----
@app.post("/api/eval/run")
def eval_api(req: EvalRequest) -> dict[str, Any]:
    if not settings.allow_eval or settings.public_demo_mode:
        raise HTTPException(status_code=403, detail="Eval endpoint disabled in this deployment")
    res = run_eval(req.golden_path, k=req.k)
    return {"examples": res.n, "hit_at_k": res.hit_at_k, "mrr": res.mrr}


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
    if path.startswith(("api", "docs", "openapi", "redoc", "health")):
        raise HTTPException(status_code=404)

    # Serve file if it exists at dist root (e.g., favicon.svg).
    candidate = DIST_DIR / path
    if candidate.exists() and candidate.is_file():
        return FileResponse(str(candidate))

    # SPA fallback
    index = DIST_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    raise HTTPException(status_code=404, detail="Frontend not built")
