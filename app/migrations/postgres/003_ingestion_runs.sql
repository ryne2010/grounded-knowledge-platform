-- 003_ingestion_runs.sql
-- Ingestion run grouping + summaries.

ALTER TABLE ingest_events
  ADD COLUMN IF NOT EXISTS run_id TEXT;

CREATE TABLE IF NOT EXISTS ingestion_runs (
  run_id TEXT PRIMARY KEY,
  started_at BIGINT NOT NULL,
  finished_at BIGINT,
  status TEXT NOT NULL,
  trigger_type TEXT NOT NULL,
  trigger_payload_json TEXT NOT NULL DEFAULT '{}',
  principal TEXT,
  objects_scanned INTEGER NOT NULL DEFAULT 0,
  docs_changed INTEGER NOT NULL DEFAULT 0,
  docs_unchanged INTEGER NOT NULL DEFAULT 0,
  bytes_processed BIGINT NOT NULL DEFAULT 0,
  errors_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_events_run_id ON ingest_events(run_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_started_at ON ingestion_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status ON ingestion_runs(status);
