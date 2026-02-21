# Cost hygiene

This repo is designed to be **safe to keep running** as a long-lived demo.

## Built-in safeguards

### Cloud Run guardrails
- min/max instances are configurable (`min_instances`, `max_instances`)
- request concurrency is configurable (`max_request_concurrency`)
- request timeout is configurable (`request_timeout_seconds`)
- serverless = no always-on VM cost for the app tier

### Artifact Registry cleanup policies (dry-run by default)
In `infra/gcp/cloud_run_demo/main.tf` we configure cleanup policies with:

- `cleanup_policy_dry_run = true`

This shows the pattern without deleting anything unexpectedly.

Once you're confident, set it to `false` to enable actual cleanup.

### Log retention
`infra/gcp/cloud_run_demo/log_views.tf` creates a service-scoped log bucket with:

- `log_retention_days` (default: 30)

## Recommended project-level controls (platform repo)

In a real environment, enforce these centrally (Repo 3):
- Billing budgets + alerting
- Org Policies / constraints
- Standard log exclusion rules (avoid runaway telemetry costs)
- Artifact Registry retention baselines

## Optional in-repo billing budget alerts

`infra/gcp/cloud_run_demo/cost_guardrails.tf` can create a project-scoped billing budget when:

- `enable_billing_budget=true`
- `billing_account_id` is set

Recommended starter thresholds:

- `0.5` (50%)
- `0.9` (90%)
- `1.0` (100%)

Runbook: `docs/RUNBOOKS/COST_INCIDENT.md`
