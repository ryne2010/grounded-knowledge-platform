locals {
  normalized_billing_account_id = (
    length(trimspace(var.billing_account_id)) == 0
    ? null
    : (
      startswith(trimspace(var.billing_account_id), "billingAccounts/")
      ? trimspace(var.billing_account_id)
      : "billingAccounts/${trimspace(var.billing_account_id)}"
    )
  )

  enable_billing_budget_guardrail = var.enable_billing_budget && local.normalized_billing_account_id != null
}

resource "google_billing_budget" "project_cost_guardrail" {
  count = local.enable_billing_budget_guardrail ? 1 : 0

  billing_account = local.normalized_billing_account_id
  display_name    = "${var.service_name} monthly cost guardrail"

  budget_filter {
    projects               = ["projects/${data.google_project.current.number}"]
    calendar_period        = "MONTH"
    credit_types_treatment = "INCLUDE_ALL_CREDITS"
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.billing_budget_amount_usd)
    }
  }

  dynamic "threshold_rules" {
    for_each = var.billing_budget_alert_thresholds
    content {
      threshold_percent = threshold_rules.value
      spend_basis       = "CURRENT_SPEND"
    }
  }

  all_updates_rule {
    schema_version                   = "1.0"
    monitoring_notification_channels = var.billing_budget_monitoring_notification_channels
    disable_default_iam_recipients   = var.billing_budget_disable_default_iam_recipients
  }
}
