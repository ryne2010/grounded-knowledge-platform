# Task: Ingestion runs UI (history + detail)

Depends on: `agents/tasks/TASK_INGESTION_RUNS.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/frontend_ux.md`

## Goal

Add UI surfaces for operators to inspect ingestion runs:

- list view (recent runs, status, trigger type, started/finished)
- detail view (summary counts, errors, linked ingest events)
- “rerun” affordance (future) with clear safety labeling

## Requirements

### Safety / gating

- Public demo:
  - page can exist, but shows empty state (“no runs in demo mode”)
  - no actions available

- Private deployments:
  - visible to readers (optional), actions restricted to admin
  - error payloads must not leak raw document content

### UX

- table list with filters (status, trigger type, date)
- detail page with:
  - summary tiles (changed, unchanged, errors)
  - expandable error details

## Acceptance criteria

- In public demo mode, the page renders a clear empty state and exposes no operator actions.
- In private deployments, operators can view run history and inspect errors without leaking raw content.
- List/detail views remain usable on mobile widths.

## Validation

- `make web-typecheck`
