output "ci_service_account_email" {
  description = "CI service account email to use in GitHub Actions (GCP_WIF_SERVICE_ACCOUNT)."
  value       = local.ci_service_account_email
}

output "workload_identity_provider" {
  description = "Workload Identity Provider resource name to use in GitHub Actions (GCP_WIF_PROVIDER)."
  value       = module.github_oidc.workload_identity_provider
}

output "workload_identity_pool" {
  description = "Workload Identity Pool resource name."
  value       = module.github_oidc.workload_identity_pool
}
