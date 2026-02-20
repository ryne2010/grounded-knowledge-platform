# Observability (Logging + Monitoring + SLOs)

This repo treats observability as **code**: dashboards, alerts, log routing, and SLOs are provisioned via Terraform.

Files to review:
- `infra/gcp/cloud_run_demo/observability.tf` — dashboards + basic alerts
- `infra/gcp/cloud_run_demo/log_views.tf` — service-scoped log bucket + sink + log view
- `infra/gcp/cloud_run_demo/slo.tf` — Service Monitoring + Availability SLO + burn-rate alerts

---

## OpenTelemetry tracing (optional)

The API supports OpenTelemetry tracing with a strict default-off posture.

Environment variables:
- `OTEL_ENABLED=0|1` (default: `0`)
- `OTEL_TRACES_EXPORTER=auto|none|otlp|gcp_trace` (default: `auto`)
- `OTEL_SERVICE_NAME` (default: `grounded-knowledge-platform`)
- `OTEL_EXPORTER_OTLP_ENDPOINT` (optional; OTLP HTTP endpoint)
- `OTEL_DEBUG_CONTENT=0|1` (default: `0`)

When enabled, spans include:
- request lifecycle (FastAPI instrumentation)
- `safety.prompt_injection_scan`
- `retrieval.retrieve`
- `generation.answer`

Metrics (OTEL SDK) include:
- `gkp.http.server.requests`
- `gkp.http.server.duration_ms`
- `gkp.query.safety_scan.duration_ms`
- `gkp.query.retrieval.duration_ms`
- `gkp.query.generation.duration_ms`

These are emitted only when `OTEL_ENABLED=1`; otherwise metric recorders are no-ops.

Privacy-by-default:
- document text and raw user prompts are **not** recorded in span attributes by default
- `OTEL_DEBUG_CONTENT=1` is reserved for short-lived debugging in private environments

Cloud Run notes:
- `OTEL_TRACES_EXPORTER=auto` on Cloud Run defaults to `gcp_trace` when no OTLP endpoint is set.
- For managed collectors, set `OTEL_TRACES_EXPORTER=otlp` + `OTEL_EXPORTER_OTLP_ENDPOINT`.
- keep OTEL off in public demo mode unless you explicitly need traces

---

## Logging: service-scoped logs (client-safe pattern)

Instead of giving stakeholders broad `roles/logging.viewer` access on the project, this repo:

1) Routes only this service’s logs into a dedicated log bucket (Logs Router sink).
2) Creates a log view over that bucket.
3) Grants clients `roles/logging.viewAccessor` with an IAM condition pinned to that view.

This is a common pattern for:
- government/regulated work
- consulting engagements with shared observability
- multi-tenant environments

---

## Monitoring dashboards

The default dashboard includes:
- request volume
- error (5xx) rate
- p95-ish latency (via Cloud Run metrics)

Dashboards are safe to share with view-only audiences via `roles/monitoring.viewer`.

---

## SLOs and error budgets (staff-level ops story)

`slo.tf` creates:
- a **Service Monitoring service** for the Cloud Run service
- an **availability SLO** (2xx / total)
- **burn-rate alerts**:
  - fast burn (5m > 14.4x)
  - slow burn (1h > 6x)

Why burn rate alerts?
- They reflect **error budget consumption** instead of static thresholds.
- They are robust across traffic volume changes.

---

## Troubleshooting drills (great interview practice)

Try these controlled failures and document your findings:

1) **IAM failure**
   Remove Secret Manager access (if used) or remove invoker role (for private services) and watch:
   - Cloud Run revision fails or 401/403 spikes
   - logs show permission errors

2) **Bad deploy**
   Deploy a container that listens on the wrong port and confirm:
   - revision fails health checks
   - error surfaces in Cloud Run + logs

3) **Performance regression**
   Add an artificial delay and observe:
   - latency metrics rise
   - alert thresholds trigger
   - SLO burn-rate trends change

Capture your results in `RUNBOOK.md` — that’s interview gold.
