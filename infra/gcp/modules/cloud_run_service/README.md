# module: cloud_run_service

Deploys a **Cloud Run (v2) service** with optional:
- unauthenticated access (public)
- Secret Manager env vars (latest version)
- Serverless VPC Access connector
- Cloud SQL Unix socket mount (`cloud_sql_instances` -> `/cloudsql`)

Defaults are chosen for low-cost demos:
- `min_instances = 0` (scale to zero)
- modest `max_instances`
- `max_request_concurrency = 40`
- `request_timeout_seconds = 30`

Operational note:
- `deletion_protection` defaults to `false` so demos can be destroyed/replaced cleanly. Set it to `true` for production guardrails.
