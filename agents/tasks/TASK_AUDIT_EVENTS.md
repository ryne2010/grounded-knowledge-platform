# Task: Audit events (admin action logging)

Related:
- `docs/ARCHITECTURE/SECURITY_MODEL.md`

Spec: `docs/SPECS/GOVERNANCE_METADATA.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/security_governance.md`

## Goal

Add an append-only audit log so security-sensitive operations are traceable:

- connector syncs
- doc deletes
- metadata changes
- eval runs
- auth failures (optional)

## Requirements

- Table: `audit_events`
  - `event_id` (PK)
  - `occurred_at`
  - `principal` (from auth context)
  - `role`
  - `action` (enum-ish string)
  - `target_type` / `target_id` (doc_id, run_id, etc)
  - `metadata_json` (safe, no document content)
  - `request_id` (correlation)

- API:
  - `GET /api/audit-events` (admin only)
  - optional filters: time range, action type

- Write points:
  - when connector sync is triggered
  - when a doc is deleted
  - when metadata is updated
  - when eval runs are created

## Acceptance criteria

- Admin actions are recorded with principal, action, and request_id.
- Audit payloads do not store document content or secrets.

## Validation

- `python scripts/harness.py test`
- `make test-postgres`
