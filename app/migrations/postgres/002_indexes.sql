-- 002_indexes.sql
-- Performance-oriented indexes for Postgres baseline.

CREATE INDEX IF NOT EXISTS idx_docs_updated_at ON docs(updated_at);
CREATE INDEX IF NOT EXISTS idx_events_ingested_at ON ingest_events(ingested_at);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_idx ON chunks(doc_id, idx);

-- Lexical retrieval (Postgres full-text search)
CREATE INDEX IF NOT EXISTS idx_chunks_fts ON chunks USING GIN (to_tsvector('english', text));

-- Vector retrieval (pgvector)
-- For small corpora, exact search is fine; this index is the production baseline.
DO $$
BEGIN
  -- pgvector HNSW indexes require a dimensioned column type (vector(n)).
  -- When vec is declared as unbounded vector, skip index creation to avoid
  -- hard-failing startup migrations.
  IF EXISTS (
    SELECT 1
    FROM pg_attribute
    WHERE attrelid = 'embeddings'::regclass
      AND attname = 'vec'
      AND atttypmod > 0
  ) THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_embeddings_vec_hnsw ON embeddings USING hnsw (vec vector_cosine_ops)';
  ELSE
    RAISE NOTICE 'Skipping idx_embeddings_vec_hnsw: embeddings.vec is not vector(n).';
  END IF;
END
$$;
