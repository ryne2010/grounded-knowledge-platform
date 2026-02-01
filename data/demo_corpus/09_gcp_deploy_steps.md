# GCP Deploy Steps (High Level)

## Targets
- Cloud Run service: `gkp-<env>` (e.g., `gkp-dev`)
- Artifact Registry repo: `gkp`
- Remote Terraform state: `gs://<project>-tfstate` with prefix `gkp/<env>`

## Workflow
1. `make init` to set gcloud project/region.
2. `make doctor` to verify tools/auth.
3. `make bootstrap-state` and `make tf-init`.
4. `make plan` then `make deploy`.
5. `make verify` and inspect logs/metrics.

## Public demo settings
Set `PUBLIC_DEMO_MODE=1` in Cloud Run env to force:
- extractive-only
- uploads disabled
- eval disabled
