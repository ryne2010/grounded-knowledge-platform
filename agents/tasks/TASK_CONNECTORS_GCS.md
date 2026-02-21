# Task: Connector Ingestion — GCS (Sync Endpoint + Roadmap)

Spec: `docs/SPECS/CONNECTOR_GCS_INGESTION.md`
Owner: @codex
Suggested sub-agent: `agents/subagents/connector_gcs.md`


## Objective

Support **cloud-native, replayable ingestion** for private deployments:

- Batch ingest from a GCS prefix via a sync endpoint
- Safe-by-default gating (disabled in public demo)
- Idempotency + lineage

## Current baseline (implemented)

- Backend module: `app/connectors/gcs.py`
  - lists objects via the Cloud Storage JSON API
  - downloads objects and runs `ingest_file(...)`
  - uses metadata server token on Cloud Run; `GCP_ACCESS_TOKEN` for local dev
- API endpoint:
  - `POST /api/connectors/gcs/sync` (admin role)
  - gated by `ALLOW_CONNECTORS=1` and disabled in `PUBLIC_DEMO_MODE`

Deletion policy:

- Sync is **add/update only**.
- No tombstoning/deletes are performed.

## Scope (remaining)

- CLI support
  - `grounded-kp ingest-gcs --bucket ... --prefix ... [--dry-run] [--max N]`
- Provenance improvements
  - dedicated metadata column/table (instead of embedding JSON in notes)
  - connector run history/audit table
- Event-driven ingestion (optional)
  - Pub/Sub notifications + push endpoint
  - Tracked separately: `agents/tasks/TASK_PUBSUB_PUSH_INGEST.md`
- Incremental sync
  - `since` filtering and/or generation-based checkpoints

## Acceptance criteria

- Sync endpoint is safe on a private deployment:
  - cannot be enabled accidentally in public demo mode
  - requires admin role
  - respects max_objects bounds
- Sync can be rerun and correctly reports `changed=false` for unchanged content

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
- `make gcs-sync GCS_BUCKET=... GCS_PREFIX=... GCS_DRY_RUN=true` (private deployments only)
