# Task: Harden Cloud SQL (Postgres) baseline (pgvector required)

Spec: `docs/SPECS/CLOUDSQL_HARDENING.md`

Owner: @codex
Suggested sub-agent: `agents/subagents/postgres_hardening.md`

## Goal

Cloud SQL (Postgres) is the **production persistence baseline** for this repo (Cloud Run demo + client deployments).

As of this iteration, **pgvector is required** for Postgres deployments (and local Postgres should mirror that).

This task is about hardening the Postgres path so it feels production-grade:

- predictable migrations
- indexes + query plans that scale beyond the demo corpus
- DB-native hybrid retrieval (FTS + pgvector)
- repeatable local integration testing

## Current state

- `DATABASE_URL` switches the backend to Postgres
- Postgres schema is created from SQL migrations
- Local docker image should include pgvector (parity with Cloud SQL)

## Deliverables (what “done” means)

1. **Migrations**
   - `schema_migrations` table tracks applied SQL files
   - migrations applied in order on startup and in CI
2. **Retrieval**
   - lexical retrieval uses Postgres FTS + GIN index
   - vector retrieval uses pgvector cosine distance + production-grade index
3. **Testing**
   - docker-based integration tests use a pgvector-enabled Postgres image by default
4. **Docs**
   - runbook for local Postgres + Cloud SQL setup
   - env var reference includes pgvector expectations

## Follow-ons (later)

- connection pooling (pgbouncer) for high concurrency
- query plan profiling and tuning knobs (HNSW/IVFFlat parameters)

## Acceptance criteria

- Postgres migrations are deterministic and tracked via `schema_migrations`.
- Hybrid retrieval works end-to-end on Postgres:
  - FTS candidate generation is indexed (GIN)
  - pgvector similarity search uses a production-grade index (HNSW)
- Local Postgres integration tests run against a pgvector-enabled image.

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
- `make test-postgres`

