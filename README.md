# Grounded Knowledge Platform (RAG) — citations-first, eval-driven

## Quickstart (team workflow)

Run a prerequisite/config check (recommended first step):

```bash
make doctor
```

For a team-friendly GCP demo deploy (one-time setup, then deploy):

```bash
make init GCLOUD_CONFIG=personal-portfolio PROJECT_ID=YOUR_PROJECT_ID REGION=us-central1
make auth    # only needed once per machine/user
make deploy
```

- Local dev: `make` is optional — see the README sections below for `uv`/`pnpm` commands.
- GCP demo deploy (safe defaults): `make deploy`

A small, production-minded reference implementation of a **grounded knowledge system**.

**Design goals**
- **Grounded answers:** every claim should be backed by retrieved sources.
- **Citations by default:** answers are returned with clickable citations.
- **Refusal mode:** if evidence is weak, the system returns *"I don't have enough information in the provided sources"*.
- **Eval-driven:** track retrieval quality over time with a tiny regression harness.
- **Deployable:** single FastAPI service that can run locally or on Cloud Run.

> This repo ships with a small **safe demo corpus** you can replace with your own documents.

---


## UI stack

- **Vite + React**
- **TanStack**: Router, Query, Table, **Virtual**, **Pacer**, **Ranger**
- **Tailwind + shadcn-style components** (vendored in `web/src/portfolio-ui` and intended to be kept in sync via git subtree)

## Quick start (local)

This repo uses:
- **uv** for Python dependency management
- **pnpm** for the React UI (`web/`)

### 1) Install Python deps

```bash
uv sync --dev
```

### 2) Run the API

```bash
uv run uvicorn app.main:app --reload --port 8080
```

Open: http://localhost:8080

### 3) Run the UI (React + TanStack)

In a second terminal:

```bash
cd web
corepack enable
pnpm install
pnpm dev
```

Open: http://localhost:5173

### 4) Ingest demo docs (optional)

The repo includes a small demo corpus in `data/demo_corpus/`.

If you're running in **PUBLIC_DEMO_MODE=1**, the server will automatically bootstrap the demo corpus on startup.

If you want to ingest manually (local/dev):

```bash
uv run python -m app.cli ingest-folder data/demo_corpus
```

### 5) Ask questions

Use the web UI or:

```bash
curl -s http://localhost:8080/api/query \
  -H 'content-type: application/json' \
  -d '{"question":"What is this project?","top_k":5}' | jq
```

---

## Public demo mode (safe, read-only)

To run a **public-facing** demo safely:

```bash
PUBLIC_DEMO_MODE=1 uv run uvicorn app.main:app --port 8080
```

When enabled, the service:
- disables uploads and eval endpoints
- forces **extractive-only** answering (no external API calls)
- enables basic in-app rate limiting + clamps query knobs
- emits structured JSON request logs (request_id, status, latency) and returns `X-Request-Id`

## LLM providers (optional)

By default, the system uses a **local extractive answerer** (no API keys required). You can optionally enable an LLM:

### OpenAI

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=... 
export OPENAI_MODEL=gpt-4.1-mini # example
```

### Gemini (Google GenAI SDK)

```bash
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=...
export GEMINI_MODEL=gemini-2.0-flash # example
```

If no provider is configured, the API falls back to extractive answers that still include citations.

### Ollama (local open models)

For sensitive/on-prem use cases, you can run an open model locally via **Ollama**.

1) Install Ollama and pull a model:

```bash
ollama pull llama3.1:8b
```

2) Run the app with:

```bash
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=llama3.1:8b
export OLLAMA_BASE_URL=http://localhost:11434
```

If Ollama is not reachable, the service gracefully falls back to the local extractive answerer.

---

## Embeddings backends

Default is `hash` (no downloads). You can also disable embeddings entirely (`none`) for a minimal footprint.

For better retrieval quality, enable `sentence-transformers`:

```bash
export EMBEDDINGS_BACKEND=sentence-transformers
export EMBEDDINGS_MODEL=all-MiniLM-L6-v2
```

> For sensitive data cases, prefer **local embeddings** (e.g., `sentence-transformers`) and a **local LLM** (Ollama) so that document content never leaves your environment.

---

## OCR (optional, open source, fully local)

For scanned PDFs, enable OCR:

```bash
export OCR_ENABLED=1
export OCR_MAX_PAGES=10
export OCR_DPI=200
```

OCR uses **Tesseract** via `pytesseract` and stays fully local.

## Evaluation (retrieval quality)

Edit `data/eval/golden.jsonl` and run:

```bash
uv run python -m app.cli eval data/eval/golden.jsonl --k 5
```

Outputs hit@k and MRR.

---

## Deploy (Docker)

```bash
docker build -t grounded-kp -f docker/Dockerfile .
docker run -p 8080:8080 grounded-kp
```

## Deploy to GCP Cloud Run (team-ready, IaC-first)

Cloud Run can scale to zero and has a generous free tier. You can typically keep a personal demo at or near $0/month,
but you should still set budgets/alerts.

This repo includes a **staff-level Makefile workflow** that:
- uses **remote Terraform state** (GCS)
- builds images via **Cloud Build** (consistent, macOS-friendly)
- deploys Cloud Run with **safe demo defaults** (`PUBLIC_DEMO_MODE=1`)
- supports **plan/apply separation**

### One-time: set gcloud defaults

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-central1
```

### Deploy (one command)

```bash
make deploy
```

### Plan/apply separation

```bash
make plan
make apply
```

See:
- `docs/DEPLOY_GCP.md`
- `docs/TEAM_WORKFLOW.md`


### Safety checklist

Before exposing a public URL, review:
- `docs/public-demo-checklist.md`

---

## Repo layout

- `app/` FastAPI service, ingestion, retrieval, eval harness
- `web/` static single-page UI served by FastAPI
- `data/` demo corpus and evaluation set
- `docs/` public demo checklist
- `infra/` Terraform examples (Cloud Run)

---

## License

MIT
