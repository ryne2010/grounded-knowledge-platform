output "service_url" {
  value       = module.cloud_run.service_uri
  description = "Cloud Run service URL."
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
  value       = var.enable_vpc_connector ? module.network[0].serverless_connector_id : null
  description = "Serverless VPC Access connector ID (if created)."
}

output "monitoring_dashboard_name" {
  value       = var.enable_observability ? try(google_monitoring_dashboard.cloudrun[0].name, null) : null
  description = "Monitoring dashboard resource name (if enabled)."
}

output "alert_policy_5xx_name" {
  value       = var.enable_observability ? try(google_monitoring_alert_policy.cloudrun_5xx[0].name, null) : null
  description = "Alert policy name for 5xx errors (if enabled)."
}

output "alert_policy_latency_name" {
  value       = var.enable_observability ? try(google_monitoring_alert_policy.cloudrun_latency_p95[0].name, null) : null
  description = "Alert policy name for latency p95 (if enabled)."
}
