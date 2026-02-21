-- 005_eval_runs.sql
-- Persisted eval runs for private deployments.

CREATE TABLE IF NOT EXISTS eval_runs (
  run_id TEXT PRIMARY KEY,
  started_at BIGINT NOT NULL,
  finished_at BIGINT,
  status TEXT NOT NULL,
  dataset_name TEXT NOT NULL,
  dataset_sha256 TEXT NOT NULL,
  k INTEGER NOT NULL,
  include_details INTEGER NOT NULL DEFAULT 0,
  app_version TEXT NOT NULL,
  embeddings_backend TEXT NOT NULL,
  embeddings_model TEXT NOT NULL,
  retrieval_config_json TEXT NOT NULL DEFAULT '{}',
  provider_config_json TEXT NOT NULL DEFAULT '{}',
  summary_json TEXT NOT NULL DEFAULT '{}',
  diff_from_prev_json TEXT NOT NULL DEFAULT '{}',
  details_json TEXT NOT NULL DEFAULT '[]',
  error TEXT
);

CREATE INDEX IF NOT EXISTS idx_eval_runs_started_at ON eval_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_eval_runs_status ON eval_runs(status);
CREATE INDEX IF NOT EXISTS idx_eval_runs_dataset_name ON eval_runs(dataset_name);
