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
- macOS-friendly **Cloud Build** based image builds
- **Serverless VPC Access connector** (auto-enabled when Cloud SQL is enabled)
- **Cloud SQL Postgres** persistence (enabled by default)
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

When Cloud SQL is enabled (default), this stack automatically creates and attaches a Serverless VPC Access connector so Cloud Run can reach Cloud SQL over private IP.

You can also enable `enable_vpc_connector=true` when Cloud SQL is disabled and you still need private networking for other resources.

> Note: Serverless VPC Access connectors are not free.

---

## Cloud SQL Postgres (baseline)

Cloud SQL is enabled by default for production-like persistence.

To disable (cost/experimentation):

```hcl
enable_cloudsql = false
```

This stack will:
- create a Cloud SQL Postgres instance + DB + user
- mount the Cloud SQL connection into Cloud Run at `/cloudsql`
- inject `DATABASE_URL` for app runtime

Runbook: `docs/RUNBOOKS/CLOUDSQL.md`

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
