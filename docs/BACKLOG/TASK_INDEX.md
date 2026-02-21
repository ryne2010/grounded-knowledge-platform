# Task index

This is a flat index of all task files under `agents/tasks/`.

Regenerate:

```bash
make task-index
```

| Task | Milestone | Owner | Suggested sub-agent | Spec |
|---|---|---|---|---|
| [`TASK_ACCESSIBILITY_AUDIT.md`](../../agents/tasks/TASK_ACCESSIBILITY_AUDIT.md)<br/>Task: Accessibility audit + fixes (UI) | M1 | @codex | `agents/subagents/frontend_ux.md` | [`docs/SPECS/UI_UX_PRODUCTION_POLISH.md`](../../docs/SPECS/UI_UX_PRODUCTION_POLISH.md) |
| [`TASK_DEMO_GUIDED_TOUR.md`](../../agents/tasks/TASK_DEMO_GUIDED_TOUR.md)<br/>Task: Public demo guided tour + suggested queries | M1 | @codex | `agents/subagents/frontend_ux.md` | [`docs/SPECS/UI_UX_PRODUCTION_POLISH.md`](../../docs/SPECS/UI_UX_PRODUCTION_POLISH.md) |
| [`TASK_DOC_VIEWER_CITATIONS.md`](../../agents/tasks/TASK_DOC_VIEWER_CITATIONS.md)<br/>Task: Doc viewer + citations UX (production feel) | M1 | @codex | `agents/subagents/frontend_ux.md` | [`docs/SPECS/UI_UX_PRODUCTION_POLISH.md`](../../docs/SPECS/UI_UX_PRODUCTION_POLISH.md) |
| [`TASK_QUERY_EXPLAIN_DRAWER.md`](../../agents/tasks/TASK_QUERY_EXPLAIN_DRAWER.md)<br/>Task: “Explain this answer” drawer (retrieval transparency) | M1 | @codex | `agents/subagents/frontend_ux.md` | [`docs/SPECS/UI_UX_PRODUCTION_POLISH.md`](../../docs/SPECS/UI_UX_PRODUCTION_POLISH.md) |
| [`TASK_UI_UX_POLISH.md`](../../agents/tasks/TASK_UI_UX_POLISH.md)<br/>Task: UI/UX Production Polish (Modern SaaS Admin) | M1 | @codex | `agents/subagents/frontend_ux.md` | [`docs/SPECS/UI_UX_PRODUCTION_POLISH.md`](../../docs/SPECS/UI_UX_PRODUCTION_POLISH.md) |
| [`TASK_AUTH.md`](../../agents/tasks/TASK_AUTH.md)<br/>Task: Add authn/authz for private deployments | M2 | @codex | `agents/subagents/backend_fastapi_platform.md` | [`docs/SPECS/AUTH_PRIVATE_DEPLOYMENTS.md`](../../docs/SPECS/AUTH_PRIVATE_DEPLOYMENTS.md) |
| [`TASK_CONNECTORS_GCS_UI.md`](../../agents/tasks/TASK_CONNECTORS_GCS_UI.md)<br/>Task: GCS sync UI (admin-only, private deployments) | M2 | @codex | `agents/subagents/frontend_ux.md` | [`docs/SPECS/CONNECTOR_GCS_INGESTION.md`](../../docs/SPECS/CONNECTOR_GCS_INGESTION.md) |
| [`TASK_DATA_CONTRACTS.md`](../../agents/tasks/TASK_DATA_CONTRACTS.md)<br/>Task: Data contracts + schema drift for tabular ingests | M2 | @codex | `agents/subagents/security_governance.md` | [`docs/DATA_CONTRACTS.md`](../../docs/DATA_CONTRACTS.md) |
| [`TASK_INGESTION_RUNS.md`](../../agents/tasks/TASK_INGESTION_RUNS.md)<br/>Task: Ingestion runs (grouping + status + summaries) | M2 | @codex | `agents/subagents/backend_fastapi_platform.md` |  |
| [`TASK_INGESTION_RUNS_UI.md`](../../agents/tasks/TASK_INGESTION_RUNS_UI.md)<br/>Task: Ingestion runs UI (history + detail) | M2 | @codex | `agents/subagents/frontend_ux.md` |  |
| [`TASK_PUBSUB_PUSH_INGEST.md`](../../agents/tasks/TASK_PUBSUB_PUSH_INGEST.md)<br/>Task: Pub/Sub push ingestion (Cloud Storage notifications) | M2 | @codex | `agents/subagents/backend_fastapi_platform.md` | [`docs/SPECS/PUBSUB_EVENT_INGESTION.md`](../../docs/SPECS/PUBSUB_EVENT_INGESTION.md) |
| [`TASK_REPLAY_BACKFILL.md`](../../agents/tasks/TASK_REPLAY_BACKFILL.md)<br/>Task: Replay/backfill tooling (safe reprocessing) | M2 | @codex | `agents/subagents/backend_fastapi_platform.md` |  |
| [`TASK_SCHEDULER_PERIODIC_SYNC.md`](../../agents/tasks/TASK_SCHEDULER_PERIODIC_SYNC.md)<br/>Task: Periodic GCS sync via Cloud Scheduler | M2 | @codex | `agents/subagents/infra_terraform_gcp.md` | [`docs/SPECS/SCHEDULER_PERIODIC_SYNC.md`](../../docs/SPECS/SCHEDULER_PERIODIC_SYNC.md) |
| [`TASK_AUDIT_EVENTS.md`](../../agents/tasks/TASK_AUDIT_EVENTS.md)<br/>Task: Audit events (admin action logging) | M3 | @codex | `agents/subagents/security_governance.md` | [`docs/SPECS/GOVERNANCE_METADATA.md`](../../docs/SPECS/GOVERNANCE_METADATA.md) |
| [`TASK_EVAL_CI_SMOKE.md`](../../agents/tasks/TASK_EVAL_CI_SMOKE.md)<br/>Task: CI smoke eval gate | M3 | @codex | `agents/subagents/eval_harness.md` | [`docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`](../../docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md) |
| [`TASK_EVAL_DATASET_AUTHORING.md`](../../agents/tasks/TASK_EVAL_DATASET_AUTHORING.md)<br/>Task: Eval dataset authoring guide + tooling | M3 | @codex | `agents/subagents/eval_harness.md` | [`docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`](../../docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md) |
| [`TASK_EVAL_PRODUCTIZATION.md`](../../agents/tasks/TASK_EVAL_PRODUCTIZATION.md)<br/>Task: Evaluation Productization | M3 | @codex | `agents/subagents/eval_harness.md` | [`docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`](../../docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md) |
| [`TASK_GOVERNANCE_METADATA_UI.md`](../../agents/tasks/TASK_GOVERNANCE_METADATA_UI.md)<br/>Task: Governance metadata UI (classification/retention/tags) | M3 | @codex | `agents/subagents/frontend_ux.md` | [`docs/SPECS/GOVERNANCE_METADATA.md`](../../docs/SPECS/GOVERNANCE_METADATA.md) |
| [`TASK_RETENTION_ENFORCEMENT.md`](../../agents/tasks/TASK_RETENTION_ENFORCEMENT.md)<br/>Task: Retention enforcement (hide/expire content) | M3 | @codex | `agents/subagents/backend_fastapi_platform.md` | [`docs/SPECS/GOVERNANCE_METADATA.md`](../../docs/SPECS/GOVERNANCE_METADATA.md) |
| [`TASK_SAFETY_HARDENING.md`](../../agents/tasks/TASK_SAFETY_HARDENING.md)<br/>Task: Safety hardening (prompt injection + exfiltration) | M3 | @codex | `agents/subagents/security_governance.md` |  |
| [`TASK_BACKUP_RESTORE.md`](../../agents/tasks/TASK_BACKUP_RESTORE.md)<br/>Task: Backup/restore runbook + drills (Cloud SQL) | M4 | @codex | `agents/subagents/infra_terraform_gcp.md` | [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) |
| [`TASK_CONTAINER_IMAGE_SCANNING.md`](../../agents/tasks/TASK_CONTAINER_IMAGE_SCANNING.md)<br/>Task: DevSecOps — container image vulnerability scanning | M4 | @codex | `agents/subagents/security_governance.md` | [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) |
| [`TASK_COST_GUARDRAILS.md`](../../agents/tasks/TASK_COST_GUARDRAILS.md)<br/>Task: Cost guardrails (no edge WAF assumed) | M4 | @codex | `agents/subagents/infra_terraform_gcp.md` | [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) |
| [`TASK_DASHBOARDS_TERRAFORM.md`](../../agents/tasks/TASK_DASHBOARDS_TERRAFORM.md)<br/>Task: Terraform-managed dashboards (Cloud Monitoring) | M4 | @codex | `agents/subagents/infra_terraform_gcp.md` | [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) |
| [`TASK_DEPENDABOT_CODE_SCANNING.md`](../../agents/tasks/TASK_DEPENDABOT_CODE_SCANNING.md)<br/>Task: DevSecOps — dependency updates + code scanning | M4 | @codex | `agents/subagents/security_governance.md` | [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) |
| [`TASK_OTEL.md`](../../agents/tasks/TASK_OTEL.md)<br/>Task: Add OpenTelemetry tracing + metrics | M4 | @codex | `agents/subagents/backend_fastapi_platform.md` | [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) |
| [`TASK_RELEASE_PROCESS.md`](../../agents/tasks/TASK_RELEASE_PROCESS.md)<br/>Task: Release process (versioning + changelog discipline) | M4 | @codex | `agents/subagents/product_planner.md` | [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) |
| [`TASK_SLOS_BURN_RATE.md`](../../agents/tasks/TASK_SLOS_BURN_RATE.md)<br/>Task: SLOs + burn-rate alerts (Cloud Run) | M4 | @codex | `agents/subagents/infra_terraform_gcp.md` | [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) |
| [`TASK_SMOKE_TESTS_DEPLOY.md`](../../agents/tasks/TASK_SMOKE_TESTS_DEPLOY.md)<br/>Task: Post-deploy smoke tests (Makefile shortcuts) | M4 | @codex | `agents/subagents/infra_terraform_gcp.md` | [`docs/SPECS/OBSERVABILITY_OPS.md`](../../docs/SPECS/OBSERVABILITY_OPS.md) |
| [`TASK_BIGQUERY_EXPORT.md`](../../agents/tasks/TASK_BIGQUERY_EXPORT.md)<br/>Task: BigQuery Export (Analytics + Governance) | M5 | @codex | `agents/subagents/product_planner.md` | [`docs/SPECS/BIGQUERY_EXPORT.md`](../../docs/SPECS/BIGQUERY_EXPORT.md) |
| [`TASK_BIGQUERY_MODELS.md`](../../agents/tasks/TASK_BIGQUERY_MODELS.md)<br/>Task: BigQuery modeling notes (raw→curated→marts) | M5 | @codex | `agents/subagents/product_planner.md` | [`docs/SPECS/BIGQUERY_EXPORT.md`](../../docs/SPECS/BIGQUERY_EXPORT.md) |
| [`TASK_PWA.md`](../../agents/tasks/TASK_PWA.md)<br/>Task: Make the Web UI an offline-friendly PWA | MO1 | @codex |  |  |
| [`TASK_STREAMING.md`](../../agents/tasks/TASK_STREAMING.md)<br/>Task: Streaming answers (SSE) with incremental citations | MO2 | @codex | `agents/subagents/backend_fastapi_platform.md` | [`docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md`](../../docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md) |
| [`BUGFIX.md`](../../agents/tasks/BUGFIX.md)<br/>Task: Bug Fix |  |  |  |  |
| [`DOCS.md`](../../agents/tasks/DOCS.md)<br/>Task: Documentation Update |  |  |  |  |
| [`FEATURE.md`](../../agents/tasks/FEATURE.md)<br/>Task: Feature Implementation |  |  |  |  |
| [`REFACTOR.md`](../../agents/tasks/REFACTOR.md)<br/>Task: Refactor (No Behavior Change) |  |  |  |  |
| [`TASK_CLOUDSQL.md`](../../agents/tasks/TASK_CLOUDSQL.md)<br/>Task: Harden Cloud SQL (Postgres) baseline (pgvector required) |  | @codex | `agents/subagents/postgres_hardening.md` | [`docs/SPECS/CLOUDSQL_HARDENING.md`](../../docs/SPECS/CLOUDSQL_HARDENING.md) |
| [`TASK_CONNECTORS_GCS.md`](../../agents/tasks/TASK_CONNECTORS_GCS.md)<br/>Task: Connector Ingestion — GCS (Sync Endpoint + Roadmap) |  | @codex | `agents/subagents/connector_gcs.md` | [`docs/SPECS/CONNECTOR_GCS_INGESTION.md`](../../docs/SPECS/CONNECTOR_GCS_INGESTION.md) |
| [`TASK_HYBRID_RETRIEVAL_TUNING.md`](../../agents/tasks/TASK_HYBRID_RETRIEVAL_TUNING.md)<br/>Task: Hybrid retrieval tuning (FTS + pgvector) |  | @codex | `agents/subagents/postgres_hardening.md` |  |
| [`TASK_MULTITENANCY_RBAC.md`](../../agents/tasks/TASK_MULTITENANCY_RBAC.md)<br/>Task: Multi-tenancy boundary (optional) |  | @codex | `agents/subagents/security_governance.md` |  |
| [`TASK_SEARCH_PERF_PROFILE.md`](../../agents/tasks/TASK_SEARCH_PERF_PROFILE.md)<br/>Task: Retrieval performance profiling (Postgres) |  | @codex | `agents/subagents/postgres_hardening.md` |  |
| [`TASK_TEMPLATE.md`](../../agents/tasks/TASK_TEMPLATE.md)<br/>Task template |  | @codex | `agents/subagents/<subagent>.md` |  |
