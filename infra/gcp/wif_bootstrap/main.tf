locals {
  create_ci_service_account = var.ci_service_account_email == ""
}

resource "google_service_account" "ci" {
  count = local.create_ci_service_account ? 1 : 0

  project      = var.project_id
  account_id   = var.ci_service_account_id
  display_name = var.ci_service_account_display_name
}

locals {
  ci_service_account_email = local.create_ci_service_account ? google_service_account.ci[0].email : var.ci_service_account_email
  ci_member                = "serviceAccount:${local.ci_service_account_email}"
}

module "github_oidc" {
  source = "../modules/github_oidc"

  project_id            = var.project_id
  service_account_email = local.ci_service_account_email
  github_repository     = var.github_repository
  allowed_branches      = var.allowed_branches
  pool_id               = var.wif_pool_id
  provider_id           = var.wif_provider_id
}

# Allow CI (via WIF) to download backend.hcl + terraform.tfvars from the config bucket.
resource "google_storage_bucket_iam_member" "config_reader" {
  bucket = var.config_bucket_name
  role   = "roles/storage.objectViewer"
  member = local.ci_member
}

# Optional: allow CI to write back updated config (e.g., bump image_tag on deploy).
resource "google_storage_bucket_iam_member" "config_writer" {
  count = var.enable_config_bucket_write ? 1 : 0

  bucket = var.config_bucket_name
  role   = "roles/storage.objectAdmin"
  member = local.ci_member
}

# Allow CI (via WIF) to read/write Terraform state in the state bucket used by your backends.
resource "google_storage_bucket_iam_member" "tfstate_rw" {
  bucket = var.tfstate_bucket_name
  role   = "roles/storage.objectAdmin"
  member = local.ci_member
}
