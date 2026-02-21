-- 001_init.sql
-- Base schema for Cloud SQL / Postgres deployments.
-- NOTE: This migration assumes pgvector is available (production baseline).
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS docs (
  doc_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  source TEXT NOT NULL,
  classification TEXT NOT NULL DEFAULT 'public',
  retention TEXT NOT NULL DEFAULT 'indefinite',
  tags_json TEXT NOT NULL DEFAULT '[]',
  content_sha256 TEXT,
  content_bytes BIGINT NOT NULL DEFAULT 0,
  num_chunks INTEGER NOT NULL DEFAULT 0,
  doc_version INTEGER NOT NULL DEFAULT 1,
  created_at BIGINT NOT NULL,
  updated_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
  chunk_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL REFERENCES docs(doc_id) ON DELETE CASCADE,
  idx INTEGER NOT NULL,
  text TEXT NOT NULL
);

-- Embeddings stored as pgvector type (required).
CREATE TABLE IF NOT EXISTS embeddings (
  chunk_id TEXT PRIMARY KEY REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  dim INTEGER NOT NULL,
  vec vector NOT NULL
);

CREATE TABLE IF NOT EXISTS ingest_events (
  event_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL REFERENCES docs(doc_id) ON DELETE CASCADE,
  doc_version INTEGER NOT NULL,
  ingested_at BIGINT NOT NULL,
  content_sha256 TEXT NOT NULL,
  prev_content_sha256 TEXT,
  changed INTEGER NOT NULL,
  num_chunks INTEGER NOT NULL,
  embedding_backend TEXT NOT NULL,
  embeddings_model TEXT NOT NULL,
  embedding_dim INTEGER NOT NULL,
  chunk_size_chars INTEGER NOT NULL,
  chunk_overlap_chars INTEGER NOT NULL,
  schema_fingerprint TEXT,
  contract_sha256 TEXT,
  validation_status TEXT,
  validation_errors_json TEXT,
  schema_drifted INTEGER NOT NULL DEFAULT 0,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
