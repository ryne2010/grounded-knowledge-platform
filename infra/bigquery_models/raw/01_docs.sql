-- Raw layer: docs
-- Replaces placeholders:
--   {{PROJECT_ID}}, {{OPS_DATASET}}, {{RAW_DATASET}}, {{TABLE_PREFIX}}

CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{RAW_DATASET}}`;

CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{RAW_DATASET}}.raw_docs`
PARTITION BY updated_date
CLUSTER BY classification, retention, doc_id AS
SELECT
  doc_id,
  title,
  source,
  classification,
  retention,
  tags,
  content_sha256,
  content_bytes,
  num_chunks,
  doc_version,
  TIMESTAMP_SECONDS(created_at) AS created_ts,
  DATE(TIMESTAMP_SECONDS(created_at)) AS created_date,
  TIMESTAMP_SECONDS(updated_at) AS updated_ts,
  DATE(TIMESTAMP_SECONDS(updated_at)) AS updated_date,
  CURRENT_TIMESTAMP() AS modeled_at
FROM `{{PROJECT_ID}}.{{OPS_DATASET}}.{{TABLE_PREFIX}}docs`;
