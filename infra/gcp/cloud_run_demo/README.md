# Cloud Run deployment (Terraform) — Grounded Knowledge Platform

This Terraform root deploys the **Grounded Knowledge Platform** API to **Cloud Run** using the same “platform baseline” patterns used across the portfolio.

What this demonstrates (staff-level):
- **Remote Terraform state** (GCS backend)
- **Plan/apply separation** (PR-friendly)
- **Safe public demo defaults** (`PUBLIC_DEMO_MODE=1`, no uploads, extractive-only)
- Optional **private service IAM** via `allow_unauthenticated=false` + `private_invoker_members`
- Optional **Secret Manager env wiring** via `secret_env` (no plaintext keys in tfvars)
- **Scale-to-zero** (min instances 0)
- **Cost guardrails** (max instances cap)
- macOS-friendly **Cloud Build** based image builds
- Optional (disabled by default): **Serverless VPC Access connector**
- Optional (disabled by default): **Cloud SQL Postgres** persistence
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

## Optional: VPC connector

If you want to demonstrate private networking (Cloud Run → private IP resources), enable `enable_vpc_connector`.

> Note: Serverless VPC Access connectors are not free.

---

## Optional: Cloud SQL Postgres

Enable persistent Postgres storage:

```hcl
enable_cloudsql   = true
cloudsql_database = "gkp"
cloudsql_user     = "gkp_app"
```

This stack will:
- create a Cloud SQL Postgres instance + DB + user
- mount the Cloud SQL connection into Cloud Run at `/cloudsql`
- inject `DATABASE_URL` for app runtime

Runbook: `docs/RUNBOOKS/CLOUDSQL.md`
