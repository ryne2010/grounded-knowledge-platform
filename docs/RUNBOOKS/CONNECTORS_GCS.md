# Runbook: GCS Connector (Prefix Sync)

## Scope

This runbook covers operating the **GCS prefix sync connector** in private deployments.

- Endpoint: `POST /api/connectors/gcs/sync`
- Implementation: `app/connectors/gcs.py`
- Spec: `docs/SPECS/CONNECTOR_GCS_INGESTION.md`

This connector is intentionally **disabled** in the public demo deployment.

Related (planned):

- Event-driven ingestion via Pub/Sub push: `docs/SPECS/PUBSUB_EVENT_INGESTION.md`
- Periodic sync via Cloud Scheduler: `docs/SPECS/SCHEDULER_PERIODIC_SYNC.md`

Implemented endpoint:

- `POST /api/connectors/gcs/notify` (Pub/Sub push envelope)

## Safety posture

The connector is gated by:

- `PUBLIC_DEMO_MODE=0` (required)
- `ALLOW_CONNECTORS=1`
- **admin** role

**Deletion policy:** the connector is **add/update only**.

- It never deletes docs/chunks/embeddings.
- If an object disappears from the bucket/prefix, its doc remains until an operator deletes it manually.

## Preconditions

### App configuration

Private deployment (example):

- `PUBLIC_DEMO_MODE=0`
- `ALLOW_CONNECTORS=1`
- `AUTH_MODE=api_key` (recommended) with an admin key configured

### IAM permissions

The Cloud Run service account (or the identity running the sync) needs, at minimum:

- `storage.objects.list` on the bucket
- `storage.objects.get` on the bucket objects

The simplest approach is to grant:

- `roles/storage.objectViewer` on the target bucket

## How to run a sync

### Optional Make target

If you prefer shortcuts, the repo includes a Make target that posts to the API:

```bash
# Dry run
GCS_BUCKET=my-bucket GCS_PREFIX=knowledge/ GCS_DRY_RUN=true make gcs-sync

# Execute
GCS_BUCKET=my-bucket GCS_PREFIX=knowledge/ GCS_DRY_RUN=false make gcs-sync
```

Overrides:

- `GKP_API_URL` (default: `http://127.0.0.1:8080`)
- `GKP_API_KEY` (optional; used when `AUTH_MODE=api_key`)

### 1) Dry run (recommended)

```bash
curl -sS -X POST "${GKP_API_URL:-http://127.0.0.1:8080}/api/connectors/gcs/sync" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${GKP_API_KEY:-}" \
  -d '{
    "bucket": "my-bucket",
    "prefix": "knowledge/",
    "max_objects": 200,
    "dry_run": true
  }'
```

Expected outcome:

- Response includes `scanned`, `skipped_unsupported`
- Each `results[]` entry includes `action: "would_ingest"`

### 2) Execute the sync

```bash
curl -sS -X POST "${GKP_API_URL:-http://127.0.0.1:8080}/api/connectors/gcs/sync" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${GKP_API_KEY:-}" \
  -d '{
    "bucket": "my-bucket",
    "prefix": "knowledge/",
    "max_objects": 200,
    "dry_run": false,
    "classification": "internal",
    "retention": "indefinite",
    "tags": ["client-x"],
    "notes": "Initial import"
  }'
```

Expected outcome:

- Response includes `ingested` and `changed`
- Re-running the same sync should produce many `changed=false` items

## Event-driven ingestion (Pub/Sub push)

Use this when you want object-finalize events to ingest automatically.

### Endpoint behavior

- `POST /api/connectors/gcs/notify`
- accepts Pub/Sub push envelope
- processes `OBJECT_FINALIZE` events (attributes-first, `message.data` fallback)
- returns `202` for accepted events and idempotent duplicates
- returns `404` when demo mode or connectors are disabled

### Terraform setup (private deployments)

Enable optional Pub/Sub resources in `infra/gcp/cloud_run_demo/terraform.tfvars`:

```hcl
allow_unauthenticated      = false
enable_pubsub_push_ingest  = true
pubsub_push_bucket         = "my-bucket"
pubsub_push_prefix         = "knowledge/"
```

Recommended app overrides for private mode:

```hcl
app_env_overrides = {
  PUBLIC_DEMO_MODE = "0"
  ALLOW_CONNECTORS = "1"
  AUTH_MODE        = "api_key"
}
```

Then run:

```bash
make plan
make apply
```

### Manual endpoint test

```bash
curl -sS -X POST "${GKP_API_URL:-http://127.0.0.1:8080}/api/connectors/gcs/notify" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${GKP_API_KEY:-}" \
  -d '{
    "message": {
      "messageId": "manual-test-1",
      "attributes": {
        "eventType": "OBJECT_FINALIZE",
        "bucketId": "my-bucket",
        "objectId": "knowledge/guide.txt",
        "objectGeneration": "1",
        "objectSize": "128"
      }
    },
    "subscription": "projects/demo/subscriptions/gkp-ingest-events-push"
  }'
```

Expected outcome:

- `202 Accepted`
- response includes `run_id`, `gcs_uri`, and `result` (`changed|unchanged|skipped_unsupported|ignored_event`)
- repeated delivery for the same object remains idempotent (no duplicate docs)

## Local development notes

### Token acquisition

The connector uses the metadata server by default (Cloud Run / GCE).

For local development, you can set a temporary access token:

```bash
export GCP_ACCESS_TOKEN="$(gcloud auth print-access-token)"
```

Notes:

- This is an **escape hatch** for local dev only.
- Prefer running the sync on Cloud Run with a service account for production.

## Observability

- The sync response includes a `run_id`.
- In Cloud Run, use structured logs and search for the `run_id`.

Useful endpoints:

- `/api/meta` to confirm `connectors_enabled=true` and `public_demo_mode=false`

## Common failure modes

### `403 Connectors are disabled in this deployment`

- `PUBLIC_DEMO_MODE=1` OR `ALLOW_CONNECTORS=0`

Fix:

- Ensure private deployment env is set (`PUBLIC_DEMO_MODE=0`, `ALLOW_CONNECTORS=1`).

### `401 Missing API key` / `401 Invalid API key`

- `AUTH_MODE=api_key` enabled but request did not include `x-api-key`, or key is wrong.

Fix:

- Provide `x-api-key: …` for an admin key.

### `GCS list failed` / `GCS download failed`

Likely causes:

- Service account missing Storage permissions
- Bucket/prefix is wrong

Fix:

- Verify bucket IAM and object existence.

### `Unable to reach the GCP metadata server`

- You ran the connector locally without `GCP_ACCESS_TOKEN`.

Fix:

- Set `GCP_ACCESS_TOKEN` locally, or run in a GCP workload.

### Large files / timeouts

- Default connector timeouts are tuned for typical doc sizes.

Mitigations:

- Reduce `max_objects`
- Split prefixes
- Increase Cloud Run request timeout for the service (Terraform)

## Cleanup / rollback

Because this connector is add/update only:

- A “bad sync” does not automatically undo itself.
- To remove content, delete the corresponding docs via admin tools (if enabled) or via a maintenance script.

(Deletions are intentionally disabled in the public demo deployment.)
