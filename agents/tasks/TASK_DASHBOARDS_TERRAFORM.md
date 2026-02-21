# Task: Terraform-managed dashboards (Cloud Monitoring)

Related:
- `docs/OBSERVABILITY.md`
- `agents/tasks/TASK_OTEL.md`

Spec: `docs/SPECS/OBSERVABILITY_OPS.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/infra_terraform_gcp.md`

## Goal

Provide “client-safe observability” by shipping dashboards as code:

- request rate/latency/error ratio (Cloud Run)
- query latency breakdown (retrieval vs answering)
- ingestion failures (private deployments)
- DB health (Cloud SQL)

## Requirements

- Terraform module(s) create:
  - Cloud Monitoring dashboards (JSON)
  - log-based metrics (optional)
  - alert policies (optional; SLOs handled in separate task)

- Keep demo posture in mind:
  - dashboards should work even with limited traffic
  - avoid recording sensitive payloads

## Acceptance criteria

- Fresh apply results in visible dashboards without manual click-ops.
- Docs explain how to find dashboards and what they mean.

## Validation

- `make tf-check`
- `terraform plan` shows dashboard resources
