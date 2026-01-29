#!/usr/bin/env bash
set -euo pipefail

# Deploy a safety-first public demo to Cloud Run.
#
# Notes:
# - This uses `gcloud run deploy --source .` which triggers Cloud Build.
# - For many personal demos, Cloud Run usage can stay near the free tier, but you should still set a budget.

: "${GCP_PROJECT:?Set GCP_PROJECT}"
: "${GCP_REGION:=us-central1}"
: "${SERVICE_NAME:=grounded-kp-demo}"

gcloud config set project "$GCP_PROJECT"

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