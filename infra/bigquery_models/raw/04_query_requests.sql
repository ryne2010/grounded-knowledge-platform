-- Raw layer: query request logs (optional)
-- This model is for Cloud Logging sink data and provides a query-latency proxy.
-- Replaces placeholders:
--   {{PROJECT_ID}}, {{LOGS_DATASET}}, {{REQUEST_LOG_TABLE}}, {{RAW_DATASET}}

CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{RAW_DATASET}}`;

CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{RAW_DATASET}}.raw_query_requests`
PARTITION BY event_date
CLUSTER BY path, http_status AS
SELECT
  CAST(jsonPayload.request_id AS STRING) AS request_id,
  CAST(jsonPayload.path AS STRING) AS path,
  SAFE_CAST(jsonPayload.latency_ms AS FLOAT64) AS latency_ms,
  SAFE_CAST(httpRequest.status AS INT64) AS http_status,
  CAST(jsonPayload.limited AS BOOL) AS rate_limited,
  CAST(severity AS STRING) AS severity,
  TIMESTAMP(timestamp) AS event_ts,
  DATE(TIMESTAMP(timestamp)) AS event_date,
  CURRENT_TIMESTAMP() AS modeled_at
FROM `{{PROJECT_ID}}.{{LOGS_DATASET}}.{{REQUEST_LOG_TABLE}}`
WHERE CAST(jsonPayload.path AS STRING) IN ("/api/query", "/api/query/stream");
