# Task: Replay/backfill tooling (safe reprocessing)

Related:
- `docs/ARCHITECTURE/INGESTION_PIPELINE.md`
- `docs/ARCHITECTURE/DATA_MODEL.md` (ingestion_runs planned)

Owner: @codex  
Suggested sub-agent: `agents/subagents/backend_fastapi_platform.md`

## Goal

Provide safe replay/backfill mechanisms typical of production data platforms:

- re-run ingestion for a doc or ingestion run
- ensure idempotency (no duplicates)
- support “forward-only” migration changes safely

## Requirements

- CLI commands:
  - `app.cli replay-doc --doc-id <id> [--force]`
  - `app.cli replay-run --run-id <id> [--force]`

- Behavior:
  - default: skip unchanged content (hash-based)
  - `--force`: re-chunk/re-embed even if unchanged

- Safety:
  - public demo: commands exist but demo is read-only; do not expose replay endpoints unauthenticated
  - private: if exposing via API, admin-only

- Docs/runbook:
  - `docs/RUNBOOKS/REPLAY_BACKFILL.md` (new)

## Acceptance criteria

- Replaying an ingestion run is idempotent (no duplicate docs/chunks).
- `--force` causes reprocessing even when content hashes are unchanged.
- No replay endpoints are exposed in public demo mode.

## Validation

- `python scripts/harness.py test`
- `make test-postgres`
