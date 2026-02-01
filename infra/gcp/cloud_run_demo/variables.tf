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
  description = "Container image URI (Artifact Registry recommended)."
}

variable "allow_unauthenticated" {
  type        = bool
  description = "Whether the Cloud Run service is public. Public demo uses true; production typically uses false + IAM invoker bindings."
  default     = true
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

variable "enable_slo" {
  type        = bool
  description = "Create a Service Monitoring Service + Availability SLO + burn-rate alert policy."
  default     = true
}
