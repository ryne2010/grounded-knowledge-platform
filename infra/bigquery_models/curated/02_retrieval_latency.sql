-- Curated layer: retrieval/query latency proxy from query request logs
-- Replaces placeholders:
--   {{PROJECT_ID}}, {{RAW_DATASET}}, {{CURATED_DATASET}}

CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{CURATED_DATASET}}`;

CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{CURATED_DATASET}}.curated_retrieval_latency`
PARTITION BY event_date
CLUSTER BY path AS
SELECT
  event_date,
  path,
  COUNT(*) AS request_count,
  COUNTIF(http_status >= 500) AS server_error_count,
  SAFE_DIVIDE(COUNTIF(http_status >= 500), COUNT(*)) AS server_error_rate,
  AVG(latency_ms) AS avg_latency_ms,
  APPROX_QUANTILES(latency_ms, 100)[OFFSET(50)] AS p50_latency_ms,
  APPROX_QUANTILES(latency_ms, 100)[OFFSET(95)] AS p95_latency_ms,
  APPROX_QUANTILES(latency_ms, 100)[OFFSET(99)] AS p99_latency_ms
FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.raw_query_requests`
WHERE latency_ms IS NOT NULL
GROUP BY event_date, path;
