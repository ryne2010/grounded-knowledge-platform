# Backlog dependencies

This document describes **dependency relationships** between tasks.

It is intentionally lightweight (no rigid Gantt charts). The goal is to prevent wasted work and avoid refactors.

See also:
- Milestones: `docs/BACKLOG/MILESTONES.md`
- Epics: `docs/BACKLOG/EPICS.md`

---

## Critical path (recommended)

1) **UI grounding UX**
   - `agents/tasks/TASK_UI_UX_POLISH.md`
   - `agents/tasks/TASK_DOC_VIEWER_CITATIONS.md`
   - `agents/tasks/TASK_QUERY_EXPLAIN_DRAWER.md`

2) **Postgres baseline hardening**
   - `agents/tasks/TASK_CLOUDSQL.md`
   - `agents/tasks/TASK_HYBRID_RETRIEVAL_TUNING.md`
   - `agents/tasks/TASK_SEARCH_PERF_PROFILE.md`

3) **Private ops ingestion workflow** (behind auth)
   - `agents/tasks/TASK_AUTH.md` → enables admin-only operations
   - `agents/tasks/TASK_CONNECTORS_GCS_UI.md`
   - `agents/tasks/TASK_INGESTION_RUNS.md`
   - `agents/tasks/TASK_INGESTION_RUNS_UI.md`

4) **Measurable quality + safety**
   - `agents/tasks/TASK_EVAL_PRODUCTIZATION.md`
   - `agents/tasks/TASK_EVAL_CI_SMOKE.md`
   - `agents/tasks/TASK_SAFETY_HARDENING.md`

5) **Ops readiness**
   - `agents/tasks/TASK_OTEL.md`
   - `agents/tasks/TASK_DASHBOARDS_TERRAFORM.md`
   - `agents/tasks/TASK_SLOS_BURN_RATE.md`
   - `agents/tasks/TASK_BACKUP_RESTORE.md`

---

## Task-level dependencies

### UI tasks

- `TASK_DOC_VIEWER_CITATIONS` depends on:
  - stable doc/chunk API contracts (`docs/CONTRACTS.md`)
  - existing doc detail view (baseline)

- `TASK_QUERY_EXPLAIN_DRAWER` depends on:
  - the API returning retrieval metadata in a stable shape (may require small backend changes)

- `TASK_DEMO_GUIDED_TOUR` depends on:
  - stable routes and nav layout from `TASK_UI_UX_POLISH`

### Ingestion tasks

- `TASK_CONNECTORS_GCS_UI` depends on:
  - `TASK_AUTH` (admin-only)
  - connector endpoint already present (`POST /api/connectors/gcs/sync`)

- `TASK_INGESTION_RUNS` should land before:
  - `TASK_INGESTION_RUNS_UI`
  - `TASK_REPLAY_BACKFILL`

- `TASK_PUBSUB_PUSH_INGEST` depends on:
  - connector ingestion baseline + idempotency rules
  - infra plumbing (Pub/Sub topic + push subscription) which depends on Terraform layout

- `TASK_SCHEDULER_PERIODIC_SYNC` depends on:
  - a job/endpoint to invoke
  - auth strategy for the invoker identity

### Governance tasks

- `TASK_RETENTION_ENFORCEMENT` depends on:
  - retention being part of the document model
  - a purge job/CLI (baseline exists, but enforcement rules may evolve)

- `TASK_AUDIT_EVENTS` depends on:
  - auth principal context (`TASK_AUTH`)

### Eval tasks

- `TASK_EVAL_CI_SMOKE` depends on:
  - a deterministic eval runner + dataset format (`TASK_EVAL_PRODUCTIZATION`)

### Ops tasks

- `TASK_SLOS_BURN_RATE` depends on:
  - metrics being exported (via OTEL or native Cloud Run metrics)

- `TASK_SMOKE_TESTS_DEPLOY` depends on:
  - stable `/health` and `/api/meta` contracts

---

## Notes on sequencing

- Prefer landing **schema and API contracts** before heavy UI work.
- Avoid implementing “nice” UI polish on endpoints that are still changing.
- Keep public demo constraints in mind: privileged features should not accidentally leak into demo mode.

