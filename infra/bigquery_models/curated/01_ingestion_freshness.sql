-- Curated layer: latest ingest freshness by document
-- Replaces placeholders:
--   {{PROJECT_ID}}, {{RAW_DATASET}}, {{CURATED_DATASET}}

CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{CURATED_DATASET}}`;

CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{CURATED_DATASET}}.curated_ingestion_freshness`
PARTITION BY snapshot_date
CLUSTER BY classification, retention, doc_id AS
WITH ranked AS (
  SELECT
    e.*,
    ROW_NUMBER() OVER (
      PARTITION BY e.doc_id
      ORDER BY e.ingested_ts DESC, e.event_id DESC
    ) AS rn
  FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.raw_ingest_events` e
)
SELECT
  CURRENT_DATE() AS snapshot_date,
  doc_id,
  doc_version,
  content_sha256,
  classification,
  retention,
  tags,
  ingested_ts AS latest_ingested_ts,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), ingested_ts, HOUR) AS hours_since_last_ingest,
  changed AS last_ingest_changed,
  schema_drifted,
  validation_status,
  validation_error_count
FROM ranked
WHERE rn = 1;
