# Runbook: Cloud SQL (Postgres) for GKP

## Scope

This runbook covers enabling and operating Cloud SQL Postgres for durable storage in Cloud Run deployments.

## Preconditions

- Terraform root: `infra/gcp/cloud_run_demo`
- Cloud Run service deployed from this repo
- Private deployment (`PUBLIC_DEMO_MODE=0`) recommended for mutable data

## Enable Cloud SQL

Set Terraform vars:

```hcl
enable_cloudsql   = true
cloudsql_database = "gkp"
cloudsql_user     = "gkp_app"
```

Apply:

```bash
make apply ENV=dev
```

Expected outcome:
- Cloud SQL instance + DB + user created
- Cloud Run mounts Cloud SQL socket at `/cloudsql`
- `DATABASE_URL` injected into Cloud Run env

## Schema bootstrap

Repository migration SQL:
- `app/migrations/postgres/001_init.sql`

For local verification with Postgres:

```bash
uv run pytest tests/test_cloudsql_postgres.py -q
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

## Rollback

1. Set `enable_cloudsql = false`
2. Apply Terraform
3. Service falls back to SQLite (`SQLITE_PATH`)

Note: data in Cloud SQL is not migrated back to SQLite automatically.
