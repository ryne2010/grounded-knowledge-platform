# BigQuery model examples

This directory contains example SQL models for the warehouse narrative in
`docs/BIGQUERY_MODELING.md`.

Layout:

- `raw/`: typed replicas of exported operational tables + optional query-log source
- `curated/`: operator-facing aggregates (freshness, latency, eval trends)
- `marts/`: KPI-ready rollups for dashboards/BI

The SQL files use placeholders such as `{{PROJECT_ID}}`, `{{RAW_DATASET}}`,
`{{CURATED_DATASET}}`, and `{{MARTS_DATASET}}`.

These are examples, not a full dbt project.
