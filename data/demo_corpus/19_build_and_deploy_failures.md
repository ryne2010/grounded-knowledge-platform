# Build and Deploy Failures

## Cloud Build
- Permission to push to Artifact Registry
- APIs enabled (cloudbuild, artifactregistry)

## Cloud Run
- Container must listen on $PORT
- Health endpoint should respond quickly
- Keep memory/CPU conservative in demo

## Terraform
- Remote state bucket access
- Drift detection via `plan -detailed-exitcode`
