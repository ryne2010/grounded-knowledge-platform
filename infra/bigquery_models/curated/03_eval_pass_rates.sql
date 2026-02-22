-- Curated layer: eval pass-rate trends by run date and dataset
-- Replaces placeholders:
--   {{PROJECT_ID}}, {{RAW_DATASET}}, {{CURATED_DATASET}}

CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{CURATED_DATASET}}`;

CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{CURATED_DATASET}}.curated_eval_pass_rates`
PARTITION BY run_date
CLUSTER BY dataset_name, status AS
SELECT
  started_date AS run_date,
  dataset_name,
  status,
  COUNT(*) AS run_count,
  SUM(summary_examples) AS total_examples,
  SUM(summary_passed) AS total_passed,
  SUM(summary_failed) AS total_failed,
  SAFE_DIVIDE(SUM(summary_passed), NULLIF(SUM(summary_examples), 0)) AS pass_rate
FROM `{{PROJECT_ID}}.{{RAW_DATASET}}.raw_eval_runs`
GROUP BY run_date, dataset_name, status;
