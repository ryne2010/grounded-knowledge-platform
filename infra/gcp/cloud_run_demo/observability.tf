# Observability as code
#
# Goal:
# - Demonstrate staff-level "ops posture" by codifying dashboards + alerts.
# - Keep this small and cost-friendly.
#
# Notes:
# - Dashboards + alert policies are generally low-cost; the metrics already exist.
# - Notification channels are optional. If you attach none, incidents still show in Monitoring.

locals {
  cloudrun_base_filter    = "resource.type=\"cloud_run_revision\" metric.type=\"run.googleapis.com/request_count\" resource.label.\"service_name\"=\"${var.service_name}\""
  cloudrun_5xx_filter     = "resource.type=\"cloud_run_revision\" metric.type=\"run.googleapis.com/request_count\" metric.label.\"response_code_class\"=\"5xx\" resource.label.\"service_name\"=\"${var.service_name}\""
  cloudrun_latency_filter = "resource.type=\"cloud_run_revision\" metric.type=\"run.googleapis.com/request_latencies\" resource.label.\"service_name\"=\"${var.service_name}\""

  # OTEL metrics are exported to Cloud Monitoring under workload.googleapis.com/*
  # when OTEL is enabled in the application runtime.
  query_retrieval_latency_filter  = "metric.type=\"workload.googleapis.com/gkp.query.retrieval.duration_ms\""
  query_generation_latency_filter = "metric.type=\"workload.googleapis.com/gkp.query.generation.duration_ms\""

  ingestion_failure_metric_name = "${replace(var.service_name, "-", "_")}_ingestion_failures_${var.env}"
  ingestion_failure_log_filter = join(" AND ", [
    "resource.type=\"cloud_run_revision\"",
    "resource.labels.service_name=\"${var.service_name}\"",
    "jsonPayload.httpRequest.status>=400",
    "(jsonPayload.path=\"/api/ingest/text\" OR jsonPayload.path=\"/api/ingest/file\" OR jsonPayload.path=\"/api/connectors/gcs/sync\" OR jsonPayload.path=\"/api/connectors/gcs/notify\")",
  ])
  ingestion_failure_metric_filter = "metric.type=\"logging.googleapis.com/user/${local.ingestion_failure_metric_name}\""

  cloudsql_database_id = var.enable_cloudsql ? "${var.project_id}:${google_sql_database_instance.cloudsql[0].name}" : null
  cloudsql_cpu_filter = var.enable_cloudsql ? join(" AND ", [
    "resource.type=\"cloudsql_database\"",
    "metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\"",
    "resource.label.\"database_id\"=\"${local.cloudsql_database_id}\"",
  ]) : ""
  cloudsql_connections_filter = var.enable_cloudsql ? join(" AND ", [
    "resource.type=\"cloudsql_database\"",
    "metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\"",
    "resource.label.\"database_id\"=\"${local.cloudsql_database_id}\"",
  ]) : ""

  dashboard_widgets_base = [
    {
      title = "Request count (per 60s)"
      xyChart = {
        dataSets = [
          {
            minAlignmentPeriod = "60s"
            plotType           = "LINE"
            targetAxis         = "Y1"
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = local.cloudrun_base_filter
                aggregation = {
                  alignmentPeriod    = "60s"
                  perSeriesAligner   = "ALIGN_DELTA"
                  crossSeriesReducer = "REDUCE_SUM"
                  groupByFields      = []
                }
              }
            }
          }
        ]
        thresholds = []
        yAxis = {
          label = ""
          scale = "LINEAR"
        }
      }
    },
    {
      title = "5xx errors (per 60s)"
      xyChart = {
        dataSets = [
          {
            minAlignmentPeriod = "60s"
            plotType           = "LINE"
            targetAxis         = "Y1"
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = local.cloudrun_5xx_filter
                aggregation = {
                  alignmentPeriod    = "60s"
                  perSeriesAligner   = "ALIGN_DELTA"
                  crossSeriesReducer = "REDUCE_SUM"
                  groupByFields      = []
                }
              }
            }
          }
        ]
        thresholds = []
        yAxis = {
          label = ""
          scale = "LINEAR"
        }
      }
    },
    {
      title = "Latency p95 (ms)"
      xyChart = {
        dataSets = [
          {
            minAlignmentPeriod = "60s"
            plotType           = "LINE"
            targetAxis         = "Y1"
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = local.cloudrun_latency_filter
                aggregation = {
                  alignmentPeriod    = "60s"
                  perSeriesAligner   = "ALIGN_PERCENTILE_95"
                  crossSeriesReducer = "REDUCE_MEAN"
                  groupByFields      = []
                }
              }
            }
          }
        ]
        thresholds = []
        yAxis = {
          label = ""
          scale = "LINEAR"
        }
      }
    },
    {
      title = "Query stage latency p95 (retrieval vs answer, ms)"
      xyChart = {
        dataSets = [
          {
            legendTemplate     = "Retrieval p95"
            minAlignmentPeriod = "60s"
            plotType           = "LINE"
            targetAxis         = "Y1"
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = local.query_retrieval_latency_filter
                aggregation = {
                  alignmentPeriod    = "60s"
                  perSeriesAligner   = "ALIGN_PERCENTILE_95"
                  crossSeriesReducer = "REDUCE_MEAN"
                  groupByFields      = []
                }
              }
            }
          },
          {
            legendTemplate     = "Answer generation p95"
            minAlignmentPeriod = "60s"
            plotType           = "LINE"
            targetAxis         = "Y1"
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = local.query_generation_latency_filter
                aggregation = {
                  alignmentPeriod    = "60s"
                  perSeriesAligner   = "ALIGN_PERCENTILE_95"
                  crossSeriesReducer = "REDUCE_MEAN"
                  groupByFields      = []
                }
              }
            }
          }
        ]
        thresholds = []
        yAxis = {
          label = ""
          scale = "LINEAR"
        }
      }
    },
    {
      title = "Recent errors (Logs)"
      logsPanel = {
        filter = "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.service_name}\" severity>=ERROR"
        resourceNames = [
          "projects/${var.project_id}"
        ]
      }
    }
  ]

  dashboard_widgets_private = var.allow_unauthenticated ? [] : [
    {
      title = "Ingestion failures (per 60s, private deployments)"
      xyChart = {
        dataSets = [
          {
            minAlignmentPeriod = "60s"
            plotType           = "LINE"
            targetAxis         = "Y1"
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = local.ingestion_failure_metric_filter
                aggregation = {
                  alignmentPeriod    = "60s"
                  perSeriesAligner   = "ALIGN_DELTA"
                  crossSeriesReducer = "REDUCE_SUM"
                  groupByFields      = []
                }
              }
            }
          }
        ]
        thresholds = []
        yAxis = {
          label = ""
          scale = "LINEAR"
        }
      }
    }
  ]

  dashboard_widgets_cloudsql = var.enable_cloudsql ? [
    {
      title = "Cloud SQL CPU utilization (%)"
      xyChart = {
        dataSets = [
          {
            minAlignmentPeriod = "60s"
            plotType           = "LINE"
            targetAxis         = "Y1"
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = local.cloudsql_cpu_filter
                aggregation = {
                  alignmentPeriod    = "60s"
                  perSeriesAligner   = "ALIGN_MEAN"
                  crossSeriesReducer = "REDUCE_MEAN"
                  groupByFields      = []
                }
              }
            }
          }
        ]
        thresholds = []
        yAxis = {
          label = ""
          scale = "LINEAR"
        }
      }
    },
    {
      title = "Cloud SQL active backends"
      xyChart = {
        dataSets = [
          {
            minAlignmentPeriod = "60s"
            plotType           = "LINE"
            targetAxis         = "Y1"
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = local.cloudsql_connections_filter
                aggregation = {
                  alignmentPeriod    = "60s"
                  perSeriesAligner   = "ALIGN_MEAN"
                  crossSeriesReducer = "REDUCE_MEAN"
                  groupByFields      = []
                }
              }
            }
          }
        ]
        thresholds = []
        yAxis = {
          label = ""
          scale = "LINEAR"
        }
      }
    }
  ] : []

  dashboard_json = {
    displayName      = "${var.service_name} (${var.env}) — Ops"
    dashboardFilters = []
    labels = {
      playbook = ""
    }
    gridLayout = {
      columns = 2
      widgets = concat(local.dashboard_widgets_base, local.dashboard_widgets_private, local.dashboard_widgets_cloudsql)
    }
  }
}

