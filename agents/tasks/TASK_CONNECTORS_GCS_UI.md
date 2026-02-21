# Task: GCS sync UI (admin-only, private deployments)

Spec: `docs/SPECS/CONNECTOR_GCS_INGESTION.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/frontend_ux.md` + `agents/subagents/connector_gcs.md`

## Goal

Provide a polished admin UI to trigger and monitor the GCS connector sync endpoint:

- form inputs for bucket/prefix/max_objects/dry_run
- clear progress + results summary
- safe gating (disabled in demo mode)

## Requirements

### Safety / gating

- If `PUBLIC_DEMO_MODE=1`: UI shows the connector section as disabled with explanation.
- If `ALLOW_CONNECTORS=0`: UI shows disabled state.
- Connector actions require admin role when auth is enabled.

### UX

- Inputs:
  - bucket (required)
  - prefix (optional)
  - max_objects (bounded)
  - dry_run toggle
  - optional tags/classification/retention (private deployments only)

- Results:
  - count objects scanned
  - count docs changed / unchanged
  - errors list (actionable)

### API integration

- Call `POST /api/connectors/gcs/sync`
- Render response and store in UI state for later copy/export

## Acceptance criteria

- An operator can run a dry run and understand what would change.
- A real run produces a clear summary and actionable errors.
- No connector action is possible in the public demo.

## Validation

- `python scripts/harness.py lint`
- `make web-typecheck`
