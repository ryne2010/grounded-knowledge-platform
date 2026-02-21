# Task: BigQuery modeling notes (raw→curated→marts)

Depends on: `agents/tasks/TASK_BIGQUERY_EXPORT.md`

Spec: `docs/SPECS/BIGQUERY_EXPORT.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/product_planner.md`

## Goal

Make the “data architect” narrative concrete by shipping modeling notes and example SQL:

- how exported operational datasets map to a lakehouse-style model
- example curated views for:
  - ingestion freshness
  - retrieval latency
  - eval pass rates over time

## Requirements

- Add docs:
  - `docs/BIGQUERY_MODELING.md` (new)
  - include raw→curated→marts conventions

- Provide example SQL files:
  - `infra/bigquery_models/raw/*.sql`
  - `infra/bigquery_models/curated/*.sql`
  - `infra/bigquery_models/marts/*.sql`

## Acceptance criteria

- A reader can understand how to operationalize the platform’s datasets in BigQuery.
- Examples are small but realistic (partitioning, clustering, naming conventions).

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`

