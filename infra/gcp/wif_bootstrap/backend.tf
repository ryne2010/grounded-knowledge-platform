// Terraform remote state (GCS)
//
// Keep backend config out of source control; pass at init time:
//   terraform init -backend-config="bucket=..." -backend-config="prefix=..."
terraform {
  backend "gcs" {}
}

