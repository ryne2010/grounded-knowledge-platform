# Execution queue

This is the canonical, ordered execution queue derived from `docs/BACKLOG/MILESTONES.md`.

Regenerate:

```bash
make queue
```

Guardrails:
- Non-negotiables: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
- Execution playbook: `docs/BACKLOG/CODEX_PLAYBOOK.md`

## M1 — Public demo “wow path” polish

| # | Task | Owner | Suggested sub-agent | Prompt pack |
|---:|---|---|---|---|
| 1 | [`TASK_UI_UX_POLISH.md`](../../agents/tasks/TASK_UI_UX_POLISH.md)<br/>Task: UI/UX Production Polish (Modern SaaS Admin)<br/>Spec: [`docs/SPECS/UI_UX_PRODUCTION_POLISH.md`](../../docs/SPECS/UI_UX_PRODUCTION_POLISH.md) | @codex | `agents/subagents/frontend_ux.md` | `make codex-prompt TASK=agents/tasks/TASK_UI_UX_POLISH.md` |
| 2 | [`TASK_DOC_VIEWER_CITATIONS.md`](../../agents/tasks/TASK_DOC_VIEWER_CITATIONS.md)<br/>Task: Doc viewer + citations UX (production feel)<br/>Spec: [`docs/SPECS/UI_UX_PRODUCTION_POLISH.md`](../../docs/SPECS/UI_UX_PRODUCTION_POLISH.md) | @codex | `agents/subagents/frontend_ux.md` | `make codex-prompt TASK=agents/tasks/TASK_DOC_VIEWER_CITATIONS.md` |
| 3 | [`TASK_QUERY_EXPLAIN_DRAWER.md`](../../agents/tasks/TASK_QUERY_EXPLAIN_DRAWER.md)<br/>Task: “Explain this answer” drawer (retrieval transparency)<br/>Spec: [`docs/SPECS/UI_UX_PRODUCTION_POLISH.md`](../../docs/SPECS/UI_UX_PRODUCTION_POLISH.md) | @codex | `agents/subagents/frontend_ux.md` | `make codex-prompt TASK=agents/tasks/TASK_QUERY_EXPLAIN_DRAWER.md` |
| 4 | [`TASK_DEMO_GUIDED_TOUR.md`](../../agents/tasks/TASK_DEMO_GUIDED_TOUR.md)<br/>Task: Public demo guided tour + suggested queries<br/>Spec: [`docs/SPECS/UI_UX_PRODUCTION_POLISH.md`](../../docs/SPECS/UI_UX_PRODUCTION_POLISH.md) | @codex | `agents/subagents/frontend_ux.md` | `make codex-prompt TASK=agents/tasks/TASK_DEMO_GUIDED_TOUR.md` |
| 5 | [`TASK_ACCESSIBILITY_AUDIT.md`](../../agents/tasks/TASK_ACCESSIBILITY_AUDIT.md)<br/>Task: Accessibility audit + fixes (UI)<br/>Spec: [`docs/SPECS/UI_UX_PRODUCTION_POLISH.md`](../../docs/SPECS/UI_UX_PRODUCTION_POLISH.md) | @codex | `agents/subagents/frontend_ux.md` | `make codex-prompt TASK=agents/tasks/TASK_ACCESSIBILITY_AUDIT.md` |

## M2 — Private deployment operator workflows

