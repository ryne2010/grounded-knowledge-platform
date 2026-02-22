-- Raw layer: eval runs
-- Replaces placeholders:
--   {{PROJECT_ID}}, {{OPS_DATASET}}, {{RAW_DATASET}}, {{TABLE_PREFIX}}

CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{RAW_DATASET}}`;

CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{RAW_DATASET}}.raw_eval_runs`
PARTITION BY started_date
CLUSTER BY dataset_name, status AS
SELECT
  run_id,
  status,
  dataset_name,
  dataset_sha256,
  k,
  include_details,
  app_version,
  embeddings_backend,
  embeddings_model,
  retrieval_config_json,
  provider_config_json,
  summary_json,
  diff_from_prev_json,
  details_json,
  error,
  SAFE_CAST(JSON_VALUE(summary_json, "$.examples") AS INT64) AS summary_examples,
  SAFE_CAST(JSON_VALUE(summary_json, "$.passed") AS INT64) AS summary_passed,
  SAFE_CAST(JSON_VALUE(summary_json, "$.failed") AS INT64) AS summary_failed,
  SAFE_CAST(JSON_VALUE(summary_json, "$.pass_rate") AS FLOAT64) AS summary_pass_rate,
  TIMESTAMP_SECONDS(started_at) AS started_ts,
  DATE(TIMESTAMP_SECONDS(started_at)) AS started_date,
  TIMESTAMP_SECONDS(finished_at) AS finished_ts,
  DATE(TIMESTAMP_SECONDS(finished_at)) AS finished_date,
  CURRENT_TIMESTAMP() AS modeled_at
FROM `{{PROJECT_ID}}.{{OPS_DATASET}}.{{TABLE_PREFIX}}eval_runs`;
