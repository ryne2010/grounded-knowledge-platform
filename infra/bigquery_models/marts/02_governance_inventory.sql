-- Mart layer: governance inventory by classification and retention
-- Replaces placeholders:
--   {{PROJECT_ID}}, {{CURATED_DATASET}}, {{MARTS_DATASET}}

CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{MARTS_DATASET}}`;

CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{MARTS_DATASET}}.marts_governance_inventory`
PARTITION BY snapshot_date
CLUSTER BY classification, retention AS
SELECT
  snapshot_date,
  classification,
  retention,
  COUNT(*) AS doc_count,
  AVG(hours_since_last_ingest) AS avg_hours_since_last_ingest,
  COUNTIF(schema_drifted) AS docs_with_schema_drift,
  COUNTIF(validation_status = "fail") AS docs_with_validation_failures,
  CURRENT_TIMESTAMP() AS modeled_at
FROM `{{PROJECT_ID}}.{{CURATED_DATASET}}.curated_ingestion_freshness`
GROUP BY snapshot_date, classification, retention;
