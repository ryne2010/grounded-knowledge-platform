# Task: Governance metadata UI (classification/retention/tags)

Related:
- `docs/PRODUCT/FEATURE_MATRIX.md`
- `docs/ARCHITECTURE/SECURITY_MODEL.md`

Spec: `docs/SPECS/GOVERNANCE_METADATA.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/frontend_ux.md`

## Goal

Make governance metadata a first-class UX concept:

- classification (`public|internal|confidential|restricted`)
- retention (`none|30d|90d|1y|indefinite`)
- tags (normalized list)

## Requirements

- Doc Detail page:
  - read-only display for all users
  - edit mode only when:
    - `ALLOW_UPLOADS=1` (or a dedicated `ALLOW_METADATA_EDIT=1`)
    - role is editor/admin
    - demo mode is off

- Validation:
  - only allow canonical values
  - tags normalized (lowercase, trimmed, deduped)

- UX:
  - edits are explicit (“Edit metadata” button)
  - save shows a toast + updates updated_at
  - errors are actionable

## Acceptance criteria

- In public demo: metadata is visible but not editable.
- In private: an editor can update metadata and it is persisted.

## Validation

- `make web-typecheck`
- `python scripts/harness.py test`
