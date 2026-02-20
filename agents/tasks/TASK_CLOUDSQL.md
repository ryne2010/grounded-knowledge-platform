# Task: Migrate SQLite index to Cloud SQL (Postgres + pgvector)

Owner: @codex

## Goal

Make storage **durable** and production-grade for Cloud Run by migrating from ephemeral SQLite to:

- Cloud SQL Postgres
- `pgvector` for embeddings (optional, but recommended)

## Requirements

### Data model

- Port existing tables:
  - docs
  - chunks
  - embeddings
  - ingest_events
  - meta

### Access layer

- introduce a storage interface (repo pattern) so callers do not depend on SQLite SQL
- provide concrete implementations:
  - SQLite (existing)
  - Postgres (new)

### Migrations

- Alembic or SQL migration scripts
- ability to bootstrap demo corpus into Postgres

### Deployment

- Terraform updates:
  - create Cloud SQL instance + database + user
  - connect Cloud Run to Cloud SQL via connector
  - configure `DATABASE_URL`

### Performance

- indexes for:
  - docs.updated_at
  - ingest_events.ingested_at
  - FTS equivalent (either pg_trgm, tsvector, or keep lexical search in app)

## Non-goals (for first iteration)

- multi-tenant isolation
- document blob storage in GCS (can be follow-up)

## Tests

- add integration tests with a local Postgres container
- verify:
  - ingest creates doc + chunks + embeddings + ingest event
  - query returns citations
  - delete cascades

## Docs

- update README with persistence story
- add `docs/RUNBOOKS/CLOUDSQL.md`
