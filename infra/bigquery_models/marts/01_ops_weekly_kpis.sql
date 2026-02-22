-- Mart layer: weekly platform KPIs for operator dashboards
-- Replaces placeholders:
--   {{PROJECT_ID}}, {{CURATED_DATASET}}, {{MARTS_DATASET}}

CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{MARTS_DATASET}}`;

CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{MARTS_DATASET}}.marts_ops_weekly_kpis`
PARTITION BY week_start AS
WITH latency AS (
  SELECT
    DATE_TRUNC(event_date, WEEK(MONDAY)) AS week_start,
    SUM(request_count) AS query_request_count,
    AVG(avg_latency_ms) AS avg_query_latency_ms,
    MAX(p95_latency_ms) AS max_p95_query_latency_ms,
    SAFE_DIVIDE(SUM(server_error_count), NULLIF(SUM(request_count), 0)) AS query_server_error_rate
  FROM `{{PROJECT_ID}}.{{CURATED_DATASET}}.curated_retrieval_latency`
  GROUP BY week_start
),
evals AS (
  SELECT
    DATE_TRUNC(run_date, WEEK(MONDAY)) AS week_start,
    SUM(total_examples) AS eval_examples,
    SUM(total_passed) AS eval_passed,
    SUM(total_failed) AS eval_failed,
    SAFE_DIVIDE(SUM(total_passed), NULLIF(SUM(total_examples), 0)) AS eval_pass_rate
  FROM `{{PROJECT_ID}}.{{CURATED_DATASET}}.curated_eval_pass_rates`
  GROUP BY week_start
),
ingest AS (
  SELECT
    DATE_TRUNC(snapshot_date, WEEK(MONDAY)) AS week_start,
    COUNT(*) AS tracked_docs,
    COUNTIF(hours_since_last_ingest <= 24) AS docs_fresh_24h,
    SAFE_DIVIDE(COUNTIF(hours_since_last_ingest <= 24), COUNT(*)) AS freshness_ratio_24h,
    COUNTIF(schema_drifted) AS docs_with_schema_drift
  FROM `{{PROJECT_ID}}.{{CURATED_DATASET}}.curated_ingestion_freshness`
  GROUP BY week_start
)
SELECT
  COALESCE(latency.week_start, evals.week_start, ingest.week_start) AS week_start,
  query_request_count,
  avg_query_latency_ms,
  max_p95_query_latency_ms,
  query_server_error_rate,
  eval_examples,
  eval_passed,
  eval_failed,
  eval_pass_rate,
  tracked_docs,
  docs_fresh_24h,
  freshness_ratio_24h,
  docs_with_schema_drift,
  CURRENT_TIMESTAMP() AS modeled_at
FROM latency
FULL OUTER JOIN evals USING (week_start)
FULL OUTER JOIN ingest USING (week_start);
