# Task: Add OpenTelemetry tracing + metrics

Owner: @codex

## Goal

Bring production-grade observability to the API (and optionally the web app) for Cloud Run:

- distributed tracing (HTTP + key spans)
- structured logs correlation (`trace_id`, `request_id`)
- basic metrics (request count/latency, retrieval latency, LLM latency)

This aligns with the job apps/case studies emphasis on SRE/observability and Cloud Run readiness.

## Requirements

### Tracing

- Add OpenTelemetry SDK instrumentation for FastAPI.
- Emit spans for:
  - request lifecycle
  - retrieval (embedding + lexical + rerank)
  - prompt-injection scan
  - answer generation (provider-specific)
  - storage operations (optional)

### Metrics

- Expose Prometheus-compatible endpoint in private deployments (optional):
  - `GET /metrics` gated by auth (if auth task is implemented)

OR

- Emit Cloud Monitoring-compatible metrics via OTEL exporter.

### Export

- Support configuration via env vars:
  - `OTEL_ENABLED=0|1` (default 0)
  - `OTEL_EXPORTER_OTLP_ENDPOINT`
  - `OTEL_SERVICE_NAME=grounded-knowledge-platform`

### Safety

- Do not log document content or user prompts in plaintext logs by default.
- Allow a debug mode (explicit env var) to include more detail.

## Implementation notes

- Prefer official OpenTelemetry instrumentation packages.
- Ensure minimal overhead when disabled.
- Cloud Run: document how to route OTLP to Cloud Trace/Cloud Monitoring.

## Tests

- Unit test: spans created for `/api/query` request (can be a smoke test with an in-memory exporter)
- Regression: request ID header is preserved.

## Docs

- Add `docs/OBSERVABILITY.md`:
  - env vars
  - Cloud Run setup
  - what is (and is not) recorded
