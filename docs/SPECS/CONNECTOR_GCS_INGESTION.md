# Connector Ingestion — GCS (Sync Endpoint)

Status: **Draft** (2026-02-21)

Owner: Repo maintainers

Related tasks:

- `agents/tasks/TASK_CONNECTORS_GCS.md`

## Context

Public hosting is read-only and uses the **included demo corpus only**.

For **private client deployments**, ingestion must support cloud-native workflows:
batch syncing documents from a GCS bucket/prefix into the corpus, with replayable lineage.

This spec defines the **GCS sync connector** baseline.

## Safety posture

- **Disabled in `PUBLIC_DEMO_MODE`**
- Disabled unless `ALLOW_CONNECTORS=1`
- Endpoint requires **admin** role (auth mode varies by deployment)

**Deletion policy (explicit):** sync is **add/update only**.

- The connector **never deletes** docs or chunks.
- If an object is removed from GCS, its previously ingested doc remains until an operator deletes it manually.
- Tombstoning/deletes may be added later as an opt-in feature with strong guardrails.

## API surface (baseline)

### `POST /api/connectors/gcs/sync`

Triggers a one-off sync for a prefix.

Request body:

```json
{
  "bucket": "my-bucket",
  "prefix": "knowledge/",
  "max_objects": 200,
  "dry_run": false,
  "classification": "internal",
  "retention": "indefinite",
  "tags": ["client-a"],
  "notes": "optional operator note"
}
```

Response summary (shape may evolve):

```json
{
  "run_id": "…",
  "started_at": 173…,
  "finished_at": 173…,
  "bucket": "my-bucket",
  "prefix": "knowledge/",
  "dry_run": false,
  "max_objects": 200,
  "scanned": 42,
  "skipped_unsupported": 3,
  "ingested": 39,
  "changed": 12,
  "results": [
    {
      "gcs_uri": "gs://my-bucket/knowledge/foo.pdf",
      "doc_id": "…",
      "doc_version": 2,
      "changed": true,
      "num_chunks": 14,
      "content_sha256": "…"
    }
  ]
}
```

## Implementation strategy

### Auth to GCS (no extra dependency)

Use Cloud Storage JSON API + bearer tokens:

- On Cloud Run / GCE, request an access token from the metadata server.
- For local dev, allow `GCP_ACCESS_TOKEN` env var (escape hatch).

### Idempotency

- Use stable `doc_id` derived from:
  - `title = object basename`
  - `source = gs://bucket/object`
- Ingestion compares `content_sha256` to mark `changed=false` on re-sync.

### Supported file types

Only ingest suffixes already supported by the ingestion pipeline:

- `.txt`, `.md`, `.pdf`, `.csv`, `.tsv`, `.xlsx`, `.xlsm`

## Future expansions (later)

- Pub/Sub notifications + push endpoint for event-driven ingestion
- Store connector provenance in a dedicated JSON column (instead of embedding JSON in notes)
- “Since timestamp” filtering to avoid scanning everything each sync
- Connector run history table (audit trail)