| # | Task | Owner | Suggested sub-agent | Prompt pack |
|---:|---|---|---|---|
| 6 | [`TASK_AUTH.md`](../../agents/tasks/TASK_AUTH.md)<br/>Task: Add authn/authz for private deployments<br/>Spec: [`docs/SPECS/AUTH_PRIVATE_DEPLOYMENTS.md`](../../docs/SPECS/AUTH_PRIVATE_DEPLOYMENTS.md) | @codex | `agents/subagents/backend_fastapi_platform.md` | `make codex-prompt TASK=agents/tasks/TASK_AUTH.md` |
| 7 | [`TASK_CONNECTORS_GCS_UI.md`](../../agents/tasks/TASK_CONNECTORS_GCS_UI.md)<br/>Task: GCS sync UI (admin-only, private deployments)<br/>Spec: [`docs/SPECS/CONNECTOR_GCS_INGESTION.md`](../../docs/SPECS/CONNECTOR_GCS_INGESTION.md) | @codex | `agents/subagents/frontend_ux.md` | `make codex-prompt TASK=agents/tasks/TASK_CONNECTORS_GCS_UI.md` |
| 8 | [`TASK_INGESTION_RUNS.md`](../../agents/tasks/TASK_INGESTION_RUNS.md)<br/>Task: Ingestion runs (grouping + status + summaries) | @codex | `agents/subagents/backend_fastapi_platform.md` | `make codex-prompt TASK=agents/tasks/TASK_INGESTION_RUNS.md` |
| 9 | [`TASK_INGESTION_RUNS_UI.md`](../../agents/tasks/TASK_INGESTION_RUNS_UI.md)<br/>Task: Ingestion runs UI (history + detail) | @codex | `agents/subagents/frontend_ux.md` | `make codex-prompt TASK=agents/tasks/TASK_INGESTION_RUNS_UI.md` |
| 10 | [`TASK_REPLAY_BACKFILL.md`](../../agents/tasks/TASK_REPLAY_BACKFILL.md)<br/>Task: Replay/backfill tooling (safe reprocessing) | @codex | `agents/subagents/backend_fastapi_platform.md` | `make codex-prompt TASK=agents/tasks/TASK_REPLAY_BACKFILL.md` |
| 11 | [`TASK_DATA_CONTRACTS.md`](../../agents/tasks/TASK_DATA_CONTRACTS.md)<br/>Task: Data contracts + schema drift for tabular ingests<br/>Spec: [`docs/DATA_CONTRACTS.md`](../../docs/DATA_CONTRACTS.md) | @codex | `agents/subagents/security_governance.md` | `make codex-prompt TASK=agents/tasks/TASK_DATA_CONTRACTS.md` |
| 12 | [`TASK_PUBSUB_PUSH_INGEST.md`](../../agents/tasks/TASK_PUBSUB_PUSH_INGEST.md)<br/>Task: Pub/Sub push ingestion (Cloud Storage notifications)<br/>Spec: [`docs/SPECS/PUBSUB_EVENT_INGESTION.md`](../../docs/SPECS/PUBSUB_EVENT_INGESTION.md) | @codex | `agents/subagents/backend_fastapi_platform.md` | `make codex-prompt TASK=agents/tasks/TASK_PUBSUB_PUSH_INGEST.md` |
| 13 | [`TASK_SCHEDULER_PERIODIC_SYNC.md`](../../agents/tasks/TASK_SCHEDULER_PERIODIC_SYNC.md)<br/>Task: Periodic GCS sync via Cloud Scheduler<br/>Spec: [`docs/SPECS/SCHEDULER_PERIODIC_SYNC.md`](../../docs/SPECS/SCHEDULER_PERIODIC_SYNC.md) | @codex | `agents/subagents/infra_terraform_gcp.md` | `make codex-prompt TASK=agents/tasks/TASK_SCHEDULER_PERIODIC_SYNC.md` |

## M3 — Governance, safety, and measurable quality

| # | Task | Owner | Suggested sub-agent | Prompt pack |
|---:|---|---|---|---|
| 14 | [`TASK_GOVERNANCE_METADATA_UI.md`](../../agents/tasks/TASK_GOVERNANCE_METADATA_UI.md)<br/>Task: Governance metadata UI (classification/retention/tags)<br/>Spec: [`docs/SPECS/GOVERNANCE_METADATA.md`](../../docs/SPECS/GOVERNANCE_METADATA.md) | @codex | `agents/subagents/frontend_ux.md` | `make codex-prompt TASK=agents/tasks/TASK_GOVERNANCE_METADATA_UI.md` |
| 15 | [`TASK_RETENTION_ENFORCEMENT.md`](../../agents/tasks/TASK_RETENTION_ENFORCEMENT.md)<br/>Task: Retention enforcement (hide/expire content)<br/>Spec: [`docs/SPECS/GOVERNANCE_METADATA.md`](../../docs/SPECS/GOVERNANCE_METADATA.md) | @codex | `agents/subagents/backend_fastapi_platform.md` | `make codex-prompt TASK=agents/tasks/TASK_RETENTION_ENFORCEMENT.md` |
| 16 | [`TASK_AUDIT_EVENTS.md`](../../agents/tasks/TASK_AUDIT_EVENTS.md)<br/>Task: Audit events (admin action logging)<br/>Spec: [`docs/SPECS/GOVERNANCE_METADATA.md`](../../docs/SPECS/GOVERNANCE_METADATA.md) | @codex | `agents/subagents/security_governance.md` | `make codex-prompt TASK=agents/tasks/TASK_AUDIT_EVENTS.md` |
| 17 | [`TASK_SAFETY_HARDENING.md`](../../agents/tasks/TASK_SAFETY_HARDENING.md)<br/>Task: Safety hardening (prompt injection + exfiltration) | @codex | `agents/subagents/security_governance.md` | `make codex-prompt TASK=agents/tasks/TASK_SAFETY_HARDENING.md` |
| 18 | [`TASK_EVAL_PRODUCTIZATION.md`](../../agents/tasks/TASK_EVAL_PRODUCTIZATION.md)<br/>Task: Evaluation Productization<br/>Spec: [`docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`](../../docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md) | @codex | `agents/subagents/eval_harness.md` | `make codex-prompt TASK=agents/tasks/TASK_EVAL_PRODUCTIZATION.md` |
| 19 | [`TASK_EVAL_CI_SMOKE.md`](../../agents/tasks/TASK_EVAL_CI_SMOKE.md)<br/>Task: CI smoke eval gate<br/>Spec: [`docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`](../../docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md) | @codex | `agents/subagents/eval_harness.md` | `make codex-prompt TASK=agents/tasks/TASK_EVAL_CI_SMOKE.md` |
| 20 | [`TASK_EVAL_DATASET_AUTHORING.md`](../../agents/tasks/TASK_EVAL_DATASET_AUTHORING.md)<br/>Task: Eval dataset authoring guide + tooling<br/>Spec: [`docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`](../../docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md) | @codex | `agents/subagents/eval_harness.md` | `make codex-prompt TASK=agents/tasks/TASK_EVAL_DATASET_AUTHORING.md` |

