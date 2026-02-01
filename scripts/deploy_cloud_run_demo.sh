#!/usr/bin/env bash
set -euo pipefail

# Deploy a safety-first public demo to Cloud Run using gcloud.
#
# This is an OPTIONAL alternative to the Terraform workflow.
# Prefer Terraform for team workflows / repeatability (remote state, reviewable plans).

: "${GCP_PROJECT:?Set GCP_PROJECT}"
: "${GCP_REGION:=us-central1}"
: "${ENV:=dev}"
: "${SERVICE_NAME:=gkp-${ENV}}"

# Recommended: keep your CLI pointed at the right project to avoid mistakes.
gcloud config set project "$GCP_PROJECT" >/dev/null

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$GCP_REGION" \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=256Mi \
  --min-instances=0 \
  --max-instances=1 \
  --set-env-vars PUBLIC_DEMO_MODE=1 \
  --set-env-vars GCP_PROJECT="$GCP_PROJECT" \
  --set-env-vars SQLITE_PATH=/tmp/index.sqlite \
  --set-env-vars BOOTSTRAP_DEMO_CORPUS=1

echo "Deployed: $SERVICE_NAME"
