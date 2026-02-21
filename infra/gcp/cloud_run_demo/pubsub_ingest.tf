locals {
  enable_pubsub_push_ingest = var.enable_pubsub_push_ingest && trimspace(var.pubsub_push_bucket) != ""
}

resource "google_pubsub_topic" "gcs_ingest_events" {
  count   = local.enable_pubsub_push_ingest ? 1 : 0
  project = var.project_id
  name    = "${var.service_name}-gcs-ingest-events"
  labels  = local.labels
}

resource "google_pubsub_topic" "gcs_ingest_events_dlq" {
  count   = local.enable_pubsub_push_ingest ? 1 : 0
  project = var.project_id
  name    = "${var.service_name}-gcs-ingest-events-dlq"
  labels  = local.labels
}

data "google_storage_project_service_account" "gcs_notifications" {
  count   = local.enable_pubsub_push_ingest ? 1 : 0
  project = var.project_id
}

resource "google_pubsub_topic_iam_member" "gcs_notifications_publisher" {
  count   = local.enable_pubsub_push_ingest ? 1 : 0
  project = var.project_id
  topic   = google_pubsub_topic.gcs_ingest_events[0].name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_notifications[0].email_address}"
}

resource "google_service_account" "pubsub_push_invoker" {
  count        = local.enable_pubsub_push_ingest ? 1 : 0
  project      = var.project_id
  account_id   = "sa-gkp-pubsub-push-${var.env}"
  display_name = "GKP PubSub Push Invoker (${var.env})"
}

resource "google_cloud_run_v2_service_iam_member" "pubsub_push_invoker" {
  count    = local.enable_pubsub_push_ingest ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = module.cloud_run.service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub_push_invoker[0].email}"
}

resource "google_pubsub_topic_iam_member" "pubsub_dead_letter_publisher" {
  count   = local.enable_pubsub_push_ingest ? 1 : 0
  project = var.project_id
  topic   = google_pubsub_topic.gcs_ingest_events_dlq[0].name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription" "gcs_ingest_events_push" {
  count   = local.enable_pubsub_push_ingest ? 1 : 0
  project = var.project_id
  name    = "${var.service_name}-gcs-ingest-events-push"
  topic   = google_pubsub_topic.gcs_ingest_events[0].id

  ack_deadline_seconds = var.pubsub_push_ack_deadline_seconds

  push_config {
    push_endpoint = "${module.cloud_run.service_uri}/api/connectors/gcs/notify"
    oidc_token {
      service_account_email = google_service_account.pubsub_push_invoker[0].email
      audience              = module.cloud_run.service_uri
    }
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.gcs_ingest_events_dlq[0].id
    max_delivery_attempts = var.pubsub_push_max_delivery_attempts
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  depends_on = [
    google_cloud_run_v2_service_iam_member.pubsub_push_invoker,
    google_pubsub_topic_iam_member.pubsub_dead_letter_publisher,
  ]
}

resource "google_storage_notification" "gcs_object_finalize" {
  count          = local.enable_pubsub_push_ingest ? 1 : 0
  bucket         = var.pubsub_push_bucket
  payload_format = "JSON_API_V1"
  topic          = google_pubsub_topic.gcs_ingest_events[0].id
  event_types    = ["OBJECT_FINALIZE"]

  object_name_prefix = trimspace(var.pubsub_push_prefix)

  depends_on = [
    google_pubsub_topic_iam_member.gcs_notifications_publisher,
  ]
}
