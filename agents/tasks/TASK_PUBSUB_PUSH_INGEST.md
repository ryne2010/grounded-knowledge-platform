# Task: Pub/Sub push ingestion (Cloud Storage notifications)

Spec: `docs/SPECS/PUBSUB_EVENT_INGESTION.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/backend_fastapi_platform.md` + `agents/subagents/infra_terraform_gcp.md`

## Goal

Enable **event-driven ingestion** for private deployments:

- Cloud Storage object finalize → Pub/Sub → Cloud Run push endpoint
- Endpoint ingests a single object (add/update only)
- Fully disabled in public demo mode

## Requirements

### Backend

- Add endpoint: `POST /api/connectors/gcs/notify`
- Gating:
  - `PUBLIC_DEMO_MODE=1` → always 404/disabled
  - `ALLOW_CONNECTORS!=1` → 404/disabled
  - must require admin authorization (same model as connector sync)

- Payload parsing:
  - support Pub/Sub push envelope
  - read `bucketId` + `objectId` from message attributes
  - fallback to decoding `message.data` (base64 JSON)

- Ingestion:
  - download the object via GCS API
  - reuse existing ingestion pipeline
  - enforce add/update-only semantics

- Return:
  - `202` on accept
  - `2xx` for idempotent duplicates

### Terraform

- Add optional resources (private deployments only):
  - Pub/Sub topic
  - push subscription
  - dead-letter topic (recommended)
  - IAM: Cloud Run invoker binding for subscription SA
  - Cloud Storage notification config (bucket → topic)

### Observability

- Structured logs:
  - pubsub message id
  - gcs uri
  - result (ingested/unchanged/skipped)
  - latency

### Docs

- Update `docs/RUNBOOKS/CONNECTORS_GCS.md` with:
  - how to set up notifications
  - how to test the push endpoint

## Acceptance criteria

- When an object is uploaded to the configured GCS bucket/prefix, the service ingests it.
- Uploading the same object again does not create duplicates.
- In demo mode, the endpoint is not reachable.

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py test`
- `python scripts/harness.py typecheck`
- Terraform: `terraform fmt` + `terraform validate`

