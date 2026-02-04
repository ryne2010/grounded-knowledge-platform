data "google_project" "current" {
  project_id = var.project_id
}

# Cloud Build runs as: <PROJECT_NUMBER>@cloudbuild.gserviceaccount.com
#
# When we use Cloud Build to build/push the deploy image, it needs permission to push to Artifact Registry.
# We grant this at the repo level (more scoped than a project-level IAM binding).
resource "google_artifact_registry_repository_iam_member" "cloud_build_writer" {
  project    = var.project_id
  location   = var.region
  repository = var.artifact_repo_name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${data.google_project.current.number}@cloudbuild.gserviceaccount.com"

  depends_on = [module.artifact_registry]
}
