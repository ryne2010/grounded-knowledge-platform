# Task: SLOs + burn-rate alerts (Cloud Run)

Spec: `docs/SPECS/OBSERVABILITY_OPS.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/infra_terraform_gcp.md`

## Goal

Define minimal SLOs and burn-rate alerts that make the project feel production-grade:

- availability SLO (e.g., 99.5% for demo)
- latency SLO (p95 threshold)
- burn-rate alerts (fast/slow)

## Requirements

- Terraform definitions for:
  - SLOs (or equivalent monitoring constructs)
  - alert policies using burn-rate style windows

- Docs:
  - `docs/RUNBOOKS/SLOS.md` (new)
  - include: what alerts mean and what to do first

## Acceptance criteria

- Alerts are actionable (not noisy).
- Thresholds are realistic for Cloud Run + Cloud SQL.

## Validation

- `make tf-check`
