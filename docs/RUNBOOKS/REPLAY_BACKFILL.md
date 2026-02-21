# Runbook: Replay / Backfill

## Scope

This runbook covers safe replay/backfill operations in **private deployments**.

- CLI entrypoint: `uv run python -m app.cli ...`
- Commands:
  - `replay-doc --doc-id <id> [--force]`
  - `replay-run --run-id <id> [--force]`

Replay tooling is intentionally blocked in `PUBLIC_DEMO_MODE=1`.

## Safety posture

- Public demo remains read-only:
  - replay commands exit with an error
  - no replay API endpoints are exposed
- Replay defaults to **skip unchanged** content when a content hash exists.
- `--force` is explicit and reprocesses content even when unchanged.
- Replay run records are written to `ingestion_runs` with `trigger_type=cli`.

## Preconditions

- Private deployment configuration:
  - `PUBLIC_DEMO_MODE=0`
  - valid local DB configuration (`SQLITE_PATH` or `DATABASE_URL`)
- For API-key-protected deployments, this runbook is still CLI-only and runs in the trusted operator environment.

## Common workflows

### Replay one document (safe default)

```bash
uv run python -m app.cli replay-doc --doc-id <DOC_ID>
```

Expected outcome:

- unchanged docs are skipped by default
- no duplicate docs/chunks are created

### Force replay one document

```bash
uv run python -m app.cli replay-doc --doc-id <DOC_ID> --force
```

Expected outcome:

- document is re-chunked/re-embedded even if content hash is unchanged
- run is recorded in `ingestion_runs`

### Replay a prior ingestion run (safe default)

```bash
uv run python -m app.cli replay-run --run-id <RUN_ID>
```

Expected outcome:

- docs linked to `<RUN_ID>` are replayed with skip-if-unchanged behavior
- operation is idempotent at doc/chunk level

### Force replay a prior ingestion run

```bash
uv run python -m app.cli replay-run --run-id <RUN_ID> --force
```

Expected outcome:

- linked docs are reprocessed regardless of unchanged content hashes

## Validation and troubleshooting

### Check run summaries

Use the ingestion runs UI/API:

- `GET /api/ingestion-runs`
- `GET /api/ingestion-runs/{run_id}`

Look for:

- `status`
- `docs_changed` / `docs_unchanged`
- `errors`
- `event_count`

### Typical failure modes

1. `Replay/backfill commands are disabled in PUBLIC_DEMO_MODE`
   - Cause: deployment is in demo-safe read-only mode.
   - Fix: run replay only in private deployments (`PUBLIC_DEMO_MODE=0`).

2. `Doc not found` / `Ingestion run not found`
   - Cause: wrong identifier or missing lineage rows.
   - Fix: verify IDs from `/api/docs` and `/api/ingestion-runs`.

3. Replay run finishes with `status=failed`
   - Cause: one or more docs failed reprocessing.
   - Fix: inspect `errors` in the replay run detail and replay docs individually for isolation.
