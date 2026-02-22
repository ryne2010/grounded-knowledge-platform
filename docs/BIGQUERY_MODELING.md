# BigQuery Modeling Notes (Raw -> Curated -> Marts)

This guide documents a practical modeling pattern for private deployments after
running the BigQuery export workflow:

- Export runbook: `docs/RUNBOOKS/BIGQUERY_EXPORT.md`
- Export source task: `agents/tasks/TASK_BIGQUERY_EXPORT.md`

The goal is a small but credible analytics story:

- **raw**: typed replicas of exported operational data
- **curated**: operator-focused aggregates and quality signals
- **marts**: KPI-ready tables for dashboards and decision-making

Public demo mode remains out of scope (`PUBLIC_DEMO_MODE=1` disables export).

## Dataset conventions

Use one analytics namespace per private deployment/project:

- `{{OPS_DATASET}}`: direct export tables (for example `gkp_ops.gkp_docs`)
- `{{RAW_DATASET}}`: raw typed layer (for example `gkp_ops_raw`)
- `{{CURATED_DATASET}}`: curated layer (for example `gkp_ops_curated`)
- `{{MARTS_DATASET}}`: mart layer (for example `gkp_ops_marts`)
- `{{LOGS_DATASET}}`: optional Cloud Logging sink dataset for query-latency models

Recommended naming:

- raw tables: `raw_<entity>`
- curated tables: `curated_<subject>`
- marts: `marts_<consumer_view>`

## Partitioning and clustering rules

Use event-time partitioning where available and cluster by frequent filter keys.

- `raw_ingest_events`: `PARTITION BY ingested_date`, `CLUSTER BY doc_id, classification`
- `raw_eval_runs`: `PARTITION BY started_date`, `CLUSTER BY dataset_name, status`
- `raw_query_requests`: `PARTITION BY event_date`, `CLUSTER BY path, http_status`
- `curated_retrieval_latency`: `PARTITION BY event_date`, `CLUSTER BY path`
- `curated_eval_pass_rates`: `PARTITION BY run_date`, `CLUSTER BY dataset_name, status`
- marts tables: typically partition by report window date (`week_start`, `snapshot_date`)

## Source-to-model mapping

Exporter output (`gkp_*`) -> model layers:

- `gkp_docs` -> `raw_docs` -> freshness/governance curations -> governance/ops marts
- `gkp_ingest_events` -> `raw_ingest_events` -> ingestion freshness curation -> ops marts
- `gkp_eval_runs` -> `raw_eval_runs` -> eval pass-rate curation -> ops marts
- Cloud Logging request sink (optional) -> `raw_query_requests` -> retrieval latency curation -> ops marts

## SQL model layout

Example SQL models are stored in:

- `infra/bigquery_models/raw/`
- `infra/bigquery_models/curated/`
- `infra/bigquery_models/marts/`

These files use token placeholders:

- `{{PROJECT_ID}}`
- `{{OPS_DATASET}}`
- `{{RAW_DATASET}}`
- `{{CURATED_DATASET}}`
- `{{MARTS_DATASET}}`
- `{{LOGS_DATASET}}`
- `{{REQUEST_LOG_TABLE}}`
- `{{TABLE_PREFIX}}` (default `gkp_`)

## Operational workflow

1. Run export:
   - `make bigquery-export BQ_JSONL_ONLY=false BQ_PROJECT="$PROJECT_ID" BQ_DATASET="gkp_ops"`
2. Execute raw models (typed, partitioned tables).
3. Execute curated models (freshness/latency/eval trends).
4. Execute marts models (weekly KPIs and governance inventory).
5. Point dashboards/BI tools at `{{MARTS_DATASET}}`.

For scheduled operation:

- keep export cadence at least hourly for operational monitoring
- refresh model layers after each export (or on a fixed schedule)
- monitor row counts and late-arriving data behavior per partition

## Data-quality checks (recommended)

Add lightweight checks in your orchestration tool:

- uniqueness:
  - `raw_docs.doc_id`
  - `raw_ingest_events.event_id`
  - `raw_eval_runs.run_id`
- freshness:
  - max `ingested_date` not older than expected cadence window
- coverage:
  - `curated_retrieval_latency` has rows for `/api/query` when query traffic exists
- integrity:
  - `curated_eval_pass_rates.total_examples >= total_passed + total_failed`

These checks keep analytics trustworthy without introducing heavyweight tooling in
this repository.
