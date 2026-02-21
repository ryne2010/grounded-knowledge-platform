output "service_url" {
  value       = module.cloud_run.service_uri
  description = "Cloud Run service URL."
}

output "service_name" {
  value       = module.cloud_run.service_name
  description = "Cloud Run service name."
}

output "image" {
  value       = local.image
  description = "Deployed container image URI."
}

output "artifact_repo" {
  value       = module.artifact_registry.docker_repository
  description = "Artifact Registry Docker repository host/path (use for docker build/tag/push)."
}

output "runtime_service_account" {
  value       = module.service_accounts.runtime_service_account_email
  description = "Runtime service account email."
}

output "serverless_connector_id" {
  value       = (var.enable_vpc_connector || var.enable_cloudsql) ? try(module.network[0].serverless_connector_id, null) : null
  description = "Serverless VPC Access connector ID (if created)."
}

output "monitoring_dashboard_name" {
  value       = var.enable_observability ? try(google_monitoring_dashboard.cloudrun[0].id, null) : null
  description = "Monitoring dashboard resource name (if enabled)."
}

output "alert_policy_5xx_name" {
  value       = var.enable_observability ? try(google_monitoring_alert_policy.cloudrun_5xx[0].id, null) : null
  description = "Alert policy name for 5xx errors (if enabled)."
}

output "alert_policy_latency_name" {
  value       = var.enable_observability ? try(google_monitoring_alert_policy.cloudrun_latency_p95[0].id, null) : null
  description = "Alert policy name for latency p95 (if enabled)."
}

output "cloudsql_connection_name" {
  value       = var.enable_cloudsql ? try(google_sql_database_instance.cloudsql[0].connection_name, null) : null
  description = "Cloud SQL connection name (if Cloud SQL is enabled)."
}

output "cloudsql_database_url" {
  value       = var.enable_cloudsql ? local.cloudsql_database_url : null
  description = "DATABASE_URL injected into Cloud Run (if Cloud SQL is enabled)."
  sensitive   = true
}

output "pubsub_ingest_topic" {
  value       = local.enable_pubsub_push_ingest ? google_pubsub_topic.gcs_ingest_events[0].id : null
  description = "Pub/Sub topic for GCS finalize ingestion events (if enabled)."
}

output "pubsub_ingest_subscription" {
  value       = local.enable_pubsub_push_ingest ? google_pubsub_subscription.gcs_ingest_events_push[0].id : null
  description = "Pub/Sub push subscription id for GCS notify endpoint (if enabled)."
}

output "scheduler_sync_job_name" {
  value       = local.enable_scheduler_sync ? google_cloud_scheduler_job.gcs_periodic_sync[0].name : null
  description = "Cloud Scheduler periodic sync job name (if enabled)."
}

output "scheduler_sync_service_account" {
  value       = local.enable_scheduler_sync ? google_service_account.scheduler_sync_invoker[0].email : null
  description = "Service account email used by Cloud Scheduler to invoke Cloud Run (if enabled)."
}
