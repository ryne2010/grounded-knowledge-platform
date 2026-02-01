// Terraform remote state (GCS)
//
// This repo intentionally keeps environment-specific backend config out of source control.
// The Makefile runs:
//   terraform init -backend-config="bucket=..." -backend-config="prefix=..."
//
// Why:
// - Teams can use the same code across environments without editing files.
// - Staff-level posture: remote state, versioning, and explicit bootstrap.
terraform {
  backend "gcs" {}
}
