# WIF bootstrap (GitHub Actions → GCP, no keys)

This Terraform root bootstraps **Workload Identity Federation (WIF)** for GitHub Actions in your GCP project:

- Creates (or reuses) a **CI service account**
- Creates a **Workload Identity Pool + Provider** for `OWNER/REPO`
- Grants GitHub OIDC permission to impersonate the CI service account (`roles/iam.workloadIdentityUser`)
- Grants the CI service account read access to your **GCS config bucket** (`roles/storage.objectViewer`)
- Optionally grants the CI service account write access to your **GCS config bucket** (`roles/storage.objectAdmin`)
- Grants the CI service account read/write access to your **Terraform state bucket** (`roles/storage.objectAdmin`)

This is intentionally a **separate Terraform root** so you can keep CI identity bootstrapping isolated from
application infrastructure state.

## Inputs you need

- `project_id` — your GCP project ID
- `github_repository` — `OWNER/REPO` (the GitHub repo this will trust)
- `config_bucket_name` — the bucket that stores `backend.hcl` + `terraform.tfvars` (example: `<project>-config`)
- `tfstate_bucket_name` — the bucket referenced by your Terraform backend (example: `<project>-tfstate`)

Optional:
- `allowed_branches` — defaults to `["main"]`
- `ci_service_account_email` — set this to reuse an existing CI service account
- `enable_config_bucket_write` — defaults to `true` (needed for automated “push → build → deploy” that bumps `image_tag` in GCS)

## Typical usage (manual)

Create (or reuse) the tfstate bucket first (one-time), then init with a dedicated prefix:

```bash
# Example: store this root’s state in the same tfstate bucket, isolated by prefix.
terraform -chdir=infra/gcp/wif_bootstrap init -reconfigure \
  -backend-config="bucket=job-search-486101-tfstate" \
  -backend-config="prefix=gkp/wif_bootstrap"
```

Apply:

```bash
terraform -chdir=infra/gcp/wif_bootstrap apply -auto-approve \
  -var "project_id=job-search-486101" \
  -var "github_repository=YOUR_GITHUB_OWNER/YOUR_REPO" \
  -var "config_bucket_name=job-search-486101-config" \
  -var "tfstate_bucket_name=job-search-486101-tfstate"
```

After apply, set these GitHub Environment variables from Terraform outputs:
- `GCP_WIF_PROVIDER`
- `GCP_WIF_SERVICE_ACCOUNT`

Then set:
- `GCP_TF_CONFIG_GCS_PATH` (example: `gs://job-search-486101-config/gkp/dev`)

See `docs/WIF_GITHUB_ACTIONS.md`.
