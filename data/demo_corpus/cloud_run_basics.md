# GCP Engineering: Cloud Run Operations

Cloud Run is a managed serverless runtime for stateless containers.

Core engineering patterns:
- Build immutable images and deploy by tag or digest.
- Use revision-based rollout with controlled traffic shifts.
- Keep startup paths fast and deterministic.
- Treat environment variables and secrets as deploy-time config, not code.

Reliability guardrails:
- Set min/max instances intentionally for latency and cost behavior.
- Keep request timeouts aligned with downstream dependencies.
- Use health/readiness endpoints for fast diagnostics.
- Capture request IDs and structured logs for incident response.

Security and access:
- Keep production services private by default.
- Grant `roles/run.invoker` to groups instead of individual users.
- Use Secret Manager for API keys and database credentials.
- Enforce least privilege on runtime service accounts.

Observability:
- Capture request traces and application spans.
- Instrument retrieval and generation stages for latency attribution.
- Alert on 5xx rate and latency burn.
- Keep sensitive payloads out of logs and traces by default.
