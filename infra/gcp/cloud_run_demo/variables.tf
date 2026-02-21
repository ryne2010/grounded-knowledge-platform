variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "region" {
  type        = string
  description = "GCP region."
  default     = "us-central1"
}

variable "env" {
  type        = string
  description = "Deployment environment label (dev|stage|prod). Used for naming + labels."
  default     = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.env)
    error_message = "env must be one of: dev, stage, prod"
  }
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name. Recommended: gkp-<env> (e.g., gkp-dev)."
  default     = "gkp-dev"
}

variable "artifact_repo_name" {
  type        = string
  description = "Artifact Registry repository name."
  default     = "gkp"
}

variable "image" {
  type        = string
  description = <<EOT
Optional full container image URI (Artifact Registry recommended).

If empty, the image URI is derived from:
- region
- project_id
- artifact_repo_name
- image_name
- image_tag
EOT
  default     = ""
}

variable "image_name" {
  type        = string
  description = "Artifact Registry image name (the part after the repo)."
  default     = "gkp"
}

variable "image_tag" {
  type        = string
  description = <<EOT
Artifact Registry image tag.

Recommended workflow:
- Use immutable tags for deploys (e.g., v2026-02-03-1).
- Optionally ALSO push a floating tag like 'latest' for convenience.
EOT
  default     = "latest"

  validation {
    condition     = length(var.image) > 0 || length(trimspace(var.image_tag)) > 0
    error_message = "Set either image (full URI) or image_tag (when using derived image URI)."
  }
}

variable "allow_unauthenticated" {
  type        = bool
  description = "Whether the Cloud Run service is public. Public demo uses true; production typically uses false + IAM invoker bindings."
  default     = true
}

variable "private_invoker_members" {
  type        = list(string)
  description = "Additional IAM members to grant roles/run.invoker when allow_unauthenticated=false (e.g., [\"user:you@example.com\"])."
  default     = []
}

variable "min_instances" {
  type        = number
  description = "Minimum Cloud Run instances (0 for scale-to-zero)."
  default     = 0
}

variable "max_instances" {
  type        = number
  description = "Maximum Cloud Run instances (cost guardrail)."
  default     = 1
}

variable "deletion_protection" {
  type        = bool
  description = "Enable deletion protection for Cloud Run and Cloud SQL resources (recommended for real client deployments)."
  default     = false
}


variable "enable_vpc_connector" {
  type        = bool
  description = "Create and attach a Serverless VPC Access connector (NOT free)."
  default     = false
}

variable "vpc_egress" {
  type        = string
  description = "VPC egress setting when a connector is attached."
  default     = "PRIVATE_RANGES_ONLY"
}

variable "enable_cloudsql" {
  type        = bool
  description = "Create a Cloud SQL Postgres instance and mount it to Cloud Run (production baseline)."
  default     = true
}

variable "secret_env" {
  type        = map(string)
  description = "Map of Cloud Run env var name -> Secret Manager secret_id (latest version). Example: { API_KEY = \"gkp-stage-api-key\" }"
  default     = {}
}

variable "app_env_overrides" {
  type        = map(string)
  description = "Map of Cloud Run plaintext env overrides merged on top of demo-safe defaults (for private/internal deployments)."
  default     = {}
}

variable "cloudsql_tier" {
  type        = string
  description = "Cloud SQL machine tier."
  default     = "db-custom-1-3840"
}

variable "cloudsql_disk_size_gb" {
  type        = number
  description = "Cloud SQL disk size (GB)."
  default     = 20
}

variable "cloudsql_database" {
  type        = string
  description = "Application database name."
  default     = "gkp"
}

variable "cloudsql_user" {
  type        = string
  description = "Application database user."
  default     = "gkp_app"
}

# --- Workspace / team IAM (Google Groups) ---
# We intentionally keep this optional so you can run a solo demo in a personal project.

variable "workspace_domain" {
  type        = string
  description = <<EOT
Google Workspace / Cloud Identity domain used for group emails (example: "acme.com").

When empty, this module will NOT create any group IAM bindings.
EOT
  default     = ""
}

variable "group_prefix" {
  type        = string
  description = <<EOT
Group name prefix used to build group emails (example: "gkp").

Groups expected (if workspace_domain is set):
- <prefix>-clients-observers@<domain>
- <prefix>-engineers-min@<domain>
- <prefix>-engineers@<domain>
- <prefix>-auditors@<domain>
- <prefix>-platform-admins@<domain>
EOT
  default     = "gkp"
}

variable "clients_observers_group_email" {
  type        = string
  description = <<EOT
Optional override for the "clients-observers" group email.

Use this when you don't have a Workspace/Cloud Identity domain but still want to demonstrate
group-based IAM (example: "job-search-ryne@googlegroups.com").

When set, this takes precedence over workspace_domain/group_prefix for the clients-observers group only.
EOT
  default     = ""
}

variable "enable_clients_observers_monitoring_viewer" {
  type        = bool
  description = <<EOT
If true, grant roles/monitoring.viewer to the clients-observers group.

This is useful for a demo project so a "viewer" group can see dashboards without enabling the full
project-level IAM starter pack.
EOT
  default     = false
}

# --- Observability as code ---

variable "enable_observability" {
  type        = bool
  description = "Whether to create a small Cloud Monitoring dashboard + alert policies for the Cloud Run service."
  default     = true
}

variable "notification_channels" {
  type        = list(string)
  description = "Optional Monitoring notification channel IDs to attach to alert policies. If empty, incidents will be created without notifications."
  default     = []
}

variable "bootstrap_demo_corpus" {
  type        = bool
  description = "Whether the app bootstraps the bundled demo corpus on startup. Disable to troubleshoot slow startups."
  default     = true
}


# --- Staff-level hygiene toggles (recommended defaults) ---

variable "enable_project_iam" {
  type        = bool
  description = <<EOT
If true, this stack will manage *project-level* IAM bindings for your Google Groups.

Staff-level recommendation:
- Manage project-level IAM centrally in the Terraform GCP Platform Baseline repo (repo 3),
  and keep application repos focused on *app-scoped* resources.
- Leave this false unless you explicitly want this repo to be standalone.
EOT
  default     = false
}

variable "log_retention_days" {
  type        = number
  description = "Retention (days) for the service-scoped log bucket used for client log views."
  default     = 30
}

variable "enable_log_views" {
  type        = bool
  description = "Create a service-scoped log bucket + Logs Router sink + log view for least-privilege client access."
  default     = true
}

variable "enable_log_bucket_analytics" {
  type        = bool
  description = <<EOT
Enable Cloud Logging bucket analytics for the service-scoped log bucket.

Notes:
- Not required for this demo; default is false to keep costs and complexity down.
- Some bucket settings can be eventually-consistent right after create/undelete, so enabling analytics may require a retry.
EOT
  default     = false
}

variable "enable_slo" {
  type        = bool
  description = "Create a Service Monitoring Service + Availability SLO + burn-rate alert policy."
  default     = true
}
