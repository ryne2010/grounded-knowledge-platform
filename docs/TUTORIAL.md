# Tutorial

This is a practical walkthrough for the “next iteration” of the platform.

---

## Local dev on an M2 Max MacBook Pro

### Install prerequisites

- Python 3.11+
- `uv`
- Node 20+
- `pnpm`

Optional:

- `tesseract` (only needed for OCR on scanned PDFs)

### Setup

```bash
cp .env.example .env
```

Suggested local/private settings:

```bash
PUBLIC_DEMO_MODE=0
ALLOW_UPLOADS=1
ALLOW_EVAL=1
ALLOW_CHUNK_VIEW=1
ALLOW_DOC_DELETE=1

# Grounding: refuse answers without citations
CITATIONS_REQUIRED=1
```

Install deps:

```bash
make py-install
make web-install
```

Run API + UI:

```bash
make run-api
make run-ui
```

Or:

```bash
make dev
```

Housekeeping:

```bash
make clean   # remove caches / build artifacts
make dist    # create a clean source ZIP in dist/
```

---

## Ingest your first doc

### UI

1. Open **Ingest**
2. Either:
   - Upload a `.md`, `.txt`, `.pdf`, `.csv`, `.tsv`, `.xlsx`, or `.xlsm`, **or**
   - Use **Paste text** for quick notes/runbooks

> Note: For **scanned** PDFs, enable OCR via `OCR_ENABLED=1` and install `tesseract` locally.
3. Add tags + a classification
4. Verify it appears under **Docs** (and try **Search** to find matching chunks)
5. Open **Dashboard** to confirm the doc/chunk counters moved as expected

### CLI

```bash
uv run python -m app.cli ingest-folder ./my_docs --classification internal --tags "runbook,platform"
```

---

## Inspect ingest lineage

The platform records an immutable ingest lineage event on every ingest.

- Per-doc lineage: open a doc from **Docs**.
- Global audit feed: open **Ingest** (shows recent ingest events across all docs).

This is how you debug drift:

- “Which settings were used when this doc was ingested?”
- “When did the content hash change?”

Tip: the UI shows both the current content SHA and (when available) the previous content SHA per ingest event.

---

## Edit doc metadata (private deployments)

If `ALLOW_UPLOADS=1` (and `PUBLIC_DEMO_MODE=0`), you can edit doc metadata without re-ingesting:

1. Open a doc from **Docs**
2. Click **Edit metadata**
3. Update title/source/classification/retention/tags

This is useful for fixing typos, normalizing tags, or correcting retention/classification.

---

## Validate grounding and safety

Try questions that should be:

- **answerable** from the docs
- **unanswerable** (should refuse)
- **prompt-injection attempts** (should refuse)

In non-demo deployments, enable **Debug retrieval** on the home page.

- Ask a question
- Open **Retrieval** on the answer card to inspect the hybrid retrieval set (BM25 + embeddings)
- Cited rows are highlighted
- Full chunk text is only included when chunk viewing is enabled (`ALLOW_CHUNK_VIEW=1`)

You can also run the built-in evaluation suites:

```bash
# Retrieval quality (hit@k, MRR)
make eval

# Prompt-injection regression
make safety-eval
```

Tip: the **Eval** UI page can also show per-example hit/miss details and the retrieved top-k list.

---

## Retention purge (private deployments)

If you persist storage (or migrate off SQLite), you can auto-purge documents whose
retention policy has expired.

Dry-run:

```bash
make purge-expired
```

UI visibility:

- Open **Maintenance** → **Retention** to see which docs are currently expired.

Apply deletes:

```bash
make purge-expired-apply
```

---

## Cloud Run production

### Recommended production defaults

For any public or customer-facing URL:

```bash
PUBLIC_DEMO_MODE=1
ALLOW_UPLOADS=0
ALLOW_EVAL=0
ALLOW_CHUNK_VIEW=0
ALLOW_DOC_DELETE=0
CITATIONS_REQUIRED=1
RATE_LIMIT_ENABLED=1
RATE_LIMIT_SCOPE=query
```

### Deploy

See `infra/gcp/README.md` and the `Makefile` targets:

- `make doctor`
- `make deploy`

Operational endpoints:

- `/health` is a lightweight liveness check.
- `/ready` runs a minimal SQLite open/query check and returns 503 if initialization fails.

---

## Extending the system

### Add a new answer provider

1. Create a provider in `app/llm/*_provider.py`
2. Update `app/answering.py` to select it
3. Ensure the provider returns citations (or `refused=True`)
4. Add a regression test for refusal/grounding behavior

### Improve retrieval

Common upgrades:

- tune chunk size/overlap
- adjust hybrid weighting
- add document-level metadata filtering (tags/classification)

### Make storage production-grade

SQLite on Cloud Run is ephemeral.

To make the platform durable:

- move docs/chunks/embeddings to Cloud SQL (Postgres)
- use a managed vector DB if needed
- store raw documents in Cloud Storage
- add authn/authz (IAP, OIDC, or your own)
