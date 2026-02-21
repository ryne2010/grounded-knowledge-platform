# BigQuery Lakehouse Pattern

A common GCP analytics pattern is a three-layer lakehouse model in BigQuery.

Layers:
- Bronze: raw append-only ingestion tables.
- Silver: cleaned, standardized, and conformed models.
- Gold: business-facing marts optimized for BI and product analytics.

Engineering conventions:
- Partition by event date and cluster by high-cardinality filter keys.
- Enforce naming standards for datasets, tables, and views.
- Keep transformation SQL in version control.
- Use scheduled validation checks for freshness and null/uniqueness constraints.

Cost and performance:
- Prefer selective projections over `SELECT *` in serving queries.
- Prune partitions with explicit date predicates.
- Materialize expensive intermediate steps when repeatedly reused.
- Track query bytes scanned and slot usage in ops dashboards.
