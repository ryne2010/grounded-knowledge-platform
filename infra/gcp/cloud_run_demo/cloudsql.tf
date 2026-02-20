resource "random_password" "cloudsql_password" {
  count   = var.enable_cloudsql ? 1 : 0
  length  = 24
  special = false
}

resource "google_sql_database_instance" "cloudsql" {
  count            = var.enable_cloudsql ? 1 : 0
  project          = var.project_id
  region           = var.region
  name             = "gkp-${var.env}-pg"
  database_version = "POSTGRES_16"

  settings {
    tier              = var.cloudsql_tier
    availability_type = "ZONAL"
    disk_size         = var.cloudsql_disk_size_gb
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    backup_configuration {
      enabled = true
    }
  }

  deletion_protection = false
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
