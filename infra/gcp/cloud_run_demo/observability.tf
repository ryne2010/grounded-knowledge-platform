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
  cloudrun_base_filter = "resource.type=\"cloud_run_revision\" metric.type=\"run.googleapis.com/request_count\" resource.label.\"service_name\"=\"${var.service_name}\""
  cloudrun_5xx_filter  = "resource.type=\"cloud_run_revision\" metric.type=\"run.googleapis.com/request_count\" metric.label.\"response_code_class\"=\"5xx\" resource.label.\"service_name\"=\"${var.service_name}\""
  cloudrun_latency_filter = "resource.type=\"cloud_run_revision\" metric.type=\"run.googleapis.com/request_latencies\" resource.label.\"service_name\"=\"${var.service_name}\""

  # A small dashboard with four widgets:
  # - request count (total)
  # - 5xx request count
  # - p95 latency
  # - recent error logs panel
  dashboard_json = {
    "displayName" : "${var.service_name} (${var.env}) — Ops",
    "dashboardFilters" : [],
    "labels" : {
      "playbook" : ""
    },
    "gridLayout" : {
      "columns" : 2,
      "widgets" : [
        {
          "title" : "Request count (per 60s)",
          "xyChart" : {
            "dataSets" : [
              {
                "minAlignmentPeriod" : "60s",
                "plotType" : "LINE",
                "targetAxis" : "Y1",
                "timeSeriesQuery" : {
                  "timeSeriesFilter" : {
                    "filter" : local.cloudrun_base_filter,
                    "aggregation" : {
                      "alignmentPeriod" : "60s",
                      "perSeriesAligner" : "ALIGN_DELTA",
                      "crossSeriesReducer" : "REDUCE_SUM",
                      "groupByFields" : []
                    }
                  }
                }
              }
            ],
            "thresholds" : [],
            "yAxis" : {
              "label" : "",
              "scale" : "LINEAR"
            }
          }
        },
        {
          "title" : "5xx errors (per 60s)",
          "xyChart" : {
            "dataSets" : [
              {
                "minAlignmentPeriod" : "60s",
                "plotType" : "LINE",
                "targetAxis" : "Y1",
                "timeSeriesQuery" : {
                  "timeSeriesFilter" : {
                    "filter" : local.cloudrun_5xx_filter,
                    "aggregation" : {
                      "alignmentPeriod" : "60s",
                      "perSeriesAligner" : "ALIGN_DELTA",
                      "crossSeriesReducer" : "REDUCE_SUM",
                      "groupByFields" : []
                    }
                  }
                }
              }
            ],
            "thresholds" : [],
            "yAxis" : {
              "label" : "",
              "scale" : "LINEAR"
            }
          }
        },
        {
          "title" : "Latency p95 (ms)",
          "xyChart" : {
            "dataSets" : [
              {
                "minAlignmentPeriod" : "60s",
                "plotType" : "LINE",
                "targetAxis" : "Y1",
                "timeSeriesQuery" : {
                  "timeSeriesFilter" : {
                    "filter" : local.cloudrun_latency_filter,
                    "aggregation" : {
                      "alignmentPeriod" : "60s",
                      "perSeriesAligner" : "ALIGN_PERCENTILE_95",
                      "crossSeriesReducer" : "REDUCE_MEAN",
                      "groupByFields" : []
                    }
                  }
                }
              }
            ],
            "thresholds" : [],
            "yAxis" : {
              "label" : "",
              "scale" : "LINEAR"
            }
          }
        },
        {
          "title" : "Recent errors (Logs)",
          "logsPanel" : {
            "filter" : "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.service_name}\" severity>=ERROR",
            "resourceNames" : [
              "projects/${var.project_id}"
            ]
          }
        }
      ]
    }
  }
}

resource "google_monitoring_dashboard" "cloudrun" {
  count   = var.enable_observability ? 1 : 0
  project = var.project_id

  dashboard_json = jsonencode(local.dashboard_json)
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
