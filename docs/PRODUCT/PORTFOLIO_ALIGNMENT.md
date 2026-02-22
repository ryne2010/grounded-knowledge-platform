# Portfolio alignment

This document explains **how the repo demonstrates the capabilities** described in the associated resumes/case studies:

- GCP engineer / DevSecOps: Terraform-first Cloud Run deployments, policy gates, observability, runbooks
- Data architect: governed ingestion, contracts/drift/lineage, replay/backfills, evaluation and measurable quality

This is meant to be readable by hiring managers and technical interviewers.

> Note: The public demo remains intentionally constrained. The “enterprise” capabilities are demonstrated through
> documentation + planned tasks for private deployments.

---

## Capability → where it shows up in the repo

| Capability | Where it’s implemented today | Where it’s expanded (tasks/specs) |
|---|---|---|
| Terraform-first Cloud Run deployments | `infra/gcp/` + Makefile (`make deploy`, remote state) | `agents/tasks/TASK_SMOKE_TESTS_DEPLOY.md`, `TASK_RELEASE_PROCESS.md` |
| Policy-as-code / IaC hygiene | GitHub Actions: terraform fmt/validate + tflint/tfsec/checkov/conftest | Expand gates in `TASK_COST_GUARDRAILS.md` |
| Cloud SQL Postgres baseline | `docs/SPECS/CLOUDSQL_HARDENING.md`, local `compose.yml` | `TASK_CLOUDSQL.md`, `TASK_HYBRID_RETRIEVAL_TUNING.md` |
| pgvector search | Postgres schema + retrieval code path | Tuning + perf profiling tasks |
| Grounded answers w/ citations | `/api/query` and UI | `TASK_DOC_VIEWER_CITATIONS.md`, `TASK_QUERY_EXPLAIN_DRAWER.md` |
| Safe refusal (no evidence → refuse) | baseline query policy | `TASK_SAFETY_HARDENING.md` |
| Evaluation harness | CLI + demo datasets | `TASK_EVAL_PRODUCTIZATION.md`, `TASK_EVAL_CI_SMOKE.md` |
| Connector ingestion (GCS) | `POST /api/connectors/gcs/sync` (private-only) | `TASK_CONNECTORS_GCS_UI.md`, `TASK_PUBSUB_PUSH_INGEST.md` |
| Idempotency + replay/backfills | baseline ingestion rules | `TASK_REPLAY_BACKFILL.md`, ingestion run history |
| Metadata governance (classification/retention/tags) | data model + docs | `TASK_GOVERNANCE_METADATA_UI.md`, `TASK_RETENTION_ENFORCEMENT.md` |
| Auditability | runbooks + logging | `TASK_AUDIT_EVENTS.md` |
| Observability (dashboards/SLOs/runbooks) | `docs/OBSERVABILITY.md` + runbooks | `TASK_OTEL.md`, `TASK_DASHBOARDS_TERRAFORM.md`, `TASK_SLOS_BURN_RATE.md` |
| Cost guardrails (no edge WAF) | demo mode + Cloud Run caps | `TASK_COST_GUARDRAILS.md` |
| Data platform integration (BigQuery) | Private export + modeling examples (`docs/RUNBOOKS/BIGQUERY_EXPORT.md`, `docs/BIGQUERY_MODELING.md`, `infra/bigquery_models/`) | Expand with project-specific orchestration/BI in client deployments |

---

## How to demo it

- Public demo script: `docs/PRODUCT/DEMO_SCRIPT.md`
- Private deployment operator demo (auth + connector sync): see milestone M2 in `docs/BACKLOG/MILESTONES.md`
