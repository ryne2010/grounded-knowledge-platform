# Cloud Run demo deployment (Terraform)

This folder shows how to deploy the **Grounded Knowledge Platform** to **Cloud Run** using the
same **baseline Terraform modules** used across the portfolio.

Emphasis:
- **Safe public demo defaults** (`PUBLIC_DEMO_MODE=1`, no uploads)
- **Scale-to-zero** (min instances `0`)
- **Cost guardrails** (max instances `1`)
- Optional (disabled by default): **Serverless VPC Access connector**

> Note: the VPC connector is *not* free. Keep it disabled for a near-$0 demo.

---

## Prereqs

- Terraform >= 1.5
- `gcloud` authenticated (`gcloud auth application-default login`)
- A GCP project with billing enabled

---

## Quickstart

### 1) Initialize

```bash
cd infra/gcp/cloud_run_demo
terraform init
```

### 2) Plan/apply

You must provide an image URI. The module will also create an Artifact Registry repo for you.

```bash
terraform apply \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="region=us-central1" \
  -var="image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/gkp/grounded-kp:latest"
```

### 3) Build + push the image

From the repo root:

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev

IMAGE="us-central1-docker.pkg.dev/YOUR_PROJECT_ID/gkp/grounded-kp:latest"
docker build -t "$IMAGE" -f docker/Dockerfile .
docker push "$IMAGE"
```

Re-run `terraform apply` if needed.

---

## Optional: VPC connector

If you want to demonstrate a *private networking* deployment path (e.g., Cloud Run → private DB),
enable the connector:

```bash
terraform apply \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="enable_vpc_connector=true"
```

This will create a VPC + Serverless VPC Access connector and attach it to the Cloud Run service.

---

## Outputs

- `service_url` — public URL
- `artifact_repo` — Artifact Registry repo ID
- `runtime_service_account` — Cloud Run runtime service account email
