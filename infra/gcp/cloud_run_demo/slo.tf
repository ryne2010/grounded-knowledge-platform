/*
  Service Monitoring: Availability + Latency SLOs with burn-rate alerts.

  Why include this?
  - It demonstrates "staff-level ops maturity": define SLIs/SLOs and alert on
    error-budget burn rate (fast + slow windows), not only static thresholds.

  Notes:
  - Cloud Run metrics come from Cloud Monitoring (run.googleapis.com/*).
  - Availability SLI: ratio of 2xx requests / total requests.
  - Latency SLI: percentage of requests under a target latency threshold.
*/

locals {
  monitoring_service_id = var.service_name

  # Cloud Monitoring filter syntax (NOT the same as Cloud Logging filters).
  # We scope to this Cloud Run service + region.
  base_request_count_filter = join(" AND ", [
    "metric.type=\"run.googleapis.com/request_count\"",
    "resource.type=\"cloud_run_revision\"",
    "resource.label.\"service_name\"=\"${var.service_name}\"",
    "resource.label.\"location\"=\"${var.region}\"",
  ])

  good_2xx_filter = join(" AND ", [
    local.base_request_count_filter,
    "metric.label.\"response_code_class\"=\"2xx\"",
  ])

  request_latency_filter = join(" AND ", [
    "metric.type=\"run.googleapis.com/request_latencies\"",
    "resource.type=\"cloud_run_revision\"",
    "resource.label.\"service_name\"=\"${var.service_name}\"",
    "resource.label.\"location\"=\"${var.region}\"",
  ])

  availability_slo_full_name = "projects/${var.project_id}/services/${local.monitoring_service_id}/serviceLevelObjectives/availability"
  latency_slo_full_name      = "projects/${var.project_id}/services/${local.monitoring_service_id}/serviceLevelObjectives/latency-p95"
  burn_rate_fast_window      = "1h"
  burn_rate_slow_window      = "6h"
}

resource "google_monitoring_service" "cloud_run_service" {
  count = (var.enable_observability && var.enable_slo) ? 1 : 0

  project      = var.project_id
  service_id   = local.monitoring_service_id
  display_name = "Cloud Run: ${var.service_name}"

  basic_service {
    service_type = "CLOUD_RUN"
    service_labels = {
      location     = var.region
      service_name = var.service_name
    }
  }

  user_labels = {
    env     = var.env
    service = var.service_name
    repo    = "grounded-knowledge-platform"
  }
}

resource "google_monitoring_slo" "availability" {
  count = (var.enable_observability && var.enable_slo) ? 1 : 0

  project      = var.project_id
  service      = google_monitoring_service.cloud_run_service[0].service_id
  slo_id       = "availability"
  display_name = "Availability (2xx ratio) — ${var.service_name}"

  goal                = var.slo_availability_goal
  rolling_period_days = var.slo_rolling_period_days

  request_based_sli {
    good_total_ratio {
      good_service_filter  = local.good_2xx_filter
      total_service_filter = local.base_request_count_filter
    }
  }
}

resource "google_monitoring_slo" "latency_p95" {
  count = (var.enable_observability && var.enable_slo) ? 1 : 0

  project      = var.project_id
  service      = google_monitoring_service.cloud_run_service[0].service_id
  slo_id       = "latency-p95"
  display_name = "Latency (${var.slo_latency_threshold_ms}ms threshold) — ${var.service_name}"

  goal                = var.slo_latency_goal
  rolling_period_days = var.slo_rolling_period_days

  request_based_sli {
    distribution_cut {
      distribution_filter = local.request_latency_filter
      range {
        min = 0
        max = var.slo_latency_threshold_ms
      }
    }
  }
}

