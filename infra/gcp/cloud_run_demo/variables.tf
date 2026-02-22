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

variable "max_request_concurrency" {
  type        = number
  description = "Maximum number of requests a single Cloud Run instance can serve concurrently."
  default     = 40

  validation {
    condition     = var.max_request_concurrency >= 1 && var.max_request_concurrency <= 1000
    error_message = "max_request_concurrency must be between 1 and 1000."
  }
}

variable "request_timeout_seconds" {
  type        = number
  description = "Cloud Run request timeout in seconds."
  default     = 30

  validation {
    condition     = var.request_timeout_seconds >= 1 && var.request_timeout_seconds <= 3600
    error_message = "request_timeout_seconds must be between 1 and 3600."
  }
}

variable "deletion_protection" {
  type        = bool
  description = "Enable deletion protection for Cloud Run and Cloud SQL resources (recommended for real client deployments)."
  default     = false
}


variable "enable_vpc_connector" {
  type        = bool
  description = "Create and attach a Serverless VPC Access connector (NOT free). This is auto-enabled when Cloud SQL is enabled to support private IP connectivity."
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

variable "enable_pubsub_push_ingest" {
  type        = bool
  description = "Enable optional Pub/Sub push ingestion resources for GCS object finalize events."
  default     = false

  validation {
    condition     = !var.enable_pubsub_push_ingest || !var.allow_unauthenticated
    error_message = "enable_pubsub_push_ingest requires allow_unauthenticated=false (private service)."
  }
}

variable "pubsub_push_bucket" {
  type        = string
  description = "Existing GCS bucket to attach OBJECT_FINALIZE notifications to when enable_pubsub_push_ingest=true."
  default     = ""
}

variable "pubsub_push_prefix" {
  type        = string
  description = "Optional object prefix filter for GCS notification events."
  default     = ""
}

variable "pubsub_push_ack_deadline_seconds" {
  type        = number
  description = "Pub/Sub push subscription ack deadline in seconds."
  default     = 30
}

variable "pubsub_push_max_delivery_attempts" {
  type        = number
  description = "Dead-letter max delivery attempts for Pub/Sub push subscription."
  default     = 5
}

variable "enable_scheduler_sync" {
  type        = bool
  description = "Enable optional Cloud Scheduler -> /api/connectors/gcs/sync periodic sync for private deployments."
  default     = false

  validation {
    condition     = !var.enable_scheduler_sync || !var.allow_unauthenticated
    error_message = "enable_scheduler_sync requires allow_unauthenticated=false (private service)."
  }

  validation {
    condition = !var.enable_scheduler_sync || (
      try(var.app_env_overrides["PUBLIC_DEMO_MODE"], "") == "0" &&
      try(var.app_env_overrides["ALLOW_CONNECTORS"], "") == "1"
    )
    error_message = "enable_scheduler_sync requires app_env_overrides PUBLIC_DEMO_MODE=0 and ALLOW_CONNECTORS=1."
  }
}

variable "scheduler_sync_schedule" {
  type        = string
  description = "Cloud Scheduler cron expression (default: hourly at minute 0)."
  default     = "0 * * * *"

  validation {
    condition     = length(trimspace(var.scheduler_sync_schedule)) > 0
    error_message = "scheduler_sync_schedule must be a non-empty cron expression."
  }
}

variable "scheduler_sync_time_zone" {
  type        = string
  description = "Cloud Scheduler job time zone."
  default     = "Etc/UTC"
}

variable "scheduler_sync_paused" {
  type        = bool
  description = "Whether the Cloud Scheduler job should be created paused."
  default     = false
}

variable "scheduler_sync_attempt_deadline" {
  type        = string
  description = "Cloud Scheduler HTTP attempt deadline (duration string, max 1800s)."
  default     = "320s"
}

variable "scheduler_sync_bucket" {
  type        = string
  description = "Bucket for periodic sync payload when enable_scheduler_sync=true."
  default     = ""
}

variable "scheduler_sync_prefix" {
  type        = string
  description = "Optional prefix for periodic sync payload."
  default     = ""
}

variable "scheduler_sync_max_objects" {
  type        = number
  description = "Max objects per scheduled sync invocation."
  default     = 200

  validation {
    condition     = var.scheduler_sync_max_objects >= 1 && var.scheduler_sync_max_objects <= 5000
    error_message = "scheduler_sync_max_objects must be between 1 and 5000."
  }
}

variable "scheduler_sync_dry_run" {
  type        = bool
  description = "Run scheduled syncs in dry-run mode."
  default     = false
}

variable "scheduler_sync_classification" {
  type        = string
  description = "Optional classification for docs ingested by scheduled syncs."
  default     = ""
}

variable "scheduler_sync_retention" {
  type        = string
  description = "Optional retention policy for docs ingested by scheduled syncs."
  default     = ""
}

variable "scheduler_sync_tags" {
  type        = list(string)
  description = "Optional tags applied to docs ingested by scheduled syncs."
  default     = []
}

variable "scheduler_sync_notes" {
  type        = string
  description = "Optional notes applied to docs ingested by scheduled syncs."
  default     = "scheduler"
}

variable "scheduler_sync_api_key" {
  type        = string
  description = "Optional x-api-key header value for /api/connectors/gcs/sync when AUTH_MODE=api_key."
  default     = ""
  sensitive   = true
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

variable "enable_billing_budget" {
  type        = bool
  description = "Create an optional Billing budget and threshold alerts for this project."
  default     = false

  validation {
    condition     = !var.enable_billing_budget || length(trimspace(var.billing_account_id)) > 0
    error_message = "enable_billing_budget=true requires billing_account_id to be set."
  }
}

variable "billing_account_id" {
  type        = string
  description = "Cloud Billing account ID (either raw ID or full form `billingAccounts/XXXXXX-XXXXXX-XXXXXX`) used for budget resources."
  default     = ""

  validation {
    condition = (
      length(trimspace(var.billing_account_id)) == 0 ||
      can(regex("^billingAccounts/[A-Za-z0-9-]+$", trimspace(var.billing_account_id))) ||
      can(regex("^[A-Za-z0-9-]+$", trimspace(var.billing_account_id)))
    )
    error_message = "billing_account_id must be empty, a raw billing account id, or `billingAccounts/<id>`."
  }
}

variable "billing_budget_amount_usd" {
  type        = number
  description = "Billing budget amount (USD units) for monthly cost alerts."
  default     = 20

  validation {
    condition = (
      var.billing_budget_amount_usd > 0 &&
      var.billing_budget_amount_usd == floor(var.billing_budget_amount_usd)
    )
    error_message = "billing_budget_amount_usd must be a whole number greater than 0."
  }
}

variable "billing_budget_alert_thresholds" {
  type        = list(number)
  description = "Threshold percentages for billing budget alerts (for example: 0.5, 0.9, 1.0)."
  default     = [0.5, 0.9, 1.0]

  validation {
    condition = (
      length(var.billing_budget_alert_thresholds) >= 1 &&
      alltrue([for t in var.billing_budget_alert_thresholds : t >= 0 && t <= 5])
    )
    error_message = "billing_budget_alert_thresholds must include at least one value between 0 and 5."
  }
}

variable "billing_budget_monitoring_notification_channels" {
  type        = list(string)
  description = "Optional Monitoring notification channels for billing budget alerts."
  default     = []
}

variable "billing_budget_disable_default_iam_recipients" {
  type        = bool
  description = "Disable default billing IAM email recipients for budget alerts."
  default     = false
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
  description = "Create Service Monitoring SLOs (availability + latency) with burn-rate alert policies."
  default     = true
}

variable "slo_rolling_period_days" {
  type        = number
  description = "Rolling period for SLO evaluation windows."
  default     = 28

  validation {
    condition     = var.slo_rolling_period_days >= 1 && var.slo_rolling_period_days <= 30
    error_message = "slo_rolling_period_days must be between 1 and 30."
  }
}

variable "slo_availability_goal" {
  type        = number
  description = "Availability SLO goal as ratio (e.g., 0.995 for 99.5%)."
  default     = 0.995

  validation {
    condition     = var.slo_availability_goal > 0 && var.slo_availability_goal <= 1
    error_message = "slo_availability_goal must be in (0, 1]."
  }
}

variable "slo_latency_goal" {
  type        = number
  description = "Latency SLO goal as ratio of requests under threshold (e.g., 0.95)."
  default     = 0.95

  validation {
    condition     = var.slo_latency_goal > 0 && var.slo_latency_goal <= 1
    error_message = "slo_latency_goal must be in (0, 1]."
  }
}

variable "slo_latency_threshold_ms" {
  type        = number
  description = "Latency SLO threshold in milliseconds."
  default     = 1200

  validation {
    condition     = var.slo_latency_threshold_ms > 0 && var.slo_latency_threshold_ms <= 60000
    error_message = "slo_latency_threshold_ms must be between 1 and 60000."
  }
}

variable "slo_burn_rate_fast_threshold" {
  type        = number
  description = "Fast-window burn-rate multiplier threshold."
  default     = 6

  validation {
    condition     = var.slo_burn_rate_fast_threshold > 0
    error_message = "slo_burn_rate_fast_threshold must be greater than 0."
  }
}

variable "slo_burn_rate_slow_threshold" {
  type        = number
  description = "Slow-window burn-rate multiplier threshold."
  default     = 3

  validation {
    condition = (
      var.slo_burn_rate_slow_threshold > 0 &&
      var.slo_burn_rate_slow_threshold <= var.slo_burn_rate_fast_threshold
    )
    error_message = "slo_burn_rate_slow_threshold must be > 0 and <= slo_burn_rate_fast_threshold."
  }
}
