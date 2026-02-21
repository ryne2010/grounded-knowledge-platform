# Contracts

This document defines the stable external contracts for the Grounded Knowledge Platform:

- environment variables
- API endpoints
- response shapes

---

## Environment variables

### Mode and safety

- `PUBLIC_DEMO_MODE=1`
  - Forces **read-only** mode (no uploads/eval/chunk view/delete)
  - Forces `AUTH_MODE=none` (anonymous)
  - Forces **extractive** answering (no external LLM calls)
  - Enables rate limiting by default

- `APP_VERSION=...` (optional)
  - Overrides the reported app version (otherwise derived from `pyproject.toml`)

### Authentication / authorization (optional)

- `AUTH_MODE=none|api_key|oidc` (default: `none`)
  - `none`: anonymous requests (existing behavior)
  - `api_key`: require `X-API-Key` on non-health endpoints
  - `oidc`: reserved for Cloud Run/IAP JWT validation (not implemented in this build)

- API key inputs (when `AUTH_MODE=api_key`):
  - `API_KEYS_JSON` (preferred): JSON map of key -> role
    - Example: `{"reader-key":"reader","editor-key":"editor","admin-key":"admin"}`
  - `API_KEYS` (fallback): comma-separated keys, optional role suffix
    - Example: `reader-key:reader,admin-key:admin`
  - `API_KEY` (fallback): single key (defaults to `admin`)

Roles:
- `reader`: read/query endpoints
- `editor`: ingest endpoints
- `admin`: delete/chunk-view/eval endpoints

- `RATE_LIMIT_ENABLED=1`
  - Default: enabled in `PUBLIC_DEMO_MODE=1`, disabled otherwise
  - When enabled, the limiter applies to `/api/query` by default (see `RATE_LIMIT_SCOPE`).
- `RATE_LIMIT_SCOPE=query|api` (default: `query`)
- `RATE_LIMIT_WINDOW_S` (default: `60`)
- `RATE_LIMIT_MAX_REQUESTS` (default: `30`)

### Grounding

- `CITATIONS_REQUIRED=1` (default: `1`)
  - If enabled, the API will **refuse** any non-refusal answer that does not include citations.
  - In `PUBLIC_DEMO_MODE=1`, this is forced on.

### Feature gates

These should be **off for public URLs**.

- `ALLOW_UPLOADS=1`
  - Also enables doc metadata edits via `PATCH /api/docs/{doc_id}`
- `ALLOW_EVAL=1`
- `ALLOW_CHUNK_VIEW=1`
- `ALLOW_DOC_DELETE=1`

### Storage

- `SQLITE_PATH`
  - Default in private mode: `data/index.sqlite`
  - Default in public demo mode: `/tmp/index.sqlite`

> Cloud Run note: the filesystem is ephemeral. For persistence, migrate to Cloud SQL or a managed store.

### Retrieval

- `TOP_K_DEFAULT` (default: `5`)
- `MAX_TOP_K` (default: `8`)
- `MAX_QUESTION_CHARS` (default: `2000`)

### Upload hardening

- `MAX_UPLOAD_BYTES` (default: `10_000_000`)
- `MAX_QUERY_PAYLOAD_BYTES` (default: `32_768`)

### Embeddings

- `EMBEDDINGS_BACKEND=hash|sentence-transformers|none`
- `EMBEDDINGS_MODEL` (only for `sentence-transformers`)
- `EMBEDDING_DIM` (only for `hash`)
- `HASH_EMBEDDER_VERSION` (default: `1`)

> Dependency note: `sentence-transformers` is an optional extra. Install with `uv sync --extra embeddings`.

### LLM providers

- `LLM_PROVIDER=extractive|openai|gemini|ollama`

> Dependency note: OpenAI/Gemini client libraries are optional extras. Install with `uv sync --extra providers`.

Provider-specific:

- OpenAI:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL` (default: `gpt-4.1-mini`)

- Gemini:
  - `GEMINI_API_KEY`
  - `GEMINI_MODEL` (default: `gemini-2.0-flash`)

- Ollama:
  - `OLLAMA_BASE_URL` (default: `http://localhost:11434`)
  - `OLLAMA_MODEL` (default: `llama3.1:8b`)

### Optional OCR

OCR is disabled by default. Enable only for private deployments.

- `OCR_ENABLED=1`
- `OCR_MAX_PAGES` (default: `10`)
- `OCR_DPI` (default: `200`)
- `OCR_LANG` (default: `eng`)

### Observability