resource "google_monitoring_alert_policy" "slo_burn_rate" {
  count = (var.enable_observability && var.enable_slo) ? 1 : 0

  project      = var.project_id
  display_name = "${var.service_name} — SLO burn rate (Availability)"
  combiner     = "OR"

  documentation {
    mime_type = "text/markdown"
    content   = <<EOT
This alert fires when ${var.service_name} is burning availability error budget too quickly.

**What to check first**
1. Cloud Run 5xx and latency dashboards
2. Recent deploy / config / IAM changes
3. Cloud SQL health and saturation
4. Runbook: docs/RUNBOOKS/SLOS.md
EOT
  }

  # Fast burn catches sharp regressions quickly.
  conditions {
    display_name = "Fast burn (${local.burn_rate_fast_window})"
    condition_threshold {
      filter          = "select_slo_burn_rate(\"${local.availability_slo_full_name}\", \"${local.burn_rate_fast_window}\")"
      comparison      = "COMPARISON_GT"
      threshold_value = var.slo_burn_rate_fast_threshold
      duration        = "0s"

      trigger {
        count = 1
      }
    }
  }

  # Slow burn catches sustained degradation while reducing noise.
  conditions {
    display_name = "Slow burn (${local.burn_rate_slow_window})"
    condition_threshold {
      filter          = "select_slo_burn_rate(\"${local.availability_slo_full_name}\", \"${local.burn_rate_slow_window}\")"
      comparison      = "COMPARISON_GT"
      threshold_value = var.slo_burn_rate_slow_threshold
      duration        = "0s"

      trigger {
        count = 1
      }
    }
  }

  notification_channels = var.notification_channels
  enabled               = true

  user_labels = {
    env     = var.env
    service = var.service_name
    type    = "availability-slo-burn-rate"
  }
}

resource "google_monitoring_alert_policy" "latency_slo_burn_rate" {
  count = (var.enable_observability && var.enable_slo) ? 1 : 0

  project      = var.project_id
  display_name = "${var.service_name} — SLO burn rate (Latency)"
  combiner     = "OR"

  documentation {
    mime_type = "text/markdown"
    content   = <<EOT
This alert fires when ${var.service_name} is burning latency error budget too quickly.

**What to check first**
1. Query stage latency widgets (retrieval vs answer generation)
2. Cloud Run instance scaling/cold starts
3. Cloud SQL CPU and active backends
4. Runbook: docs/RUNBOOKS/SLOS.md
EOT
  }

  conditions {
    display_name = "Fast burn (${local.burn_rate_fast_window})"
    condition_threshold {
      filter          = "select_slo_burn_rate(\"${local.latency_slo_full_name}\", \"${local.burn_rate_fast_window}\")"
      comparison      = "COMPARISON_GT"
      threshold_value = var.slo_burn_rate_fast_threshold
      duration        = "0s"

      trigger {
        count = 1
      }
    }
  }

  conditions {
    display_name = "Slow burn (${local.burn_rate_slow_window})"
    condition_threshold {
      filter          = "select_slo_burn_rate(\"${local.latency_slo_full_name}\", \"${local.burn_rate_slow_window}\")"
      comparison      = "COMPARISON_GT"
      threshold_value = var.slo_burn_rate_slow_threshold
      duration        = "0s"

      trigger {
        count = 1
      }
    }
  }

  notification_channels = var.notification_channels
  enabled               = true

  user_labels = {
    env     = var.env
    service = var.service_name
    type    = "latency-slo-burn-rate"
  }
}

output "slo_full_name" {
  description = "Full resource name for the Availability SLO (backward-compatible alias)."
  value       = (var.enable_observability && var.enable_slo) ? local.availability_slo_full_name : null
}

output "latency_slo_full_name" {
  description = "Full resource name for the latency SLO."
  value       = (var.enable_observability && var.enable_slo) ? local.latency_slo_full_name : null
}

output "alert_policy_slo_burn_rate_availability_name" {
  description = "Alert policy resource name for availability SLO burn-rate alerts."
  value       = (var.enable_observability && var.enable_slo) ? google_monitoring_alert_policy.slo_burn_rate[0].id : null
}

output "alert_policy_slo_burn_rate_latency_name" {
  description = "Alert policy resource name for latency SLO burn-rate alerts."
  value       = (var.enable_observability && var.enable_slo) ? google_monitoring_alert_policy.latency_slo_burn_rate[0].id : null
}
