# Cloud SQL (Postgres) Hardening

Status: **Draft** (2026-02-21)

Owner: Repo maintainers

Related tasks:

- `agents/tasks/TASK_CLOUDSQL.md`

## Context

For production deployments, **Cloud SQL / Postgres is the baseline persistence layer**.

As of this iteration:

- **pgvector is part of the production baseline** (not optional)
- the live/public app remains **extractive-only** (no LLM calls)
- each client has **one deployment + one GCP project**

The repo already supports Postgres via `DATABASE_URL`, but we need a baseline that feels “real”:

- versioned, repeatable migrations
- predictable query performance under Cloud Run constraints
- DB-native lexical search + vector search
- local integration testing that matches production

## Goals

1. **Deterministic migrations**
   - SQL migrations applied in order
   - migration tracking table (schema_migrations)
   - safe startup behavior (apply-on-boot is OK for this app)

2. **Retrieval that scales beyond toy demos**
   - lexical search: Postgres full-text search with a GIN index
   - vector search: pgvector cosine distance with a production-grade index (HNSW baseline)

3. **Operational clarity**
   - clear env vars and runbooks
   - health/readiness probes remain lightweight
   - explicit “demo mode” safety posture (no ingestion)

## Non-goals (for this phase)

- multi-region, read replicas, PITR automation
- full multi-tenant data isolation in a single DB (we deploy one project per client)

## Design

### Migration strategy

- `app/migrations/postgres/*.sql` are applied in filename order.
- A `schema_migrations(filename, applied_at)` table records applied migrations.
- Migrations should be:
  - idempotent where possible (`IF NOT EXISTS`)
  - safe under repeat deploys

### Storage schema (baseline)

- docs: metadata, lineage pointers, content hash
- chunks: doc_id + idx + extracted text
- embeddings: pgvector vector column
- ingest_events: lineage, drift + contract validation results
- meta: small key/value configuration signatures

### Retrieval

Hybrid retrieval remains:

- lexical: Postgres FTS (plainto_tsquery + ts_rank_cd)
- vector: pgvector cosine distance
- combine: average of normalized lexical + vector scores

### Local dev parity

Local docker Postgres should include pgvector so local behavior matches Cloud SQL.

## Future hardening ideas (later)

- connection pooling (pgbouncer) if needed
- query plan profiling + pg_stat_statements
- vector index tuning parameters (lists/probes or HNSW M/ef)