- `LOG_LEVEL=INFO|DEBUG|WARNING|ERROR` (default: `INFO`)
- `OTEL_ENABLED=0|1` (default: `0`)
- `OTEL_TRACES_EXPORTER=auto|none|otlp|gcp_trace` (default: `auto`)
- `OTEL_EXPORTER_OTLP_ENDPOINT` (optional)
- `OTEL_SERVICE_NAME` (default: `grounded-knowledge-platform`)
- `OTEL_DEBUG_CONTENT=0|1` (default: `0`)

---

## API endpoints

### Health

- `GET /health` → `{ "status": "ok" }`
- `GET /ready` → `{ "ready": true, "version": string, "public_demo_mode": bool }`

### Meta

- `GET /api/meta`

Returns feature flags and deployment configuration for the UI.

Shape (stable keys):

- `public_demo_mode: bool`
- `auth_mode: string`
- `database_backend: string`
- `version: string`
- `uploads_enabled: bool`
- `metadata_edit_enabled: bool`
- `eval_enabled: bool`
- `chunk_view_enabled: bool`
- `doc_delete_enabled: bool`
- `citations_required: bool`
- `rate_limit_enabled: bool`
- `rate_limit_scope: string`
- `rate_limit_window_s: number`
- `rate_limit_max_requests: number`
- `api_docs_url: string`
- `max_upload_bytes: number`
- `max_query_payload_bytes: number`
- `llm_provider: string`
- `embeddings_backend: string`
- `ocr_enabled: bool`
- `max_question_chars: number`
- `stats: { docs: number, chunks: number, embeddings: number }`
- `index_signature: Record<string,string|null>`
- `doc_classifications: string[]`
- `doc_retentions: string[]`

### Stats

- `GET /api/stats`

Returns aggregated index statistics for dashboards and diagnostics.

Shape (stable keys):

- `docs: number`
- `chunks: number`
- `embeddings: number`
- `ingest_events: number`
- `by_classification: Record<string, number>`
- `by_retention: Record<string, number>`
- `top_tags: { tag: string, count: number }[]`

### Docs

- `GET /api/docs` → `{ docs: Doc[] }`
- `GET /api/docs/{doc_id}` → `{ doc: Doc, ingest_events: IngestEvent[] }`

`IngestEvent` includes (in addition to lineage fields):
- `schema_fingerprint?: string`
- `contract_sha256?: string`
- `validation_status?: "pass" | "warn" | "fail"`
- `validation_errors?: string[]`
- `schema_drifted?: boolean`
- `run_id?: string`

Doc metadata update (requires `ALLOW_UPLOADS=1` and not demo mode):

- `PATCH /api/docs/{doc_id}` → `{ doc: Doc }`
  - body: any of `{ title?, source?, classification?, retention?, tags? }`

Global ingest/audit view:

- `GET /api/ingest/events?limit=100&doc_id=<optional>` → `{ events: IngestEventView[] }`

Ingestion run history:

- `GET /api/ingestion-runs?limit=100` → `{ runs: IngestionRunSummary[] }`
- `GET /api/ingestion-runs/{run_id}` → `{ run: IngestionRunSummary, events: IngestEventView[] }`

Audit events (admin-only):

- `GET /api/audit-events?limit=100&action=<optional>&since=<optional unix_ts>&until=<optional unix_ts>`
  - returns `{ events: AuditEvent[] }`
  - `AuditEvent` shape:
    - `event_id: string`
    - `occurred_at: number`
    - `principal: string`
    - `role: string`
    - `action: string`
    - `target_type: string`
    - `target_id: string | null`
    - `metadata: Record<string, unknown>` (sanitized; no document content/secrets)
    - `request_id: string | null`

Chunk browsing (requires `ALLOW_CHUNK_VIEW=1` and not demo mode):

- `GET /api/docs/{doc_id}/chunks?limit=200&offset=0`
- `GET /api/chunks/{chunk_id}`

Doc export (requires `ALLOW_CHUNK_VIEW=1` and not demo mode):

- `GET /api/docs/{doc_id}/text` → (text/plain)

Doc delete (requires `ALLOW_DOC_DELETE=1` and not demo mode):

- `DELETE /api/docs/{doc_id}` → `{ deleted: true, doc_id }`

### Ingest

Uploads are disabled in demo mode.

- `POST /api/ingest/text`

Request (JSON):

- `title`, `source`, `text`
- optional: `doc_id`, `classification`, `retention`, `tags`, `notes`

- `POST /api/ingest/file`

Request (multipart form):

- required: `file` (.txt/.md/.pdf/.csv/.tsv/.xlsx)
  - Note: `.xlsx/.xlsm` ingestion uses `openpyxl` (included in the default dependency set).
