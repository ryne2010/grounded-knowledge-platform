# Design

This project is a small but production-minded **RAG** reference implementation.

---

## Architecture

### Backend (FastAPI)

Key modules:

- `app/main.py`: HTTP API + static SPA hosting
- `app/storage.py`: SQLite schema + persistence helpers
- `app/ingestion.py`: text extraction + chunking + embedding + lineage
- `app/retrieval.py`: hybrid retrieval (lexical + vector)
- `app/answering.py`: answer provider selection (extractive/OpenAI/Gemini/etc)
- `app/safety.py`: prompt injection heuristics
- `app/observability.py`: structured logging + request IDs + trace correlation

Data plane:

- SQLite stores docs/chunks/embeddings/ingest events (plus lightweight `meta` key/value state like the "index signature")
- Retrieval loads corpus into an in-process cache (per worker)

### Frontend (React + Vite)

- `web/src/api.ts`: typed API client
- `web/src/pages/Home.tsx`: ask/answer, upload, citations
- `web/src/pages/Docs.tsx`: document browser
- `web/src/pages/DocDetail.tsx`: doc metadata + ingest events + chunks (when enabled)
- `web/src/pages/Eval.tsx`: eval runner (when enabled)

---

## Threat model and defenses

### Prompt injection

Threat: user tries to override system rules (“ignore instructions”, “reveal hidden prompt”, etc.)

Defenses:

- detect likely injection patterns (`app/safety.py`)
- refuse early with a stable refusal contract
- enforce evidence: if the answer contains no citations (in demo mode), refuse

### Data exfiltration (internal deployments)

Threat: if chunk viewing is enabled, the UI could be used to exfiltrate large sections of private data.

Defenses:

- `ALLOW_CHUNK_VIEW=0` by default
- chunk endpoints are disabled in `PUBLIC_DEMO_MODE`
- debug retrieval omits full chunk text unless chunk viewing is enabled

### Upload hardening

Threat: memory exhaustion or path tricks via file upload.

Defenses:

- stream uploads to disk with a strict size cap (`MAX_UPLOAD_BYTES`)
- sanitize filenames
- restrict file types

### Rate limiting

Threat: abuse of `/api/query` on public deployments.

Defense:

- sliding-window in-memory rate limiter (good enough for single-instance demo)

---

## Deployment

### Local development (M2 Max MacBook Pro)

- `uv` for Python dependency management
- `pnpm` for the frontend
- run API + UI separately for fast iteration

### Production (Cloud Run)

- container builds the web bundle and serves it via FastAPI
- Cloud Run provides ingress + autoscaling
- SQLite is stored on the container filesystem

Important note:

- Cloud Run filesystem is **ephemeral**. For long-lived production knowledge bases, swap SQLite for a persistent store (Cloud SQL, AlloyDB, etc.) and/or move blobs to Cloud Storage.

---

## Non-goals (currently)

- multi-tenant authn/authz
- distributed embeddings / vector DB
- background ingestion pipelines
- PII redaction

Those can be added in future iterations once the core grounded behavior is stable.
