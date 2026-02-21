# Spec: Governance metadata (classification, retention, tags) + auditability

## Context

Knowledge platforms become more trustworthy and operationally safe when content is governed:

- classification labels (public/internal/confidential)
- retention intent (ephemeral/indefinite/etc.)
- tags for organization and filtering
- audit events for admin actions

The public demo posture is intentionally constrained and read-only, but private deployments should be able to manage governance metadata behind auth.

## Goals

- Define a minimal metadata model that is:
  - easy to explain
  - enforceable at ingest
  - visible in the UI
- Add retention enforcement hooks for private deployments.
- Add audit events for sensitive actions.

## Non-goals

- Full legal retention workflows
- Per-document ACLs
- Multi-tenant policy rules (one deployment per client)

## Proposed design

### User experience

- Public demo:
  - metadata visible (read-only)
  - no editing

- Private deployments:
  - admin/editor can edit metadata
  - admin-only actions create audit events

### API surface

- `PATCH /api/docs/{id}/metadata` (editor/admin)
- `GET /api/audit` (admin)

### Data model

Documents store:

- `classification` (enum)
- `retention` (enum/string)
- `tags` (array)

Audit events table stores:

- `id`, `timestamp`, `actor`, `action`, `target_type`, `target_id`, `details_json`

### Security / privacy

- Metadata update endpoints are disabled in `PUBLIC_DEMO_MODE`.
- Audit log endpoints are admin-only.

### Observability

- Metadata updates and deletes log structured events.

### Rollout / migration

- Add DB migrations for audit table and any missing metadata fields.
- Add UI editing only when auth is enabled.

## Alternatives considered

- External policy engine: heavy for portfolio baseline.

## Acceptance criteria

- Private deployment can edit metadata and see changes reflected in doc views.
- Retention enforcement can be enabled and tested.
- Audit events are created for sensitive actions (delete, connector sync, metadata edits).

## Validation plan

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
