# Task: BigQuery Export (Analytics + Governance)

Spec: `docs/SPECS/BIGQUERY_EXPORT.md`

Owner: @codex
Suggested sub-agent: `agents/subagents/product_planner.md`

## Objective

Export key operational datasets to BigQuery (or a warehouse-compatible format)
so this system can participate in a governed data platform lifecycle.

## Scope

- Define export schemas for:
  - docs
  - ingest_events
  - eval_runs (if implemented)
- Implement export path:
  - direct BigQuery load (preferred)
  - or write Parquet/JSONL to GCS for downstream load
- Document dbt-style modeling notes (raw→curated→marts)

## Non-goals

- No full dbt project in this repo (optional add-on)

## Acceptance criteria

- Export is idempotent
- Export includes basic lineage fields (doc_id, doc_version, content hash)
- Export has governance notes (classification, retention)

## Validation

- Unit tests for schema mapping and export chunking
- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
