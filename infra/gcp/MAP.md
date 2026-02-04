# Infra map (what’s “in play”)

This repo intentionally includes a **deployable Cloud Run stack** plus a small set of “baseline-style” Terraform modules and CI workflows.
This map answers: *what is actively used vs included for reference*.

---

## The deployable stack (used)

**Terraform root (entrypoint)**
- `infra/gcp/cloud_run_demo/` — deploys the app to Cloud Run with demo-safe defaults.
- `infra/gcp/wif_bootstrap/` — bootstraps GitHub Actions → GCP Workload Identity Federation (WIF) + CI service account access to config/state buckets.

**Terraform resources created by the root**
- Cloud Run service + IAM (public demo by default)
- Artifact Registry repo (+ optional cleanup policy)
- Runtime service account + roles
- Observability-as-code (dashboards, alerts, log routing/log views, SLOs)
- Optional: VPC + Serverless VPC Access connector (`enable_vpc_connector = true`)
- Optional: Google Group IAM bindings (workspace groups or single `@googlegroups.com` viewer group)

**Terraform modules invoked by `cloud_run_demo`**
- `infra/gcp/modules/core_services/` — enables required APIs
- `infra/gcp/modules/artifact_registry/` — creates Artifact Registry repo
- `infra/gcp/modules/service_accounts/` — creates runtime service account
- `infra/gcp/modules/cloud_run_service/` — creates Cloud Run v2 service + (optional) public invoker binding
- `infra/gcp/modules/network/` — optional VPC + subnets + optional serverless connector

---

## Terraform modules invoked by `wif_bootstrap`

- `infra/gcp/modules/github_oidc/` — creates GitHub Actions → GCP Workload Identity Federation (WIF) (pool + provider + IAM bindings)

---

## Included baseline modules (not used by any root today)

- `infra/gcp/modules/secret_manager/` — creates Secret Manager **secret containers** only (no secret values in TF state)
  - Not called by `cloud_run_demo/` (the demo defaults avoid external secrets)

---

## Policy / guardrails (used by CI)

- `infra/gcp/policy/terraform.rego` — small Conftest policy gate for Terraform examples
  - Enforced by `.github/workflows/terraform-hygiene.yml`

---

## GitHub Actions workflows (used)

**App CI**
- `.github/workflows/ci.yml` — Python + web build/lint smoke checks (no GCP)

**Terraform hygiene**
- `.github/workflows/terraform-hygiene.yml` — fmt/validate + tflint/tfsec/checkov/conftest (no GCP auth required)

**Terraform plan/apply (GCP via WIF + GCS config)**
- `.github/workflows/gcp-build-and-deploy.yml` — push to `main` → build image (Cloud Build) → `terraform apply` (deploy)
- `.github/workflows/gcp-terraform-plan.yml` — manual `terraform plan`
- `.github/workflows/terraform-apply-gcp.yml` — manual `terraform apply` (can be approval-gated via GitHub Environments)
- `.github/workflows/terraform-drift.yml` — scheduled drift detection (`plan -detailed-exitcode`)

These workflows assume a **single source of truth** in GCS:
- `GCP_TF_CONFIG_GCS_PATH` (example: `gs://<project>-config/gkp/dev`)
  - must contain `backend.hcl` and `terraform.tfvars`

See:
- `docs/WIF_GITHUB_ACTIONS.md`
- `docs/DRIFT_DETECTION.md`