## M4 — Ops readiness

| # | Task | Owner | Suggested sub-agent | Prompt pack |
|---:|---|---|---|---|
| 21 | [`TASK_OTEL.md`](../../agents/tasks/TASK_OTEL.md)<br/>Task: Add OpenTelemetry tracing + metrics<br/>Spec: [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) | @codex | `agents/subagents/backend_fastapi_platform.md` | `make codex-prompt TASK=agents/tasks/TASK_OTEL.md` |
| 22 | [`TASK_DASHBOARDS_TERRAFORM.md`](../../agents/tasks/TASK_DASHBOARDS_TERRAFORM.md)<br/>Task: Terraform-managed dashboards (Cloud Monitoring)<br/>Spec: [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) | @codex | `agents/subagents/infra_terraform_gcp.md` | `make codex-prompt TASK=agents/tasks/TASK_DASHBOARDS_TERRAFORM.md` |
| 23 | [`TASK_SLOS_BURN_RATE.md`](../../agents/tasks/TASK_SLOS_BURN_RATE.md)<br/>Task: SLOs + burn-rate alerts (Cloud Run)<br/>Spec: [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) | @codex | `agents/subagents/infra_terraform_gcp.md` | `make codex-prompt TASK=agents/tasks/TASK_SLOS_BURN_RATE.md` |
| 24 | [`TASK_COST_GUARDRAILS.md`](../../agents/tasks/TASK_COST_GUARDRAILS.md)<br/>Task: Cost guardrails (no edge WAF assumed)<br/>Spec: [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) | @codex | `agents/subagents/infra_terraform_gcp.md` | `make codex-prompt TASK=agents/tasks/TASK_COST_GUARDRAILS.md` |
| 25 | [`TASK_SMOKE_TESTS_DEPLOY.md`](../../agents/tasks/TASK_SMOKE_TESTS_DEPLOY.md)<br/>Task: Post-deploy smoke tests (Makefile shortcuts)<br/>Spec: [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) | @codex | `agents/subagents/infra_terraform_gcp.md` | `make codex-prompt TASK=agents/tasks/TASK_SMOKE_TESTS_DEPLOY.md` |
| 26 | [`TASK_BACKUP_RESTORE.md`](../../agents/tasks/TASK_BACKUP_RESTORE.md)<br/>Task: Backup/restore runbook + drills (Cloud SQL)<br/>Spec: [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) | @codex | `agents/subagents/infra_terraform_gcp.md` | `make codex-prompt TASK=agents/tasks/TASK_BACKUP_RESTORE.md` |
| 27 | [`TASK_RELEASE_PROCESS.md`](../../agents/tasks/TASK_RELEASE_PROCESS.md)<br/>Task: Release process (versioning + changelog discipline)<br/>Spec: [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) | @codex | `agents/subagents/product_planner.md` | `make codex-prompt TASK=agents/tasks/TASK_RELEASE_PROCESS.md` |
| 28 | [`TASK_DEPENDABOT_CODE_SCANNING.md`](../../agents/tasks/TASK_DEPENDABOT_CODE_SCANNING.md)<br/>Task: DevSecOps — dependency updates + code scanning<br/>Spec: [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) | @codex | `agents/subagents/security_governance.md` | `make codex-prompt TASK=agents/tasks/TASK_DEPENDABOT_CODE_SCANNING.md` |
| 29 | [`TASK_CONTAINER_IMAGE_SCANNING.md`](../../agents/tasks/TASK_CONTAINER_IMAGE_SCANNING.md)<br/>Task: DevSecOps — container image vulnerability scanning<br/>Spec: [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) | @codex | `agents/subagents/security_governance.md` | `make codex-prompt TASK=agents/tasks/TASK_CONTAINER_IMAGE_SCANNING.md` |

