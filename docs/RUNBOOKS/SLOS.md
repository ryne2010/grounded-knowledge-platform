# SLO Runbook (Cloud Run)

This runbook covers SLO burn-rate alerts created by `infra/gcp/cloud_run_demo/slo.tf`.

## SLOs in this stack

- Availability SLO:
  - SLI: ratio of `2xx` requests to total requests
  - default goal: `99.5%` over `28` days
- Latency SLO:
  - SLI: ratio of requests under `slo_latency_threshold_ms`
  - defaults: threshold `1200ms`, goal `95%` over `28` days

## Burn-rate alerts

Each SLO has two burn-rate conditions:

- Fast burn (`1h`): catches sharp regressions
- Slow burn (`6h`): catches sustained degradation and reduces noise

Default multipliers:

- `slo_burn_rate_fast_threshold=6`
- `slo_burn_rate_slow_threshold=3`

## First-response checklist

1. Confirm scope and blast radius:
   - is it one service revision or all traffic?
   - does it affect availability, latency, or both?
2. Check Cloud Run dashboard widgets:
   - request count / 5xx / p95 latency
   - query stage latency (retrieval vs answer generation)
3. Check Cloud SQL health:
   - CPU utilization
   - active backends / connection pressure
4. Check recent deploy and config changes:
   - new revision rollout
   - env var or Terraform changes
   - auth/IAM changes causing 401/403 spikes
5. Stabilize:
   - roll back to last known-good revision if needed
   - reduce load (temporary max instances / traffic controls) while investigating

## Common causes

- New revision regression (code path or dependency latency)
- Cloud SQL saturation (CPU or connections)
- Upstream dependency latency spikes
- Misconfigured auth path causing elevated 4xx/5xx

## Tuning guidance

Adjust in `terraform.tfvars` when alert noise is too high or too low:

- `slo_availability_goal`
- `slo_latency_goal`
- `slo_latency_threshold_ms`
- `slo_burn_rate_fast_threshold`
- `slo_burn_rate_slow_threshold`

Raise thresholds carefully and only after a post-incident review.
