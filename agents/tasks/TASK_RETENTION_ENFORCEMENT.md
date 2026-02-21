# Task: Retention enforcement (hide/expire content)

Related:
- `docs/ARCHITECTURE/SECURITY_MODEL.md`
- `docs/PRODUCT/FEATURE_MATRIX.md`

Spec: `docs/SPECS/GOVERNANCE_METADATA.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/backend_fastapi_platform.md`

## Goal

Make retention policy meaningful:

- expired documents are not retrievable
- operator has a clear way to enforce/cleanup in private deployments

## Requirements

- Data model:
  - add `retention_until` (timestamp) to `docs` OR derive deterministically from `retention` + `created_at`

- Retrieval enforcement:
  - retrieval queries must filter out expired docs/chunks

- Operator tooling:
  - CLI command: `app.cli retention-sweep` that:
    - lists expired docs
    - optionally deletes them (admin-only path)

- Safety:
  - public demo: retention sweeps not runnable via API
  - private: destructive actions require admin

## Acceptance criteria

- A doc marked `30d` is not retrievable after expiration.
- Sweep produces a clear summary (what would be deleted).

## Validation

- `python scripts/harness.py test`
- `make test-postgres`
