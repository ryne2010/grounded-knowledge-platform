variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "github_repository" {
  type        = string
  description = "GitHub repository in OWNER/REPO format."
}

variable "allowed_branches" {
  type        = list(string)
  description = "Allowed GitHub branches for OIDC auth (e.g., ['main']). Empty list means any branch."
  default     = ["main"]
}

variable "ci_service_account_email" {
  type        = string
  description = "Optional existing CI service account email. If set, this root will not create a new service account."
  default     = ""
}

variable "ci_service_account_id" {
  type        = string
  description = "CI service account ID (used only when creating a new service account)."
  default     = "sa-gkp-ci"
}

variable "ci_service_account_display_name" {
  type        = string
  description = "CI service account display name (used only when creating a new service account)."
  default     = "GKP CI (Terraform)"
}

variable "wif_pool_id" {
  type        = string
  description = "Workload Identity Pool ID."
  default     = "github-pool"
}

variable "wif_provider_id" {
  type        = string
  description = "Workload Identity Provider ID."
  default     = "github-provider"
}

variable "config_bucket_name" {
  type        = string
  description = "GCS bucket name that stores backend.hcl + terraform.tfvars for CI (example: <project>-config)."
}

variable "enable_config_bucket_write" {
  type        = bool
  description = "If true, grant the CI service account roles/storage.objectAdmin on the config bucket (lets CI update terraform.tfvars during deploy)."
  default     = true
}

variable "tfstate_bucket_name" {
  type        = string
  description = "GCS bucket name used for Terraform remote state (example: <project>-tfstate)."
}
