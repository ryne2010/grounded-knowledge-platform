locals {
  labels = {
    app = "grounded-knowledge-platform"
    env = "demo"
  }

  # Safety-first public demo configuration.
  env_vars = {
    GCP_PROJECT           = var.project_id
    PUBLIC_DEMO_MODE       = "1"
    BOOTSTRAP_DEMO_CORPUS  = "1"
    # On Cloud Run, /tmp is the safest writable location.
    SQLITE_PATH            = "/tmp/index.sqlite"
    LLM_PROVIDER           = "extractive"
    EMBEDDINGS_BACKEND     = "hash"
    OCR_ENABLED            = "0"
    RATE_LIMIT_ENABLED     = "1"
    RATE_LIMIT_WINDOW_S    = "60"
    RATE_LIMIT_MAX_REQUESTS = "30"
  }
}

module "core_services" {
  source     = "../modules/core_services"
  project_id = var.project_id
}

module "artifact_registry" {
  source      = "../modules/artifact_registry"
  project_id  = var.project_id
  location      = var.region
  repository_id = var.artifact_repo_name
  description   = "Images for Grounded Knowledge Platform demo"
}

module "service_accounts" {
  source     = "../modules/service_accounts"
  project_id = var.project_id
  runtime_account_id   = "sa-gkp-demo"
  runtime_display_name = "GKP Demo Runtime"

  # Cloud Run runtime needs logs/metrics and (optionally) trace correlation.
  runtime_roles = [
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
  ]
}

module "network" {
  count  = var.enable_vpc_connector ? 1 : 0
  source = "../modules/network"

  project_id   = var.project_id
  network_name = "gkp-demo-vpc"

  subnets = {
    "gkp-demo-subnet" = {
      region = var.region
      cidr   = "10.10.0.0/24"
    }
  }

  create_serverless_connector   = true
  serverless_connector_name     = "gkp-demo-connector"
  serverless_connector_region   = var.region
  serverless_connector_cidr     = "10.8.0.0/28"
  serverless_connector_min_throughput = 200
  serverless_connector_max_throughput = 300
}

module "cloud_run" {
  source = "../modules/cloud_run_service"

  project_id            = var.project_id
  region                = var.region
  service_name          = var.service_name
  image                 = var.image
  service_account_email = module.service_accounts.runtime_service_account_email

  cpu          = "1"
  memory       = "256Mi"
  min_instances = var.min_instances
  max_instances = var.max_instances

  allow_unauthenticated = var.allow_unauthenticated
  env_vars              = local.env_vars
  labels                = local.labels

  vpc_connector_id = var.enable_vpc_connector ? module.network[0].serverless_connector_id : null
  vpc_egress       = var.vpc_egress
}
