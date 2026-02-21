# Task: Multi-tenancy boundary (optional)

Owner: @codex
Suggested sub-agent: `agents/subagents/security_governance.md`

> Note: The default deployment model for this repo is **one GCP project per client**.
> Multi-tenancy is **not required** for the primary roadmap. Keep this task for a future "host multiple clients/workspaces in one deployment" scenario.
## Objective

Add a **workspace (tenant) boundary** so that multiple corpora can be isolated inside one deployment.

This aligns the app with real client/internal use where multiple corpora must be isolated.

## Scope (if you ever need it)

- **Prereq:** complete `agents/tasks/TASK_AUTH.md` first (single-deployment auth + RBAC).

- Data model changes:
  - add `tenant_id` to docs/chunks/ingest_events
  - update indexes for tenant-scoped retrieval
- API changes:
  - tenant selection (header or path-based)
  - role enforcement per tenant
- UI changes:
  - tenant switcher
  - tenant-scoped views
- Audit log events for security-sensitive actions

## Non-goals

- No external identity provider integration (OIDC) in this task
- No billing/quotas (out of scope)

## Acceptance criteria

- It is impossible to retrieve docs/chunks from another tenant through the API
- Roles are enforced:
  - reader: query + read metadata
  - editor: ingest + metadata edits
  - admin: deletes + retention actions
- Tests cover cross-tenant isolation

## Migration notes

- Provide a one-time migration for existing SQLite DBs:
  - default `tenant_id = "default"`
- For CloudSQL/Postgres path, add a migration script in `app/migrations/postgres/`

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