- optional: `contract_file` (YAML, max 64KB; tabular files only)
- optional: `title`, `source`, `classification`, `retention`, `tags`, `notes`

Response:

- `{ doc_id, doc_version, changed, num_chunks, embedding_dim, content_sha256 }`

### Connectors (private only)

- `POST /api/connectors/gcs/sync` (requires `ALLOW_CONNECTORS=1`, admin role, and not demo mode)
- `POST /api/connectors/gcs/notify` (Pub/Sub push envelope; requires `ALLOW_CONNECTORS=1`, admin role, and not demo mode)

`/api/connectors/gcs/notify` is intentionally hidden when disabled:
- returns `404` in `PUBLIC_DEMO_MODE=1`
- returns `404` when `ALLOW_CONNECTORS!=1`

Request (JSON):

- `bucket` (required)
- optional: `prefix`, `max_objects`, `dry_run`, `classification`, `retention`, `tags`, `notes`

Response includes:

- run metadata (`run_id`, `started_at`, `finished_at`)
- sync summary (`scanned`, `skipped_unsupported`, `ingested`, `changed`)
- optional `errors`
- `results[]` per processed object/doc

Pub/Sub notify response includes:
- `accepted: true`
- `run_id: string | null`
- `pubsub_message_id: string`
- `gcs_uri: string`
- `result: "changed" | "unchanged" | "skipped_unsupported" | "ignored_event"`

### Query

- `POST /api/query`
- `POST /api/query/stream` (SSE)

Request:

- `question: string`
- `top_k?: number`
- `debug?: boolean` (ignored in demo mode)

Response (stable):

- `question: string`
- `answer: string`
- `refused: boolean`
- `refusal_reason: string | null`
  - canonical values in this build: `insufficient_evidence | safety_block | internal_error | null`
- `provider: string`
- `citations: Citation[]`
- optional: `retrieval: RetrievalDebug[]` (debug-only)

Auth note:
- when `AUTH_MODE=api_key`, requests must include `X-API-Key: <key>`

Streaming event schema (`/api/query/stream`):

- `retrieval`: `RetrievalDebug[]`
- `token`: `{ text: string }`
- `citations`: `Citation[]`
- `done`: `{ question, answer, refused, refusal_reason, provider }`
- `error`: `{ message: string }`

`RetrievalDebug` shape:

- `chunk_id: string`
- `doc_id: string`
- `idx: number`
- `score: number`
- `lexical_score: number`
- `vector_score: number`
- `text_preview: string`
- optional: `text: string`
  - included only when **chunk viewing is enabled** (`ALLOW_CHUNK_VIEW=1`) and not in demo mode

### Eval

- All eval endpoints require `ALLOW_EVAL=1`, `PUBLIC_DEMO_MODE=0`, and `admin` role.

- `POST /api/eval/run`
  - runs evaluation and persists a run record.
  - Request:
    - `golden_path: string`
    - `k: number`
    - `include_details?: boolean` (default: `false`)
  - Response (stable keys):
    - `run_id: string`
    - `examples: number`
    - `passed: number`
    - `failed: number`
    - `pass_rate: number`
    - `hit_at_k: number`
    - `mrr: number`
    - `status: string`
    - `dataset_name: string`
    - `dataset_sha256: string`
    - `k: number`
    - `include_details: boolean`
    - `app_version: string`
    - `embeddings_backend: string`
    - `embeddings_model: string`
    - `retrieval_config: object` (includes `k` and `hybrid_weights`)
    - `provider_config: object` (provider/model)
    - `diff_from_prev: object`
    - optional `details: EvalExample[]` when `include_details=true`

- `GET /api/eval/runs?limit=50`
  - returns `{ runs: EvalRunSummary[] }` ordered by newest-first.

- `GET /api/eval/runs/{run_id}`
  - returns `{ run: EvalRunSummary, details: EvalExample[] }`.

### Maintenance

These endpoints are **read-only** helpers intended for operators.
Retention delete/sweep operations are CLI-only (`app.cli retention-sweep`) and are not exposed as API writes.

- `GET /api/maintenance/retention/expired?now=<optional unix_ts>`

Returns docs whose retention policy has expired.

Shape (stable keys):

- `now: number`
- `expired: { doc_id: string, title: string, retention: string, updated_at: number }[]`

---

## Error semantics

- `400` invalid input
- `403` gated endpoint (demo mode / feature disabled)
- `404` missing doc/chunk
- `413` upload too large
- `429` rate limit exceeded
- `500` unexpected server error

All responses include `X-Request-Id` for correlation.
