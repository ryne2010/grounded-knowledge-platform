locals {
  labels = {
    app = "grounded-knowledge-platform"
    env = var.env
  }

  # Preferred: keep `image_tag` as the only thing you bump per deploy, and derive the full URI.
  # You can override with a full URI via var.image if needed (e.g., pinning by digest).
  image = length(trimspace(var.image)) > 0 ? trimspace(var.image) : "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_name}/${var.image_name}:${var.image_tag}"

  # Safety-first public demo configuration.
  # - extractive-only (no generative output)
  # - no uploads
  # - fixed demo corpus
  base_env_vars = {
    GCP_PROJECT = var.project_id
    GKP_ENV     = var.env

    PUBLIC_DEMO_MODE      = "1"
    CITATIONS_REQUIRED    = "1"
    BOOTSTRAP_DEMO_CORPUS = var.bootstrap_demo_corpus ? "1" : "0"

    # On Cloud Run, /tmp is the safest writable location.
    SQLITE_PATH = "/tmp/index.sqlite"

    # Keep the live demo "boring" on purpose.
    LLM_PROVIDER       = "extractive"
    EMBEDDINGS_BACKEND = "hash"
    OCR_ENABLED        = "0"

    # Simple edge rate limiting (application-level).
    RATE_LIMIT_ENABLED      = "1"
    RATE_LIMIT_WINDOW_S     = "60"
    RATE_LIMIT_MAX_REQUESTS = "30"
  }

  cloudsql_connection_name = var.enable_cloudsql ? google_sql_database_instance.cloudsql[0].connection_name : null
  cloudsql_database_url = var.enable_cloudsql ? format(
    "postgresql://%s:%s@/%s?host=/cloudsql/%s",
    var.cloudsql_user,
    random_password.cloudsql_password[0].result,
    var.cloudsql_database,
    google_sql_database_instance.cloudsql[0].connection_name,
  ) : null

  env_vars = merge(
    local.base_env_vars,
    var.enable_cloudsql ? { DATABASE_URL = local.cloudsql_database_url } : {},
    var.app_env_overrides,
  )

  runtime_roles = concat(
    [
      "roles/logging.logWriter",
      "roles/monitoring.metricWriter",
      "roles/cloudtrace.agent",
    ],
    var.enable_cloudsql ? ["roles/cloudsql.client"] : [],
  )
}

module "core_services" {
  source     = "../modules/core_services"
  project_id = var.project_id
}

module "artifact_registry" {
  source        = "../modules/artifact_registry"
  project_id    = var.project_id
  location      = var.region
  repository_id = var.artifact_repo_name
  description   = "Images for Grounded Knowledge Platform"

  # Cost hygiene: keep demo repositories from growing forever.
  # - dry-run defaults to true so you can review what *would* be deleted.
  # - set to false once you're confident.
  cleanup_policy_dry_run = true
  cleanup_policies = [
    {
      id     = "delete-untagged-old"
      action = "DELETE"
      condition = {
        tag_state  = "UNTAGGED"
        older_than = "1209600s" # 14d
      }
    },
    {
      id     = "keep-latest-tag"
      action = "KEEP"
      condition = {
        tag_state    = "TAGGED"
        tag_prefixes = ["latest"]
      }
    }
  ]
}

module "service_accounts" {
  source     = "../modules/service_accounts"
  project_id = var.project_id

  # Environment-scoped runtime identity (so dev/stage/prod don't share a runtime principal).
  runtime_account_id   = "sa-gkp-runtime-${var.env}"
  runtime_display_name = "GKP Runtime (${var.env})"

  # Cloud Run runtime needs logs/metrics and (optionally) trace correlation.
  runtime_roles = local.runtime_roles
}

module "network" {
  count  = var.enable_vpc_connector ? 1 : 0
  source = "../modules/network"

  project_id   = var.project_id
  network_name = "${var.service_name}-vpc"

  subnets = {
    "${var.service_name}-subnet" = {
      region = var.region
      cidr   = "10.10.0.0/24"
    }
  }

  create_serverless_connector         = true
  serverless_connector_name           = "${var.service_name}-connector"
  serverless_connector_region         = var.region
  serverless_connector_cidr           = "10.8.0.0/28"
  serverless_connector_min_throughput = 200
  serverless_connector_max_throughput = 300
}

module "cloud_run" {
  source = "../modules/cloud_run_service"

  project_id            = var.project_id
  region                = var.region
  service_name          = var.service_name
  image                 = local.image
  service_account_email = module.service_accounts.runtime_service_account_email

  cpu = "1"
  # Cloud Run v2 enforces >= 512Mi for some CPU allocation modes; 512Mi is also safer for Python apps.
  memory        = "512Mi"
  min_instances = var.min_instances
  max_instances = var.max_instances

  allow_unauthenticated = var.allow_unauthenticated
  env_vars              = local.env_vars
  secret_env            = var.secret_env
  cloud_sql_instances   = var.enable_cloudsql ? [google_sql_database_instance.cloudsql[0].connection_name] : []
  labels                = local.labels

  # For real client deployments, consider setting var.deletion_protection=true.
  deletion_protection = var.deletion_protection

  vpc_connector_id = var.enable_vpc_connector ? module.network[0].serverless_connector_id : null
  vpc_egress       = var.vpc_egress
}

resource "google_secret_manager_secret_iam_member" "runtime_secret_access" {
  for_each = toset(values(var.secret_env))

  project   = var.project_id
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.service_accounts.runtime_service_account_email}"
}