## M5 — Data platform integration

| # | Task | Owner | Suggested sub-agent | Prompt pack |
|---:|---|---|---|---|
| 30 | [`TASK_BIGQUERY_EXPORT.md`](../../agents/tasks/TASK_BIGQUERY_EXPORT.md)<br/>Task: BigQuery Export (Analytics + Governance)<br/>Spec: [`docs/SPECS/BIGQUERY_EXPORT.md`](../../docs/SPECS/BIGQUERY_EXPORT.md) | @codex | `agents/subagents/product_planner.md` | `make codex-prompt TASK=agents/tasks/TASK_BIGQUERY_EXPORT.md` |
| 31 | [`TASK_BIGQUERY_MODELS.md`](../../agents/tasks/TASK_BIGQUERY_MODELS.md)<br/>Task: BigQuery modeling notes (raw→curated→marts)<br/>Spec: [`docs/SPECS/BIGQUERY_EXPORT.md`](../../docs/SPECS/BIGQUERY_EXPORT.md) | @codex | `agents/subagents/product_planner.md` | `make codex-prompt TASK=agents/tasks/TASK_BIGQUERY_MODELS.md` |

## MO1 — Offline/PWA experience

| # | Task | Owner | Suggested sub-agent | Prompt pack |
|---:|---|---|---|---|
| 32 | [`TASK_PWA.md`](../../agents/tasks/TASK_PWA.md)<br/>Task: Make the Web UI an offline-friendly PWA | @codex |  | `make codex-prompt TASK=agents/tasks/TASK_PWA.md` |

## MO2 — Streaming answers

| # | Task | Owner | Suggested sub-agent | Prompt pack |
|---:|---|---|---|---|
| 33 | [`TASK_STREAMING.md`](../../agents/tasks/TASK_STREAMING.md)<br/>Task: Streaming answers (SSE) with incremental citations<br/>Spec: [`docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md`](../../docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md) | @codex | `agents/subagents/backend_fastapi_platform.md` | `make codex-prompt TASK=agents/tasks/TASK_STREAMING.md` |

## Unsequenced tasks

These task files exist but are not currently referenced in `docs/BACKLOG/MILESTONES.md` (so they are not in the numbered queue above).

| Task | Owner | Suggested sub-agent |
|---|---|---|
| [`TASK_CLOUDSQL.md`](../../agents/tasks/TASK_CLOUDSQL.md)<br/>Task: Harden Cloud SQL (Postgres) baseline (pgvector required) | @codex | `agents/subagents/postgres_hardening.md` |
| [`TASK_CONNECTORS_GCS.md`](../../agents/tasks/TASK_CONNECTORS_GCS.md)<br/>Task: Connector Ingestion — GCS (Sync Endpoint + Roadmap) | @codex | `agents/subagents/connector_gcs.md` |
| [`TASK_HYBRID_RETRIEVAL_TUNING.md`](../../agents/tasks/TASK_HYBRID_RETRIEVAL_TUNING.md)<br/>Task: Hybrid retrieval tuning (FTS + pgvector) | @codex | `agents/subagents/postgres_hardening.md` |
| [`TASK_MULTITENANCY_RBAC.md`](../../agents/tasks/TASK_MULTITENANCY_RBAC.md)<br/>Task: Multi-tenancy boundary (optional) | @codex | `agents/subagents/security_governance.md` |
| [`TASK_SEARCH_PERF_PROFILE.md`](../../agents/tasks/TASK_SEARCH_PERF_PROFILE.md)<br/>Task: Retrieval performance profiling (Postgres) | @codex | `agents/subagents/postgres_hardening.md` |
