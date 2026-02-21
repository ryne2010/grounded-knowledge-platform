# Milestones

This document slices the epic backlog into **milestones** that can be executed as a sequence of small tasks.

- Canonical epics: `docs/BACKLOG/EPICS.md`
- Task index: `docs/BACKLOG/TASK_INDEX.md`
- Execution queue (generated): `docs/BACKLOG/QUEUE.md`
- Product constraints: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

## Guiding rules

- **Public demo stays safe-by-default** (read-only, extractive-only, demo corpus only).
- **Private deployments** may enable privileged features behind auth.
- Each milestone is “done” when:
  - the UX / behavior is demonstrable end-to-end
  - the harness stays green
  - docs/runbooks are updated

---

## M0 — Baseline (already in repo)

**Outcome:** a deployable Cloud Run + Cloud SQL baseline with safe public demo posture.

**Included**

- Terraform-first deployment (remote state, plan/apply separation)
- Cloud SQL Postgres + pgvector baseline
- Public demo mode: extractive-only, demo corpus only
- Harness + CI + IaC policy gates

**Exit criteria**

- `make dev-doctor` succeeds locally
- `make deploy` succeeds into a fresh GCP project

---

## M1 — Public demo “wow path” polish

**Outcome:** a modern SaaS admin UI that makes grounding obvious (citations, sources, refusal).

**Primary tasks**

- `agents/tasks/TASK_UI_UX_POLISH.md`
- `agents/tasks/TASK_DOC_VIEWER_CITATIONS.md`
- `agents/tasks/TASK_QUERY_EXPLAIN_DRAWER.md`
- `agents/tasks/TASK_DEMO_GUIDED_TOUR.md` *(new)*
- `agents/tasks/TASK_ACCESSIBILITY_AUDIT.md` *(new)*

**Exit criteria**

- A first-time visitor can:
  - ask a question
  - click a citation
  - verify the supporting snippet
  - understand a refusal without confusion
- Demo-mode affordances are visually clear (“read-only”, “demo corpus only”)

---

## M2 — Private deployment operator workflows

**Outcome:** private deployments feel operationally real: auth, ingestion runs, connector UI, lineage breadcrumbs.

**Primary tasks**

- `agents/tasks/TASK_AUTH.md`
- `agents/tasks/TASK_CONNECTORS_GCS_UI.md`
- `agents/tasks/TASK_INGESTION_RUNS.md`
- `agents/tasks/TASK_INGESTION_RUNS_UI.md`
- `agents/tasks/TASK_REPLAY_BACKFILL.md`
- `agents/tasks/TASK_DATA_CONTRACTS.md`
- `agents/tasks/TASK_PUBSUB_PUSH_INGEST.md` *(new)*
- `agents/tasks/TASK_SCHEDULER_PERIODIC_SYNC.md` *(new)*

**Exit criteria**

- Operator can run a GCS sync and see a persisted run summary.
- Rerunning sync is idempotent (no duplicates).
- Public demo remains unaffected (connectors disabled).

---

## M3 — Governance, safety, and measurable quality

**Outcome:** the system is “governable” and regressions are detectable.

**Primary tasks**

- `agents/tasks/TASK_GOVERNANCE_METADATA_UI.md`
- `agents/tasks/TASK_RETENTION_ENFORCEMENT.md`
- `agents/tasks/TASK_AUDIT_EVENTS.md`
- `agents/tasks/TASK_SAFETY_HARDENING.md`
- `agents/tasks/TASK_EVAL_PRODUCTIZATION.md`
- `agents/tasks/TASK_EVAL_CI_SMOKE.md`
- `agents/tasks/TASK_EVAL_DATASET_AUTHORING.md`

**Exit criteria**

- Governance metadata is visible and enforceable in private deployments.
- CI catches obvious retrieval/safety regressions.

---

## M4 — Ops readiness

**Outcome:** a “platform owner” can operate the system with dashboards, SLOs, and runbooks.

**Primary tasks**

- `agents/tasks/TASK_OTEL.md`
- `agents/tasks/TASK_DASHBOARDS_TERRAFORM.md`
- `agents/tasks/TASK_SLOS_BURN_RATE.md`
- `agents/tasks/TASK_COST_GUARDRAILS.md`
- `agents/tasks/TASK_SMOKE_TESTS_DEPLOY.md`
- `agents/tasks/TASK_BACKUP_RESTORE.md`
- `agents/tasks/TASK_RELEASE_PROCESS.md`
- `agents/tasks/TASK_DEPENDABOT_CODE_SCANNING.md` *(new)*
- `agents/tasks/TASK_CONTAINER_IMAGE_SCANNING.md` *(new)*

**Exit criteria**

- A new project has dashboards + alerts after `terraform apply`.
- Operator runbooks cover: deploy, rollback, backup/restore, incident checklist.

---

## M5 — Data platform integration

**Outcome:** integrate with a governed analytics lifecycle (BigQuery) to match “data platform” narratives.

**Primary tasks**

- `agents/tasks/TASK_BIGQUERY_EXPORT.md`
- `agents/tasks/TASK_BIGQUERY_MODELS.md`

**Exit criteria**

- Export tables exist and can be queried for ops/eval analytics.
- Documentation includes a simple raw→curated→marts story for the exported datasets.

---

## Optional milestones (only if desired)

### MO1 — Offline/PWA experience

- `agents/tasks/TASK_PWA.md`

### MO2 — Streaming answers

- `agents/tasks/TASK_STREAMING.md`

