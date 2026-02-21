# Task: Ingestion runs (grouping + status + summaries)

Related:
- `docs/ARCHITECTURE/DATA_MODEL.md` (planned tables)
- `docs/ARCHITECTURE/INGESTION_PIPELINE.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/backend_fastapi_platform.md`

## Goal

Introduce an `ingestion_runs` concept so connector operations and batch ingests are:

- observable (status, errors)
- replayable (rerun by id)
- auditable (who triggered it)
- easy to summarize (counts, bytes, changed docs)

This is a “real platform” capability: not just individual ingest events.

## Requirements

### Data model

Add table `ingestion_runs`:

- `run_id` (PK)
- `started_at`, `finished_at`
- `status`: `running|succeeded|failed|cancelled`
- `trigger_type`: `ui|cli|connector`
- `trigger_payload_json` (bucket/prefix, etc)
- `principal` (if auth enabled)
- summary fields:
  - `objects_scanned`
  - `docs_changed`
  - `docs_unchanged`
  - `bytes_processed`
  - `errors_json`

Add table `ingestion_run_events` (or add `run_id` to `ingest_events`):
- links run → ingest_events

### API

- `GET /api/ingestion-runs` (list)
- `GET /api/ingestion-runs/{run_id}` (detail)
- connector endpoint should create + update a run record

### Safety / gating

- public demo: read-only visibility (no create via demo, but list empty is fine)
- private: creating runs requires admin/editor depending on trigger

## Acceptance criteria

- Triggering a GCS sync creates an ingestion run with a summary.
- A failed run retains actionable errors.
- Re-running the same sync is idempotent (no duplicates).

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py test`
- `make test-postgres`
