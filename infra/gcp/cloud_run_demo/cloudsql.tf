resource "random_password" "cloudsql_password" {
  count   = var.enable_cloudsql ? 1 : 0
  length  = 24
  special = false
}

resource "google_compute_global_address" "cloudsql_private_ip_range" {
  count         = (var.enable_cloudsql && var.cloudsql_private_ip_enabled) ? 1 : 0
  project       = var.project_id
  name          = "${var.service_name}-cloudsql-private-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = module.network[0].network_id
}

resource "google_service_networking_connection" "cloudsql_private_vpc_connection" {
  count                   = (var.enable_cloudsql && var.cloudsql_private_ip_enabled) ? 1 : 0
  network                 = module.network[0].network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.cloudsql_private_ip_range[0].name]
}

resource "google_sql_database_instance" "cloudsql" {
  count            = var.enable_cloudsql ? 1 : 0
  project          = var.project_id
  region           = var.region
  name             = "${var.service_name}-pg"
  database_version = "POSTGRES_16"

  settings {
    edition           = var.cloudsql_edition
    tier              = var.cloudsql_tier
    availability_type = "ZONAL"
    disk_size         = var.cloudsql_disk_size_gb
    disk_type         = var.cloudsql_disk_type
    disk_autoresize   = true

    dynamic "data_cache_config" {
      for_each = var.cloudsql_enable_data_cache ? [1] : []
      content {
        data_cache_enabled = true
      }
    }

    #tfsec:ignore:google-sql-encrypt-in-transit-data Provider v7 removed `require_ssl`; TLS is enforced via `ssl_mode`.
    #tfsec:ignore:google-sql-no-public-access Public IP is an intentional low-cost default with Cloud SQL connector auth; set cloudsql_private_ip_enabled=true for private IP.
    ip_configuration {
      ipv4_enabled    = var.cloudsql_private_ip_enabled ? false : true
      private_network = var.cloudsql_private_ip_enabled ? module.network[0].network_id : null
      ssl_mode        = "ENCRYPTED_ONLY"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }

    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_temp_files"
      value = "0"
    }

    database_flags {
      name  = "log_duration"
      value = "on"
    }

    database_flags {
      name  = "log_hostname"
      value = "on"
    }

    database_flags {
      name  = "log_min_messages"
      value = "error"
    }

    database_flags {
      name  = "log_min_error_statement"
      value = "error"
    }

    database_flags {
      name  = "log_statement"
      value = "ddl"
    }

    database_flags {
      name  = "cloudsql.enable_pgaudit"
      value = "on"
    }

    backup_configuration {
      enabled                        = true
      location                       = var.cloudsql_backup_location
      start_time                     = var.cloudsql_backup_start_time
      point_in_time_recovery_enabled = var.cloudsql_enable_point_in_time_recovery
      transaction_log_retention_days = var.cloudsql_enable_point_in_time_recovery ? var.cloudsql_transaction_log_retention_days : null

      backup_retention_settings {
        retained_backups = var.cloudsql_retained_backups
        retention_unit   = "COUNT"
      }
    }
  }

  deletion_protection = var.deletion_protection

  depends_on = [google_service_networking_connection.cloudsql_private_vpc_connection]
}

resource "google_sql_database" "app" {
  count    = var.enable_cloudsql ? 1 : 0
  project  = var.project_id
  name     = var.cloudsql_database
  instance = google_sql_database_instance.cloudsql[0].name
}

resource "google_sql_user" "app" {
  count    = var.enable_cloudsql ? 1 : 0
  project  = var.project_id
  name     = var.cloudsql_user
  instance = google_sql_database_instance.cloudsql[0].name
  password = random_password.cloudsql_password[0].result
}
