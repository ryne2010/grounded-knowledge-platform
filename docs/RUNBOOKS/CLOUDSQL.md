# Runbook: Cloud SQL (Postgres) for GKP

## Scope

This runbook covers operating Cloud SQL Postgres for durable storage in Cloud Run deployments.

In this repo, **Cloud SQL (Postgres) is the production baseline**. The app can fall back to SQLite for local/demo use, but public Cloud Run deployments are expected to use Cloud SQL.

Runtime behavior:
- when `DATABASE_URL` is set to a Postgres DSN, API/ingest/retrieval paths use Postgres at runtime
- Postgres deployments require pgvector support (`CREATE EXTENSION vector`)
- when `DATABASE_URL` is unset, the app uses SQLite (`SQLITE_PATH`)

## Preconditions

- Terraform root: `infra/gcp/cloud_run_demo`
- Cloud Run service deployed from this repo
- Private deployment (`PUBLIC_DEMO_MODE=0`) recommended for mutable data

## Cloud SQL in Terraform

Cloud SQL is **enabled by default** in `infra/gcp/cloud_run_demo` via `enable_cloudsql = true` (default).

If you want to disable Cloud SQL (cost/experimentation), set:

```hcl
enable_cloudsql = false
```

Apply:

```bash
make apply ENV=dev
```

When Cloud SQL is enabled, expected outcome:
- Cloud SQL instance + DB + user created
- Private IP connectivity is configured for Cloud SQL
- Serverless VPC Access connector is created/attached for Cloud Run
- Cloud Run mounts Cloud SQL socket at `/cloudsql`
- `DATABASE_URL` injected into Cloud Run env
- `/api/meta` reports `"database_backend": "postgres"`

Backup defaults in this repo:
- automated backups are enabled
- backup start time is configurable (`cloudsql_backup_start_time`)
- retained backups are configurable (`cloudsql_retained_backups`)
- PITR is enabled by default (`cloudsql_enable_point_in_time_recovery=true`)
- transaction log retention is configurable (`cloudsql_transaction_log_retention_days`)

Backup/restore and restore-drill workflow:
- `docs/RUNBOOKS/BACKUP_RESTORE.md`

## Schema bootstrap

Repository migration SQL:
- `app/migrations/postgres/*.sql` (applied in filename order)

Migration tracking:
- applied filenames are recorded in `schema_migrations(filename, applied_at)`
- migrations are applied automatically on startup for Postgres connections (`init_db`)

Hardening roadmap/spec:
- `docs/SPECS/CLOUDSQL_HARDENING.md`

For local verification with Postgres:

```bash
# Optional override (default): GKP_POSTGRES_IMAGE=pgvector/pgvector:0.8.0-pg16-bookworm
make db-up
make test-postgres
```

The test:
- initializes schema
- ingests one doc (doc/chunks/embeddings/ingest_event)
- queries citations
- verifies delete cascade

## Operational checks

After deploy:

1. `make url`
2. `curl <service-url>/ready`
3. `curl <service-url>/api/meta`
4. Confirm app env includes `DATABASE_URL`
5. Confirm Cloud SQL CPU/storage/connection metrics in Cloud Monitoring

## Failure modes and mitigations

- `Cloud SQL connection failed`:
  - verify Cloud Run service account has `roles/cloudsql.client`
  - verify Cloud SQL instance is RUNNABLE
  - verify socket mount and `DATABASE_URL` path (`/cloudsql/<connection_name>`)

- `Migration/init errors`:
  - run schema SQL manually against target DB
  - check SQL compatibility for current Postgres major version

- `Connection saturation`:
  - lower Cloud Run max instances or add connection pooling layer
  - scale Cloud SQL tier

## Disable / rollback

1. Set `enable_cloudsql = false`
2. Apply Terraform
3. Service falls back to SQLite (`SQLITE_PATH`)

Note: data in Cloud SQL is not migrated back to SQLite automatically.
