# Event-driven ingestion (Pub/Sub)

Status: **Draft** (2026-02-21)

Owner: Repo maintainers

Related tasks:

- `agents/tasks/TASK_PUBSUB_PUSH_INGEST.md`

## Context

Private deployments may want **event-driven ingestion** rather than “scan a prefix” batch sync.

This spec defines an optional path:

- Cloud Storage sends object finalize events → Pub/Sub
- Pub/Sub push subscription calls a Cloud Run endpoint
- The endpoint ingests the single object (add/update only)

This matches the “event-driven ingestion + replay/backfill + observability” platform narrative.

## Safety posture

- **Disabled in `PUBLIC_DEMO_MODE`**
- Disabled unless `ALLOW_CONNECTORS=1`
- Endpoint requires **admin** identity (recommended: OIDC / service account identity)

**Deletion policy:** add/update only.

- Object delete events do **not** delete docs.
- Delete/tombstone is explicitly out of scope unless added later as an opt-in.

## API surface

### `POST /api/connectors/gcs/notify`

Receives a Pub/Sub push payload (Cloud Storage notification event).

- Validates the caller identity (OIDC preferred).
- Extracts the bucket + object key.
- Downloads object content.
- Calls the existing ingestion pipeline (`ingest_file`), using the same idempotency rules as batch sync.

Response:

- `202 Accepted` when the event is accepted for processing.
- `2xx` even if the object is a duplicate (idempotency).
- `4xx` only when the request is invalid/unauthorized.

## Payload

Pub/Sub push sends:

```json
{
  "message": {
    "data": "<base64>" ,
    "attributes": {
      "eventType": "OBJECT_FINALIZE",
      "bucketId": "my-bucket",
      "objectId": "knowledge/foo.pdf"
    },
    "messageId": "..."
  },
  "subscription": "..."
}
```

Implementation should support:

- attributes-first parsing
- fallback to decoding `message.data` if needed

## Reliability and retry

- Pub/Sub push will retry on non-2xx.
- The endpoint must be:
  - idempotent (safe to retry)
  - fast (do not block on long ingestion)

Recommended design:

- Accept the event quickly.
- Enqueue long work to a background queue (Cloud Tasks) or process synchronously only for small objects.

If Cloud Tasks is introduced:

- include a dead-letter path
- include per-object dedupe window

## Infrastructure requirements (Terraform)

- Pub/Sub topic: `gkp-ingest-events`
- Cloud Storage notification binding (bucket → topic)
- Push subscription:
  - push endpoint URL `/api/connectors/gcs/notify`
  - OIDC token from a dedicated service account
  - retry policy + dead-letter topic

IAM:

- Pub/Sub service account can invoke Cloud Run (invoker role)
- Ingest service account can read GCS objects

## Observability

For each event, log:

- request_id
- pubsub messageId
- gcs uri
- ingestion result (ingested/unchanged/skipped)
- latency and bytes

Expose counters:

- events received
- events ingested
- events deduped
- failures by reason

## Non-goals

- Exactly-once processing
- Deletion/tombstone behavior
- Multi-bucket routing (single bucket/prefix is enough initially)

