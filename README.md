# Grounded Knowledge Platform

A small, safety-minded, citation-first **RAG** (retrieval augmented generation) reference app.

- **FastAPI** backend + **React (Vite)** frontend
- **SQLite** for doc/chunk storage + embeddings
- optional **Cloud SQL (Postgres)** adapter path for durable persistence
- **Hybrid retrieval** (lexical + vector)
- **Grounding enforced**: answers must be supported by retrieved sources (or the system refuses)
- **Public demo mode**: read-only + extractive answering + rate limiting

This repo is intentionally designed to run well:

- on an **M2 Max MacBook Pro** for development
- on **Cloud Run** for production

---

## Quickstart (M2 Max MacBook Pro)

Full setup notes: `docs/DEV_SETUP_MACOS.md`.

Prereqs:

- Python **3.11+**
- [`uv`](https://github.com/astral-sh/uv)
- Node **20+**
- `pnpm` via Corepack (`corepack enable && corepack prepare pnpm@9.15.0 --activate`)

### 1) Configure env

```bash
cp .env.example .env
```

By default `.env.example` enables `PUBLIC_DEMO_MODE=1` (read-only). For local/private development, disable it and enable uploads:

```bash
# .env
PUBLIC_DEMO_MODE=0
ALLOW_UPLOADS=1
ALLOW_EVAL=1
ALLOW_CHUNK_VIEW=1
ALLOW_DOC_DELETE=1
CITATIONS_REQUIRED=1
BOOTSTRAP_DEMO_CORPUS=1
```

### 2) Install deps

```bash
make py-install
make web-install
```

### 3) Run (two terminals)

Backend:

```bash
make run-api
```

Frontend:

```bash
make run-ui
```

Or run both concurrently:

```bash
make dev
```

Open:

- UI: http://127.0.0.1:5173
- API: http://127.0.0.1:8080

---

## Key concepts

- **Doc**: top-level document record (title, source, metadata)
- **Chunk**: character-based chunking of doc text
- **Embedding**: vector representation per chunk (hash / sentence-transformers / none; sentence-transformers is an optional extra)
- **Ingest event**: lineage record for every ingest (content hash, settings, version)
- **Citation**: chunk quote returned alongside an answer

---

## Safety / deployment modes

### PUBLIC_DEMO_MODE (recommended for public URLs)

`PUBLIC_DEMO_MODE=1` forces:

- no uploads
- no eval endpoints
- **extractive** answering only
- rate limiting on `/api/query`
- citations-required behavior forced on
- chunk viewing disabled

### Private deployment toggles

These are **dangerous** on a public URL, but useful for private/internal deployments:

- `ALLOW_UPLOADS=1` – enables ingestion endpoints (and doc metadata edits)
- `ALLOW_EVAL=1` – enables `/api/eval/run`
- `ALLOW_CHUNK_VIEW=1` – allows full chunk text viewing via `/api/chunks/*`
- `ALLOW_DOC_DELETE=1` – enables `DELETE /api/docs/{doc_id}`

Defense in depth:

- `MAX_UPLOAD_BYTES=10000000` (10MB default)

---

## Ingesting documents

### UI

Use the **Upload file** / **Paste text** cards on the **Ingest** page.

Supported file uploads:

- `.txt`, `.md`
- `.pdf` (optional OCR when `OCR_ENABLED=1`; requires `tesseract` locally)
- `.csv`, `.tsv` (tabular ingestion is rendered into retrieval-friendly text)
- `.xlsx` / `.xlsm` (uses `openpyxl`, included in the default dependency set)

For tabular files, you can optionally attach a YAML `contract_file` to validate required columns/types and record schema drift in ingest lineage.

To ingest docs and inspect ingest lineage across all docs, open the **Ingest** page.

For index/config health, open the **Dashboard** page.

You can attach metadata:

- classification: `public|internal|confidential|restricted`
- retention: `none|30d|90d|1y|indefinite`
- tags: comma-separated
- notes: recorded in ingest lineage

### CLI

```bash
uv run python -m app.cli ingest-folder data/demo_corpus --classification internal --tags "runbook,platform"
```

---

## Cloud Run deployment

This repo ships a production Dockerfile that builds the UI and serves it from the FastAPI container.

High level:

- build container
- deploy to Cloud Run
- set env vars (and secrets)

See:

- `infra/gcp/README.md`
- `Makefile` targets: `make build`, `make deploy`
- Cloud SQL runbook: `docs/RUNBOOKS/CLOUDSQL.md`

---

## Developer workflow

Run the full local quality harness:

```bash
make dev-doctor
```

Or run specific checks:

```bash
make lint
make typecheck
make test
make eval
make safety-eval
```

(See `scripts/harness.py` for what runs.)

Housekeeping:

```bash
make clean   # remove local caches/build artifacts
make dist    # create a clean source ZIP in dist/
```

---

## Maintenance (private deployments)

Retention purge is available for persisted/private deployments:

```bash
make purge-expired         # dry-run
make purge-expired-apply   # delete expired docs
```

The web UI also includes a **Maintenance** page that lists currently-expired docs (read-only).

See `docs/RUNBOOKS/MAINTENANCE.md`.
