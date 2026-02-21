# Spec: Observability and ops baseline

## Context

A “production-feel” platform needs more than features:

- predictable deployments
- usable telemetry
- cost guardrails
- runbooks

This repo targets Cloud Run + Cloud SQL deployments and should provide an operator-friendly baseline without requiring edge/WAF products.

## Goals

- Adopt a consistent observability baseline:
  - structured logs
  - request ids
  - optional OTEL traces/metrics
- Provide dashboards + SLO/burn-rate alerts as code (Terraform).
- Provide cost guardrails appropriate for a public demo and small private deployments.
- Provide smoke tests and basic backup/restore guidance.

## Non-goals

- Full enterprise SIEM integration
- Mandatory Cloud Armor / Cloudflare
- Heavy APM vendor adoption

## Proposed design

### User experience

- Public demo remains cost-capped and safe.
- Private deployments can enable deeper visibility and alerts.

### API surface

No new public APIs required.

Private deployment endpoints may expose:

- `/health` and `/api/meta` for smoke checks

### Data model

No required DB changes.

(Optionally later: persist operational metrics in BigQuery via export.)

### Security / privacy

- Avoid logging secrets.
- Use least-privilege IAM for log/dashboards access.

### Observability

- Logs:
  - JSON logs with consistent keys (`severity`, `request_id`, `event`, `latency_ms`, `status_code`).
- Traces (optional):
  - OTEL instrumentation for API requests and key internal spans (ingestion, query, embedding calls).
- Metrics:
  - request count/latency/error rate
  - ingestion failures (private)
  - eval run pass rate (private)

Dashboards:

- Cloud Run request rate/latency/error
- Cloud SQL connections/errors
- Ingestion runs (private)
- Eval runs (private)

SLOs:

- API availability SLO
- API latency SLO

Burn-rate alerts:

- 1h and 6h burn-rate windows

### Rollout / migration

- Start with logs + request ids (already baseline).
- Add OTEL behind `ENABLE_OTEL=1`.
- Add dashboards/SLOs as Terraform modules.
- Add smoke tests to the deploy Makefile.

## Alternatives considered

- Vendor-specific APM: strong features, but limits portability.
- Manual dashboards: faster initially, but not repeatable.

## Acceptance criteria

- A deploy produces usable dashboards and a minimal SLO set.
- Smoke tests can be run via Makefile.
- Public demo has explicit cost caps and rate limits without requiring an edge WAF.

## Validation plan

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
