# BigQuery Export (Private Deployments)

This runbook covers exporting operational datasets to BigQuery (or JSONL snapshots)
for private deployments.

Task source: `agents/tasks/TASK_BIGQUERY_EXPORT.md`  
Spec: `docs/SPECS/BIGQUERY_EXPORT.md`

## Guardrails

- Disabled in `PUBLIC_DEMO_MODE=1`.
- Export is operator/admin workflow for private deployments only.
- Exported governance fields are included from document metadata (`classification`, `retention`, `tags`).

## Exported datasets

The exporter writes three table-shaped datasets:

- `docs`
- `ingest_events`
- `eval_runs`

Lineage fields are always included:

- `doc_id`
- `doc_version`
- `content_sha256` (where applicable)

## CLI usage

JSONL snapshot only (safe default):

```bash
uv run python -m app.cli export-bigquery --jsonl-only
```

Target directory defaults to `dist/bigquery_export/raw` and includes:

- `docs.jsonl`
- `ingest_events.jsonl`
- `eval_runs.jsonl`
- `manifest.json`

Load into BigQuery:

```bash
uv run python -m app.cli export-bigquery \
  --project "$PROJECT_ID" \
  --dataset "gkp_ops" \
  --table-prefix "gkp_"
```

Optional:

- `--location us-central1`
- `--batch-size 500`
- `--jsonl-dir dist/bigquery_export/raw`

## Makefile shortcut

```bash
# JSONL only
make bigquery-export

# BigQuery load
make bigquery-export BQ_JSONL_ONLY=false BQ_PROJECT="$PROJECT_ID" BQ_DATASET="gkp_ops"
```

## Idempotency behavior

- JSONL snapshot export rewrites full table snapshots each run.
- BigQuery loads use truncate-then-append semantics per table, so reruns do not duplicate rows.

## IAM guidance

Grant the export principal least privilege for a single dataset (for example):

- `roles/bigquery.dataEditor` on the target dataset
- `roles/bigquery.jobUser` on the project

Avoid broad project-wide admin roles for routine exports.
