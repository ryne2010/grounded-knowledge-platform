# Cloud Run deployment (Terraform) — Grounded Knowledge Platform

This Terraform root deploys the **Grounded Knowledge Platform** API to **Cloud Run** using the same “platform baseline” patterns used across the portfolio.

What this demonstrates (staff-level):
- **Remote Terraform state** (GCS backend)
- **Plan/apply separation** (PR-friendly)
- **Safe public demo defaults** (`PUBLIC_DEMO_MODE=1`, no uploads, extractive-only)
- Optional **private service IAM** via `allow_unauthenticated=false` + `private_invoker_members`
- Optional **Secret Manager env wiring** via `secret_env` (no plaintext keys in tfvars)
- Optional **Pub/Sub push ingestion plumbing** (topic, DLQ, push subscription, GCS notification)
- Optional **Cloud Scheduler periodic sync** (`POST /api/connectors/gcs/sync`)
- **Scale-to-zero** (min instances 0)
- **Cost guardrails** (max instances cap)
- **Request guardrails** (Cloud Run timeout + per-instance concurrency caps)
- Optional **Billing budget alerts** (project-scoped, threshold-based)
- macOS-friendly **Cloud Build** based image builds
- Optional **Serverless VPC Access connector** (not free; only needed for private IP egress paths)
- **Cloud SQL Postgres** persistence (enabled by default, low-cost profile)
- Optional: **Workspace IAM starter pack** (Google Groups → roles)
- **Observability as code** (small dashboard + alert policies)

---

## Recommended workflow

Use the repo root Makefile:

```bash
make deploy
```

Or use plan/apply separation:

```bash
make plan
make apply
```

More details:
- `../../docs/DEPLOY_GCP.md`
- `../../docs/TEAM_WORKFLOW.md`
- `../../docs/IAM_STARTER_PACK.md`
- `../../docs/OBSERVABILITY.md`

---

## Remote state

This root includes `backend.tf`:

```hcl
terraform { backend "gcs" {} }
```

Backend config (`bucket`/`prefix`) is passed at init time by the Makefile so this code stays environment-agnostic.

---

## Team IAM (Google Groups)

Set `workspace_domain` to enable the in-repo IAM starter pack.

Expected groups (by default):
- `gkp-clients-observers@<domain>`
- `gkp-engineers-min@<domain>`
- `gkp-engineers@<domain>`
- `gkp-auditors@<domain>`
- `gkp-platform-admins@<domain>`

See `docs/IAM_STARTER_PACK.md` for the full role matrix.

---

## VPC connector

By default, Cloud SQL uses the Cloud SQL connector path with public IP and does **not** require Serverless VPC Access.

If you need private IP Cloud SQL connectivity, set `cloudsql_private_ip_enabled=true`. This stack will then create and attach a Serverless VPC Access connector automatically.

You can also enable `enable_vpc_connector=true` when Cloud SQL is disabled and you still need private networking for other resources.

> Note: Serverless VPC Access connectors are not free.

---

## Cloud SQL Postgres (baseline)

Cloud SQL is enabled by default using a low-cost profile.

To disable Cloud SQL entirely (for near-zero DB cost):

```hcl
enable_cloudsql = false
```

This stack will:
- create a Cloud SQL Postgres instance + DB + user
- enable automated backups with retention controls
- optionally enable PITR with transaction-log retention controls
- mount the Cloud SQL connection into Cloud Run at `/cloudsql`
- inject `DATABASE_URL` for app runtime

Runbook: `docs/RUNBOOKS/CLOUDSQL.md`
Backup/restore drill runbook: `docs/RUNBOOKS/BACKUP_RESTORE.md`

Low-cost Cloud SQL defaults in this repo:

```hcl
enable_cloudsql                         = true
cloudsql_edition                        = "ENTERPRISE"
cloudsql_private_ip_enabled             = false
cloudsql_tier                           = "db-f1-micro"
cloudsql_disk_type                      = "PD_HDD"
cloudsql_disk_size_gb                   = 10
cloudsql_retained_backups               = 1
cloudsql_enable_point_in_time_recovery  = false
cloudsql_enable_data_cache              = false
```

