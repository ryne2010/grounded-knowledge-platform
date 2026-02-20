# Deploy to GCP (Cloud Run + Terraform)

This repo is designed to deploy cleanly to a single GCP project using Terraform + Cloud Run.

## What gets deployed

Infrastructure (Terraform):
- APIs / baseline services
- Artifact Registry
- Cloud Run service (container built and pushed by Cloud Build)
- Observability as code:
  - dashboards + basic alerts
  - service-scoped log bucket + log view (for least-privilege client access)
  - availability SLO + burn-rate alerts

Optional:
- project-level IAM bindings for Google Groups (standalone mode)

---

## 0) Prereqs

On macOS:

- `gcloud`
- `terraform`
- `docker` (optional; used for local lint/sec/policy checks)
- Python 3.11+ (the app)
- Node 18+ (UI tooling, if applicable)

Auth:

```bash
gcloud auth login
gcloud auth application-default login
```

---

## 1) Set your project + region (no env var exports needed)

This repo’s Makefile reads your active gcloud config.

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-central1
```

Sanity check:

```bash
make doctor
```

---

## 2) Deploy (dev)

One command will:
- create the remote state bucket (if missing)
- run Terraform (APIs, AR, SAs, Cloud Run, dashboards, log views, SLOs)
- build + push container via Cloud Build
- verify endpoints

```bash
make deploy ENV=dev
```

---

## 3) (Optional) Enable Google Groups IAM

If you want group-based IAM in this repo (standalone demo mode), set:

```hcl
workspace_domain  = "example.com"
group_prefix      = "gkp"
enable_project_iam = true
```

Recommended for real teams:
- manage project IAM centrally in Repo 3 (`terraform-gcp-platform`)
- keep app repos focused on app-scoped resources

See `docs/IAM_STARTER_PACK.md`.

---

## 3b) (Optional) Private auth on Cloud Run

For private/internal deployments, keep Cloud Run non-public and enable API-key auth in app env:

```hcl
allow_unauthenticated = false
private_invoker_members = [
  "user:you@example.com",
]
secret_env = {
  API_KEY = "gkp-stage-api-key"
}
```

Set environment variables (Cloud Run service or Terraform module env map):

```bash
AUTH_MODE=api_key
PUBLIC_DEMO_MODE=0
OTEL_ENABLED=1
OTEL_TRACES_EXPORTER=gcp_trace
```

Notes:
- `private_invoker_members` keeps the service private while allowing selected users to open it in a browser after Google sign-in.
- Use Secret Manager for `API_KEY` / `API_KEYS_JSON` and map via `secret_env` (never commit keys in tfvars).
- In demo mode (`PUBLIC_DEMO_MODE=1`), auth is always forced off (`AUTH_MODE=none`) and the app stays read-only.

---

## 3c) (Optional) Cloud SQL Postgres persistence

Set Terraform vars:

```hcl
enable_cloudsql   = true
cloudsql_database = "gkp"
cloudsql_user     = "gkp_app"
```

On apply, Terraform provisions Cloud SQL resources and injects `DATABASE_URL` into Cloud Run.
Operational runbook: `docs/RUNBOOKS/CLOUDSQL.md`.

---

## 4) Verify

```bash
make url
make verify
```

---

## 5) Observability

See:
- `docs/OBSERVABILITY.md` (dashboards + alerts + SLOs)
- `docs/IAM_STARTER_PACK.md` (client log view access pattern)

---

## 6) Keyless CI/CD (WIF) + drift detection

This repo includes keyless GitHub Actions workflows (WIF, no long-lived keys):

- `.github/workflows/gcp-build-and-deploy.yml` (push → build image → deploy)
- `.github/workflows/gcp-terraform-plan.yml` (manual plan)
- `.github/workflows/terraform-apply-gcp.yml`
- `.github/workflows/terraform-drift.yml`

Notes:
- `gcp-build-and-deploy.yml` runs on `push` to `main` (and can be run manually). It uses path filters, so doc-only changes won't trigger a deploy.
- `gcp-terraform-plan.yml` and `terraform-apply-gcp.yml` are `workflow_dispatch` (manual) by design.
- `terraform-drift.yml` runs on a weekly schedule and can also be run manually.

To enable:
- Bootstrap WIF with `infra/gcp/wif_bootstrap/`
- Set GitHub Environment variables as described in `docs/WIF_GITHUB_ACTIONS.md`

---

## Cleanup

```bash
make destroy ENV=dev
```

This destroys Terraform-managed resources but **keeps the remote state bucket**.
