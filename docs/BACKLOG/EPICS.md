# Epics

This is the canonical epic-level backlog for the repo.

- Product intent: `docs/PRODUCT/PRODUCT_BRIEF.md`
- Architecture maps: `docs/ARCHITECTURE/`
- Roadmap sequencing: `docs/ROADMAP.md`

Safety constraints: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

---

## Epic index

| Epic | Theme | Public demo impact | Private deployment impact |
|---|---|---|---|
| E1 | UI/UX polish (modern SaaS admin, neutral) | High | High |
| E2 | Postgres/Cloud SQL hardening (pgvector + FTS baseline) | Medium | High |
| E3 | Ingestion platform (connectors, ingestion runs, lineage) | Low (disabled) | High |
| E4 | Governance + auditability (metadata, retention, audit events) | Medium (read-only) | High |
| E5 | Retrieval experience (citations UX, explainability, streaming) | High | High |
| E6 | Evaluation and safety regression | Medium (read-only) | High |
| E7 | Ops + deployment ergonomics (Terraform, runbooks, dashboards) | Medium | High |
| E8 | Warehouse/export integration (BigQuery) | Low | Medium |

---

## E1 — UI/UX polish (modern SaaS admin, neutral)

**Why:** a portfolio project should feel like a production app: clear navigation, crisp empty states, and evidence-first UX.

Specs:
- `docs/SPECS/UI_UX_PRODUCTION_POLISH.md`
- `docs/PRODUCT/PERSONAS_AND_JOURNEYS.md`

Tasks:
- `../../agents/tasks/TASK_UI_UX_POLISH.md`
- `../../agents/tasks/TASK_DOC_VIEWER_CITATIONS.md` (new)
- `../../agents/tasks/TASK_QUERY_EXPLAIN_DRAWER.md` (new)
- `../../agents/tasks/TASK_DEMO_GUIDED_TOUR.md` (new)
- `../../agents/tasks/TASK_ACCESSIBILITY_AUDIT.md` (new)
- `../../agents/tasks/TASK_STREAMING.md`
- `../../agents/tasks/TASK_PWA.md`

---

## E2 — Cloud SQL / Postgres hardening (pgvector baseline)

**Why:** production deployments should be Cloud SQL Postgres-first, with scalable retrieval.

Specs:
- `docs/SPECS/CLOUDSQL_HARDENING.md`
- `docs/ARCHITECTURE/DATA_MODEL.md`

Tasks:
- `../../agents/tasks/TASK_CLOUDSQL.md`
- `../../agents/tasks/TASK_HYBRID_RETRIEVAL_TUNING.md` (new)
- `../../agents/tasks/TASK_SEARCH_PERF_PROFILE.md` (new)

---

## E3 — Ingestion platform (connectors, ingestion runs, lineage)

**Why:** private deployments should support repeatable ingestion patterns (file feeds, cloud storage sync, replay/backfill).

Specs:
- `docs/SPECS/CONNECTOR_GCS_INGESTION.md`
- `docs/ARCHITECTURE/INGESTION_PIPELINE.md`

Tasks:
- `../../agents/tasks/TASK_CONNECTORS_GCS.md`
- `../../agents/tasks/TASK_CONNECTORS_GCS_UI.md` (new)
- `../../agents/tasks/TASK_INGESTION_RUNS.md` (new)
- `../../agents/tasks/TASK_INGESTION_RUNS_UI.md` (new)
- `../../agents/tasks/TASK_REPLAY_BACKFILL.md` (new)
- `../../agents/tasks/TASK_DATA_CONTRACTS.md`
- `../../agents/tasks/TASK_PUBSUB_PUSH_INGEST.md` (new)
- `../../agents/tasks/TASK_SCHEDULER_PERIODIC_SYNC.md` (new)

Note: ingestion/connectors are disabled in the public demo posture.

---

## E4 — Governance + auditability (metadata, retention, audit events)

**Why:** “production” knowledge systems need metadata and auditability boundaries, even in small form.

Specs:
- `docs/ARCHITECTURE/SECURITY_MODEL.md`
- `docs/PRODUCT/FEATURE_MATRIX.md`
- `docs/SPECS/GOVERNANCE_METADATA.md`

Tasks:
- `../../agents/tasks/TASK_GOVERNANCE_METADATA_UI.md` (new)
- `../../agents/tasks/TASK_RETENTION_ENFORCEMENT.md` (new)
- `../../agents/tasks/TASK_AUDIT_EVENTS.md` (new)
- `../../agents/tasks/TASK_AUTH.md`

---

## E5 — Retrieval experience (citations UX, explainability, streaming)

**Why:** “grounded” systems win when the evidence is easy to verify.

Specs:
- `docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md`
- `docs/SPECS/UI_UX_PRODUCTION_POLISH.md`

Tasks:
- `../../agents/tasks/TASK_DOC_VIEWER_CITATIONS.md`
- `../../agents/tasks/TASK_QUERY_EXPLAIN_DRAWER.md`
- `../../agents/tasks/TASK_STREAMING.md`
- `../../agents/tasks/TASK_SAFETY_HARDENING.md` (new)

---

## E6 — Evaluation and safety regression

**Why:** measurable quality is a differentiator; regressions should be catchable in CI.

Specs:
- `docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`

Tasks:
- `../../agents/tasks/TASK_EVAL_PRODUCTIZATION.md`
- `../../agents/tasks/TASK_EVAL_CI_SMOKE.md` (new)
- `../../agents/tasks/TASK_EVAL_DATASET_AUTHORING.md` (new)

---

## E7 — Ops + deployment ergonomics (Terraform, runbooks, dashboards)

**Why:** production readiness includes runbooks, repeatable deploys, and incident-friendly telemetry.

Specs:
- `docs/SPECS/OBSERVABILITY_OPS.md`

Tasks:
- `../../agents/tasks/TASK_OTEL.md`
- `../../agents/tasks/TASK_DASHBOARDS_TERRAFORM.md` (new)
- `../../agents/tasks/TASK_SLOS_BURN_RATE.md` (new)
- `../../agents/tasks/TASK_COST_GUARDRAILS.md` (new)
- `../../agents/tasks/TASK_SMOKE_TESTS_DEPLOY.md` (new)
- `../../agents/tasks/TASK_RELEASE_PROCESS.md` (new)
- `../../agents/tasks/TASK_BACKUP_RESTORE.md` (new)
- `../../agents/tasks/TASK_DEPENDABOT_CODE_SCANNING.md` (new)
- `../../agents/tasks/TASK_CONTAINER_IMAGE_SCANNING.md` (new)

---

## E8 — Warehouse/export integration (BigQuery)

**Why:** connect the knowledge system to a governed data platform lifecycle.

Specs:
- `docs/SPECS/BIGQUERY_EXPORT.md`

Tasks:
- `../../agents/tasks/TASK_BIGQUERY_EXPORT.md`
- `../../agents/tasks/TASK_BIGQUERY_MODELS.md` (new)

