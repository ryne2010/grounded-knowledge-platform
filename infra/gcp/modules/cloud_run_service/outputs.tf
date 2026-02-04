output "service_uri" {
  # Some provider/API combinations may populate `urls` but leave `uri` empty.
  # Prefer `uri` when present, otherwise fall back to the first URL.
  value = (
    length(trimspace(try(google_cloud_run_v2_service.service.uri, ""))) > 0
    ? google_cloud_run_v2_service.service.uri
    : try(google_cloud_run_v2_service.service.urls[0], "")
  )
  description = "Cloud Run service URL."
}

output "service_name" {
  value       = google_cloud_run_v2_service.service.name
  description = "Cloud Run service resource name."
}
