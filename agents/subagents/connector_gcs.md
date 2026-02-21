# Sub-agent: GCS connector ingestion

You are implementing a connector that ingests documents from **Google Cloud Storage**.

## Mission

- batch ingest from `gs://bucket/prefix/**`
- idempotency + change detection
- record provenance/lineage per ingest event
- stay safe-by-default (disabled in public demo)

## Constraints (must follow)

- **Public demo mode must remain read-only**.
- File type allow-list only.
- Apply size caps before downloading objects.
- IAM should be minimal (objectViewer on a specific bucket).

## Hotspots

- `app/cli.py` (add `ingest-gcs` command)
- `app/ingestion.py` (reuse ingestion primitives)
- `app/storage.py` (persist provenance; consider `metadata_json`)
- `docs/SPECS/CONNECTOR_GCS_INGESTION.md`

## Validation

- unit tests for filtering/idempotency
- manual test against a small bucket (private deployment only)
