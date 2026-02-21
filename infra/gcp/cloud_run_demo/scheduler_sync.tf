locals {
  enable_scheduler_sync = var.enable_scheduler_sync && trimspace(var.scheduler_sync_bucket) != ""

  scheduler_sync_payload = merge(
    {
      bucket      = trimspace(var.scheduler_sync_bucket)
      prefix      = trimspace(var.scheduler_sync_prefix)
      max_objects = var.scheduler_sync_max_objects
      dry_run     = var.scheduler_sync_dry_run
      notes       = trimspace(var.scheduler_sync_notes)
    },
    length(trimspace(var.scheduler_sync_classification)) > 0 ? {
      classification = trimspace(var.scheduler_sync_classification)
    } : {},
    length(trimspace(var.scheduler_sync_retention)) > 0 ? {
      retention = trimspace(var.scheduler_sync_retention)
    } : {},
    length(var.scheduler_sync_tags) > 0 ? {
      tags = var.scheduler_sync_tags
    } : {},
  )

  scheduler_sync_headers = merge(
    { "Content-Type" = "application/json" },
    length(trimspace(var.scheduler_sync_api_key)) > 0 ? {
      "X-API-Key" = trimspace(var.scheduler_sync_api_key)
    } : {},
  )
}

resource "google_service_account" "scheduler_sync_invoker" {
  count = local.enable_scheduler_sync ? 1 : 0

  project      = var.project_id
  account_id   = "sa-gkp-scheduler-sync-${var.env}"
  display_name = "GKP Scheduler Sync Invoker (${var.env})"
}

resource "google_cloud_run_v2_service_iam_member" "scheduler_sync_invoker" {
  count = local.enable_scheduler_sync ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = module.cloud_run.service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_sync_invoker[0].email}"
}

resource "google_cloud_scheduler_job" "gcs_periodic_sync" {
  count = local.enable_scheduler_sync ? 1 : 0

  project          = var.project_id
  region           = var.region
  name             = "${var.service_name}-gcs-sync"
  description      = "Periodic GCS prefix sync for Grounded Knowledge Platform"
  schedule         = var.scheduler_sync_schedule
  time_zone        = var.scheduler_sync_time_zone
  paused           = var.scheduler_sync_paused
  attempt_deadline = var.scheduler_sync_attempt_deadline

  http_target {
    uri         = "${module.cloud_run.service_uri}/api/connectors/gcs/sync"
    http_method = "POST"
    headers     = local.scheduler_sync_headers
    body        = base64encode(jsonencode(local.scheduler_sync_payload))

    oidc_token {
      service_account_email = google_service_account.scheduler_sync_invoker[0].email
      audience              = module.cloud_run.service_uri
    }
  }

  depends_on = [google_cloud_run_v2_service_iam_member.scheduler_sync_invoker]
}
