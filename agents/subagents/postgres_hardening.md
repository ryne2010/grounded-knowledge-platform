# Sub-agent: Postgres / Cloud SQL hardening

You are hardening the Postgres path so Cloud SQL is a **production baseline**.

## Mission

- deterministic migrations with tracking
- scalable retrieval that avoids loading the full corpus into memory
- (optional) pgvector phased support
- reliable local integration tests (Docker)

## Constraints (must follow)

- Keep changes compatible with Cloud Run.
- Do not introduce multi-tenant complexity.
- Public demo mode remains safe-by-default.

## Hotspots

- `app/storage.py` (Postgres init + query helpers)
- `app/migrations/postgres/*.sql`
- `app/retrieval.py` (Postgres retrieval strategy)
- `tests/test_cloudsql_postgres.py`
- `docs/RUNBOOKS/CLOUDSQL.md`

## Working style

- Prefer idempotent SQL migrations.
- Add indexes only with a clear query-path rationale.
- Add a small amount of instrumentation (timing logs) around retrieval.

## Validation

- `make db-up`
- `make test-postgres`