For stricter networking or higher durability/performance, override these to your required baseline (for example `cloudsql_private_ip_enabled`, `cloudsql_tier`, `cloudsql_retained_backups`, and PITR settings).

Backup defaults can be tuned in tfvars:

```hcl
cloudsql_backup_start_time              = "03:00" # UTC
cloudsql_retained_backups               = 1
cloudsql_enable_point_in_time_recovery  = false
cloudsql_transaction_log_retention_days = 1
# cloudsql_backup_location              = null
```

---

## Optional: Pub/Sub push ingestion

To wire event-driven ingestion (`POST /api/connectors/gcs/notify`) for private deployments:

```hcl
allow_unauthenticated     = false
enable_pubsub_push_ingest = true
pubsub_push_bucket        = "my-bucket"
pubsub_push_prefix        = "knowledge/"
```

You must also run the app in private mode (`PUBLIC_DEMO_MODE=0`) and enable connectors (`ALLOW_CONNECTORS=1`) via `app_env_overrides`.

---

## Optional: Cloud Scheduler periodic sync

To run connector sync on a schedule for private deployments:

```hcl
allow_unauthenticated = false

app_env_overrides = {
  PUBLIC_DEMO_MODE = "0"
  ALLOW_CONNECTORS = "1"
  AUTH_MODE        = "api_key" # or "none" when relying only on Cloud Run IAM
}

enable_scheduler_sync      = true
scheduler_sync_schedule    = "0 * * * *"
scheduler_sync_bucket      = "my-bucket"
scheduler_sync_prefix      = "knowledge/"
scheduler_sync_max_objects = 200
scheduler_sync_api_key     = "set-admin-key-if-auth-mode-api-key"
```

This stack creates:
- a dedicated scheduler service account
- a `roles/run.invoker` binding on the Cloud Run service
- a Cloud Scheduler HTTP job that posts to `/api/connectors/gcs/sync`

Runbook: `docs/RUNBOOKS/CONNECTORS_GCS.md`

---

## Cost guardrail knobs

Built-in defaults are tuned for public demo safety/cost hygiene:

- `min_instances = 0`
- `max_instances = 1`
- `max_request_concurrency = 40`
- `request_timeout_seconds = 30`

Optional billing budget alerts (recommended for shared/public projects):

```hcl
enable_billing_budget = true
billing_account_id    = "billingAccounts/XXXXXX-XXXXXX-XXXXXX" # or raw account id

billing_budget_amount_usd     = 20
billing_budget_alert_thresholds = [0.5, 0.9, 1.0]

# Optional: Cloud Monitoring channels for billing alerts
# billing_budget_monitoring_notification_channels = [
#   "projects/<project>/notificationChannels/<id>",
# ]
```

Budget resource output:

```bash
terraform -chdir=infra/gcp/cloud_run_demo output -raw billing_budget_name
```

Runbook: `docs/RUNBOOKS/COST_INCIDENT.md`

---

## Observability dashboard outputs

After `terraform apply`, you can fetch the dashboard resource directly:

```bash
terraform -chdir=infra/gcp/cloud_run_demo output -raw monitoring_dashboard_name
```

The dashboard covers:
- Cloud Run request count, 5xx, and request latency
- OTEL query-stage latency (retrieval vs answer generation)
- ingestion failures in private deployments (`allow_unauthenticated=false`)
- Cloud SQL health widgets when `enable_cloudsql=true`

For private deployments, the ingestion failure log-based metric name is also exported:

```bash
terraform -chdir=infra/gcp/cloud_run_demo output -raw ingestion_failure_metric_name
```

When `enable_slo=true`, this stack also creates availability + latency SLOs with burn-rate alerts:

```bash
terraform -chdir=infra/gcp/cloud_run_demo output -raw slo_full_name
terraform -chdir=infra/gcp/cloud_run_demo output -raw latency_slo_full_name
terraform -chdir=infra/gcp/cloud_run_demo output -raw alert_policy_slo_burn_rate_availability_name
terraform -chdir=infra/gcp/cloud_run_demo output -raw alert_policy_slo_burn_rate_latency_name
```

Runbook: `docs/RUNBOOKS/SLOS.md`
