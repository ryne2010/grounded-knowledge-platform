# Cost Incident Runbook

Use this runbook when spend spikes unexpectedly for a deployment in `infra/gcp/cloud_run_demo`.

## Trigger conditions

- Billing budget alert fires (`50%`, `90%`, or `100%` threshold)
- Unexpected daily spend trend in Cloud Billing reports
- Sudden Cloud Run request surge that does not match expected traffic

## Fast triage checklist

1. Confirm source of spend:
   - Cloud Run request/instance metrics
   - Cloud SQL usage (if enabled)
   - Cloud Logging ingestion spikes
   - Cloud Build or Artifact Registry growth
2. Confirm blast radius:
   - single project or multiple projects
   - single revision or all revisions
3. Check recent changes:
   - latest deploy revision
   - Terraform/app config changes
   - auth mode or invoker access changes

## Immediate containment actions

1. Reduce Cloud Run cost envelope:
   - lower `max_instances`
   - lower `max_request_concurrency` if runaway per-instance saturation is causing retries/backpressure
   - lower `request_timeout_seconds` to cut long-running abusive requests
2. Tighten access temporarily:
   - set `allow_unauthenticated = false`
   - grant `private_invoker_members` only to operator principals while investigating
3. Tighten app guardrails:
   - keep `RATE_LIMIT_ENABLED=1`
   - lower `RATE_LIMIT_MAX_REQUESTS` if traffic is abusive
4. Pause non-essential workloads:
   - disable optional connector/scheduler jobs in private deployments
   - pause rebuild-heavy workflows

## Recovery steps

1. Identify root cause (traffic abuse, app bug, deployment config, dependency issue).
2. Keep a safe interim config until trend is stable for at least 24h.
3. Restore normal access gradually:
   - re-enable unauthenticated access only if needed for public demo
   - revert temporary conservative limits in measured steps
4. Record incident notes and follow-ups:
   - guardrail value changes
   - detection gaps (alerts, dashboards, budget thresholds)
   - permanent fixes

## Terraform knobs reference

- `max_instances`
- `max_request_concurrency`
- `request_timeout_seconds`
- `enable_billing_budget`
- `billing_account_id`
- `billing_budget_amount_usd`
- `billing_budget_alert_thresholds`

## Validation after mitigation

- `GET /health` returns `200`
- `GET /api/meta` confirms expected safety flags
- Cloud Run error/latency dashboards stabilize
- Budget forecast trend returns to expected range
