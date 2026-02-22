-- 006_tenant_boundary.sql
-- Optional multi-workspace boundary: add tenant scoping columns and indexes.

ALTER TABLE docs
  ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';

ALTER TABLE chunks
  ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';

ALTER TABLE ingest_events
  ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';

ALTER TABLE ingestion_runs
  ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';

UPDATE docs
SET tenant_id = 'default'
WHERE tenant_id IS NULL OR btrim(tenant_id) = '';

UPDATE chunks c
SET tenant_id = d.tenant_id
FROM docs d
WHERE c.doc_id = d.doc_id
  AND (c.tenant_id IS NULL OR btrim(c.tenant_id) = '');

UPDATE ingest_events e
SET tenant_id = d.tenant_id
FROM docs d
WHERE e.doc_id = d.doc_id
  AND (e.tenant_id IS NULL OR btrim(e.tenant_id) = '');

UPDATE ingestion_runs
SET tenant_id = 'default'
WHERE tenant_id IS NULL OR btrim(tenant_id) = '';

CREATE INDEX IF NOT EXISTS idx_docs_tenant ON docs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_docs_tenant_updated_at ON docs(tenant_id, updated_at);

CREATE INDEX IF NOT EXISTS idx_chunks_tenant_doc ON chunks(tenant_id, doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_tenant_doc_idx ON chunks(tenant_id, doc_id, idx);

CREATE INDEX IF NOT EXISTS idx_events_tenant ON ingest_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_events_tenant_doc_ver ON ingest_events(tenant_id, doc_id, doc_version);
CREATE INDEX IF NOT EXISTS idx_events_tenant_ingested_at ON ingest_events(tenant_id, ingested_at);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_tenant_started_at ON ingestion_runs(tenant_id, started_at);
