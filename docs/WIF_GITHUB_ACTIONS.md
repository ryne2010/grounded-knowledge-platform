# Workload Identity Federation (WIF) for GitHub Actions

This repo includes GitHub Actions workflows that can run Terraform **without** long-lived service account keys.

Workflows:
- `terraform-hygiene.yml` — fmt/validate/lint/sec/policy (no GCP auth required)
- `gcp-build-and-deploy.yml` — push to `main` → Cloud Build image → Terraform deploy (Cloud Run)
- `gcp-terraform-plan.yml` — plan on demand (workflow_dispatch)
- `terraform-apply-gcp.yml` — apply on demand (workflow_dispatch)
- `terraform-drift.yml` — scheduled drift detection (plan -detailed-exitcode)

---

## 1) Create WIF + CI service account

This repo includes a small bootstrap root you can run directly:
- `infra/gcp/wif_bootstrap/`

It creates:
- a CI service account (or reuses one you provide)
- a Workload Identity Pool + Provider for your `OWNER/REPO`
- bucket access needed to download config + manage state

### Bootstrap commands (manual)

Assumptions:
- You already created your tfstate bucket (example: `<project>-tfstate`)
- You already created (or will create) your config bucket (example: `<project>-config`)

```bash
PROJECT_ID="your-project-id"
TFSTATE_BUCKET="${PROJECT_ID}-tfstate"

terraform -chdir=infra/gcp/wif_bootstrap init -reconfigure \
  -backend-config="bucket=${TFSTATE_BUCKET}" \
  -backend-config="prefix=gkp/wif_bootstrap"

terraform -chdir=infra/gcp/wif_bootstrap apply -auto-approve \
  -var "project_id=${PROJECT_ID}" \
  -var "github_repository=OWNER/REPO" \
  -var "config_bucket_name=${PROJECT_ID}-config" \
  -var "tfstate_bucket_name=${TFSTATE_BUCKET}"
```

Grab outputs for GitHub:

```bash
terraform -chdir=infra/gcp/wif_bootstrap output -raw workload_identity_provider
terraform -chdir=infra/gcp/wif_bootstrap output -raw ci_service_account_email
```

Gotcha:

- If `terraform output` says **“No outputs found”**, you almost always haven’t applied this root (or you’re pointed at the wrong state).
  - Make sure you ran `terraform init` for this root with a real backend config (bucket + prefix), then `terraform apply`.
  - Quick sanity check: `terraform -chdir=infra/gcp/wif_bootstrap state list | head`

### 1b) Grant the CI service account permissions to run Terraform

WIF only answers **how** GitHub authenticates. You still need to decide **what** it is allowed to do.

For this repo’s `infra/gcp/cloud_run_demo` stack, the CI service account must be able to:
- create/update Cloud Run, Monitoring, Logging, Artifact Registry resources
- (optionally) enable project APIs (Service Usage)
- set some project IAM bindings (runtime service account roles, optional group access)

Fastest (personal sandbox):

```bash
PROJECT_ID="your-project-id"
CI_SA_EMAIL="$(terraform -chdir=infra/gcp/wif_bootstrap output -raw ci_service_account_email)"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${CI_SA_EMAIL}" \
  --role="roles/owner"
```

IAM prompt gotcha:
- If `gcloud` prompts you to select an IAM condition (because your project already has conditional bindings),
  choose **`None`** to add an unconditional binding.

More “production-ish” (still broad, but avoids full Owner):

```bash
PROJECT_ID="your-project-id"
CI_SA_EMAIL="$(terraform -chdir=infra/gcp/wif_bootstrap output -raw ci_service_account_email)"

: "These are common building blocks for Terraform in a single-project demo."
: "Adjust as needed if you disable observability/log views."
for ROLE in \
  roles/cloudbuild.builds.editor \
  roles/run.admin \
  roles/artifactregistry.admin \
  roles/monitoring.admin \
  roles/logging.configWriter \
  roles/serviceusage.serviceUsageAdmin \
  roles/resourcemanager.projectIamAdmin \
  roles/iam.serviceAccountAdmin \
  roles/iam.serviceAccountUser
do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${CI_SA_EMAIL}" \
    --role="${ROLE}"
done
```

