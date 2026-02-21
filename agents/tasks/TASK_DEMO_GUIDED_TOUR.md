# Task: Public demo guided tour + suggested queries

Spec: `docs/SPECS/UI_UX_PRODUCTION_POLISH.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/frontend_ux.md`

## Goal

Improve “time to wow” for the **public demo** by adding:

- a **Suggested queries** panel (click-to-run)
- a lightweight **guided tour** (optional, user-triggered) explaining:
  - demo mode constraints (read-only, demo corpus only)
  - how to verify citations
  - why refusals happen

## Constraints

- Must remain **neutral** (no custom brand kit).
- Must not introduce heavy dependencies unless justified.
- Must work in `PUBLIC_DEMO_MODE=1`.

## Requirements

### Suggested queries

- Render a small list of curated demo queries (5–10).
- Clicking a query should populate the input and run it.
- Queries should be stored in a single place (config file) so they’re easy to change.

### Guided tour

- User-triggered (e.g., “Help” or “Tour” button in top bar).
- Step highlights:
  1) demo mode badge
  2) query input
  3) citations list
  4) doc/source viewer
  5) refusal behavior

- Must be keyboard accessible:
  - focus management
  - escape closes
  - next/prev buttons are reachable

### Safety / gating

- Tour must not expose privileged actions.
- If a step points at disabled controls (ingest/connectors), the copy must explain why.

## Deliverables

- UI: suggested queries panel + tour trigger
- Minimal docs update:
  - `docs/PRODUCT/DEMO_SCRIPT.md` (optional) to mention the tour

## Acceptance criteria

- A first-time visitor can reach “citations verified” in < 2 minutes without reading docs.
- Tour can be started and exited without breaking navigation.

## Validation

- `make web-typecheck`
- `python scripts/harness.py lint`
- `python scripts/harness.py test`

