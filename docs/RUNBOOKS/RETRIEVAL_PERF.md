# Runbook: Retrieval Performance Profiling (Postgres)

## Scope

This runbook helps operators verify that retrieval queries use the expected Postgres indexes:

- lexical: `idx_chunks_fts` (GIN FTS index)
- vector: `idx_embeddings_vec_hnsw` (pgvector HNSW index)

It is intended for private deployments using Cloud SQL/Postgres.

## Prerequisites

- `DATABASE_URL` points to Postgres
- Postgres migrations are applied (`schema_migrations` is current)
- `pgvector` extension exists
- the database has at least some ingested docs/chunks/embeddings for the tenant being profiled

## How to run

From repo root:

```bash
make profile-retrieval PROFILE_TENANT_ID=default
```

Optional overrides:

```bash
# Profile one explicit query
make profile-retrieval PROFILE_TENANT_ID=default PROFILE_QUERY="Why use Cloud SQL for persistence?"

# Write JSON report (and include raw plan JSON)
make profile-retrieval \
  PROFILE_TENANT_ID=default \
  PROFILE_JSON_OUT=dist/retrieval_profile.json \
  PROFILE_INCLUDE_PLANS=true
```

Underlying command:

```bash
uv run python -m app.cli profile-retrieval --tenant-id default --top-k 40
```

## Output interpretation

The command prints:

- lexical index usage ratio (`idx_chunks_fts` hits / total queries)
- vector index usage ratio (`idx_embeddings_vec_hnsw` hits / total queries)
- per-query summary:
  - `index_used=yes|no`
  - `planning_ms` / `exec_ms`
  - `seq_scans=<relations>`
  - optional `error=...`

### What good looks like

For non-trivial corpora, typical healthy signs are:

- lexical plans include `Bitmap Index Scan` or index usage referencing `idx_chunks_fts`
- vector plans include `Index Scan`/`Index Only Scan` usage of `idx_embeddings_vec_hnsw`
- no persistent `Seq Scan` on `embeddings` for vector retrieval
- stable planning and execution times across representative queries

## Common failure modes

### 1. Lexical path uses sequential scan

Symptoms:

- lexical `index_used=no`
- `seq_scans=chunks`

Likely causes:

- missing or dropped `idx_chunks_fts`
- stale planner stats
- very small corpus where planner prefers seq scan

### 2. Vector path uses sequential scan

Symptoms:

- vector `index_used=no`
- `seq_scans=embeddings`

Likely causes:

- missing/dropped `idx_embeddings_vec_hnsw`
- `pgvector` extension/index mismatch
- stale planner stats
- low row counts where planner still chooses seq scan

### 3. Vector profiling errors

Symptoms:

- per-query vector line includes `error=...`

Likely causes:

- no embeddings for profiled tenant
- vector dimension mismatch after embedding config drift
- malformed `DATABASE_URL` / connectivity issue

## Remediation steps

Run these in psql against the target database.

### Verify indexes

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('idx_chunks_fts', 'idx_embeddings_vec_hnsw');
```

### Verify pgvector extension

```sql
SELECT extname FROM pg_extension WHERE extname = 'vector';
```

### Refresh planner stats

```sql
ANALYZE chunks;
ANALYZE embeddings;
```

### Rebuild indexes (if corruption/suspected drift)

```sql
REINDEX INDEX idx_chunks_fts;
REINDEX INDEX idx_embeddings_vec_hnsw;
```

### Re-run migrations

From app startup path, migrations are auto-applied; for troubleshooting, redeploy and confirm `schema_migrations` includes latest filenames.

## Notes

- In very small corpora, Postgres may legitimately choose seq scans despite existing indexes.
- Tenant profiling should be run with the tenant that reflects real workload (`PROFILE_TENANT_ID=...`).
- Public demo safety posture is unchanged; this is an operator CLI workflow.