Teaching point:
- In mature orgs, Terraform often runs under a tightly-controlled “platform automation” identity that is powerful within a constrained scope (project/folder), and every change is gated by PR review + audit logs.

---

## 2) Configure GitHub Actions Variables

Recommended: use **GitHub Environments** (`dev`, `stage`, `prod`) so:
- `prod` can require approvals
- each environment can point at its own GCS config path

GitHub → Settings → **Environments** → (create/select `dev`, `stage`, `prod`) → **Environment variables**

Set:

### WIF variables
- `GCP_WIF_PROVIDER`
  Example: `projects/123456789/locations/global/workloadIdentityPools/my-pool/providers/github`

- `GCP_WIF_SERVICE_ACCOUNT`
  Example: `ci-terraform@my-project.iam.gserviceaccount.com`

### Single-source-of-truth config (GCS)

This repo’s workflows can fetch Terraform configuration from GCS at runtime so you don’t have to
duplicate `PROJECT_ID`, `REGION`, state bucket names, image URIs, etc. across GitHub variables.

Create (or reuse) a **config bucket** (separate from your tfstate bucket):

```bash
PROJECT_ID="your-project-id"
REGION="us-central1"

gcloud storage buckets create "gs://${PROJECT_ID}-config" \
  --location="${REGION}" \
  --uniform-bucket-level-access \
  --public-access-prevention
gcloud storage buckets update "gs://${PROJECT_ID}-config" --versioning
```

Put per-environment config files at that path (`backend.hcl` + `terraform.tfvars`).

- If you follow the GCS-first flow, `docs/MANUAL_DEPLOY_GCP_CLOUD_RUN.md` step **1c** creates these objects directly in GCS.
- If you already have local files (ignored by git), you can upload them:

```bash
ENV="dev"
TF_DIR="infra/gcp/cloud_run_demo"

gcloud storage cp "${TF_DIR}/backend.hcl" "gs://${PROJECT_ID}-config/gkp/${ENV}/backend.hcl"
gcloud storage cp "${TF_DIR}/terraform.tfvars" "gs://${PROJECT_ID}-config/gkp/${ENV}/terraform.tfvars"
```

Then set ONE environment variable per GitHub Environment:
- `GCP_TF_CONFIG_GCS_PATH`
  Example: `gs://your-project-id-config/gkp/dev`

> The workflows expect that path to contain `backend.hcl` and `terraform.tfvars`.

IAM gotcha:
- The CI service account must be able to **read** the config objects:
  - grant `roles/storage.objectViewer` on the config bucket (or object prefix)
- If you use the automated deploy workflow (`gcp-build-and-deploy.yml`), the CI service account must also be able to **write** config objects:
  - grant `roles/storage.objectAdmin` on the config bucket (or just the specific config prefix)
- It must also be able to **read/write** Terraform state in the tfstate bucket referenced by `backend.hcl`.

---

## 3) Run an apply

Actions → **terraform-apply-gcp** → Run workflow → env: `dev`

If you configure GitHub **Environments** (`dev`, `stage`, `prod`), you can require approvals for applies (recommended).

---

## 4) Push → build → deploy (automatic)

This repo includes an automated workflow:
- `.github/workflows/gcp-build-and-deploy.yml`

What it does (high level):
1. Auths to GCP via WIF (no keys)
2. Downloads `backend.hcl` + `terraform.tfvars` from `GCP_TF_CONFIG_GCS_PATH`
3. Bootstraps prerequisite infra (APIs + Artifact Registry + runtime service account)
4. Builds + pushes an immutable image tag via Cloud Build (`sha-${GITHUB_SHA}`)
5. Updates `image_tag` in `terraform.tfvars` **in GCS** (single source of truth)
6. Runs `terraform apply` to deploy to Cloud Run
7. Verifies `/health` and `/api/meta`

Enable it:
- Set the GitHub Environment variables in section (2)
- Ensure the CI service account has permissions (section 1b)
- Push/merge to `main`

Notes:
- The WIF provider created by `infra/gcp/wif_bootstrap` is branch-restricted by default (`main` only).
- If you want `dev` to deploy from a non-main branch, update `allowed_branches` (or loosen the provider condition).

## Security notes

- Do **not** use downloadable service account keys for CI.
- Prefer WIF + short-lived tokens.
- Keep the CI service account least-privilege, and separate state prefixes per env.
