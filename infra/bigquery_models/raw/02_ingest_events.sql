-- Raw layer: ingest events
-- Replaces placeholders:
--   {{PROJECT_ID}}, {{OPS_DATASET}}, {{RAW_DATASET}}, {{TABLE_PREFIX}}

CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{RAW_DATASET}}`;

CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{RAW_DATASET}}.raw_ingest_events`
PARTITION BY ingested_date
CLUSTER BY doc_id, classification, validation_status AS
SELECT
  event_id,
  doc_id,
  doc_version,
  content_sha256,
  prev_content_sha256,
  changed,
  num_chunks,
  embedding_backend,
  embeddings_model,
  embedding_dim,
  chunk_size_chars,
  chunk_overlap_chars,
  classification,
  retention,
  tags,
  schema_fingerprint,
  contract_sha256,
  validation_status,
  validation_errors,
  ARRAY_LENGTH(validation_errors) AS validation_error_count,
  schema_drifted,
  run_id,
  notes,
  TIMESTAMP_SECONDS(ingested_at) AS ingested_ts,
  DATE(TIMESTAMP_SECONDS(ingested_at)) AS ingested_date,
  CURRENT_TIMESTAMP() AS modeled_at
FROM `{{PROJECT_ID}}.{{OPS_DATASET}}.{{TABLE_PREFIX}}ingest_events`;