resource "google_logging_metric" "ingestion_failures" {
  count   = (var.enable_observability && !var.allow_unauthenticated) ? 1 : 0
  project = var.project_id
  name    = local.ingestion_failure_metric_name

  description = "Count of failed ingestion-related API requests for ${var.service_name}."
  filter      = local.ingestion_failure_log_filter

  metric_descriptor {
    metric_kind  = "DELTA"
    value_type   = "INT64"
    unit         = "1"
    display_name = "Ingestion failures"
  }
}

resource "google_monitoring_dashboard" "cloudrun" {
  count   = var.enable_observability ? 1 : 0
  project = var.project_id

  dashboard_json = jsonencode(local.dashboard_json)
  depends_on     = [google_logging_metric.ingestion_failures]
}

resource "google_monitoring_alert_policy" "cloudrun_5xx" {
  count        = var.enable_observability ? 1 : 0
  project      = var.project_id
  display_name = "${var.service_name} (${var.env}) — 5xx detected"

  combiner = "OR"

  conditions {
    display_name = "5xx request count > 0"

    condition_threshold {
      filter          = local.cloudrun_5xx_filter
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = []
      }

      trigger {
        count = 1
      }
    }
  }

  # You can attach e-mail / Slack / PagerDuty channels.
  notification_channels = var.notification_channels

  user_labels = {
    app = "gkp"
    env = var.env
  }
}

resource "google_monitoring_alert_policy" "cloudrun_latency_p95" {
  count        = var.enable_observability ? 1 : 0
  project      = var.project_id
  display_name = "${var.service_name} (${var.env}) — latency p95 high"

  combiner = "OR"

  conditions {
    display_name = "p95 latency > 1000ms"

    condition_threshold {
      filter          = local.cloudrun_latency_filter
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 1000

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields      = []
      }

      trigger {
        count = 1
      }
    }
  }

  notification_channels = var.notification_channels

  user_labels = {
    app = "gkp"
    env = var.env
  }
}
