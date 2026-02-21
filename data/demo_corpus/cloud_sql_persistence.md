# Cloud SQL Persistence on GCP

Cloud Run local filesystem is ephemeral, so persistent application state belongs in Cloud SQL.

Connection model:
- Use the Cloud SQL Auth path with Unix socket mount on Cloud Run.
- Inject `DATABASE_URL` at runtime.
- Keep credentials in Secret Manager and rotate regularly.

Schema and migration discipline:
- Apply migrations before or with app rollouts.
- Keep migration scripts idempotent where possible.
- Test rollback and forward-only recovery paths.
- Verify connection pool behavior under scale events.

Operational checks:
- Monitor connection saturation, CPU, and storage growth.
- Alert on query latency regressions and lock contention.
- Validate backup policy and restore drill cadence.
- Keep separate stage and prod instances for safe change testing.
