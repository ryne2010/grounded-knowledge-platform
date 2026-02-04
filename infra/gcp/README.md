# GCP infrastructure examples

This folder contains Terraform examples for deploying this project to **Google Cloud Platform**.

Included:
- `cloud_run_demo/` — deploy the app to **Cloud Run** with safe public-demo defaults.
- `wif_bootstrap/` — bootstrap **Workload Identity Federation (WIF)** for GitHub Actions (no long-lived keys).

## Repo map (what’s used vs included)

See `MAP.md` for a quick “what’s in play” inventory:
- deploy entrypoints
- Terraform modules actually invoked by `cloud_run_demo/`
- CI workflows that run in GitHub Actions
- optional baseline modules included for reference

## Baseline modules

`infra/gcp/modules/` is a snapshot of the portfolio's shared Terraform modules
(*"Terraform GCP Platform Baseline"* repo). They are copied here so this repo can be
deployed independently.

**License note:** these baseline Terraform modules are licensed under **Apache-2.0**.
See `infra/gcp/modules/LICENSE` and `infra/gcp/modules/NOTICE`.

If you prefer a single source of truth, you can replace module sources like:

```hcl
source = "../modules/cloud_run_service"
```

with a Git source pointing at the baseline repo, for example:

```hcl
source = "git::https://github.com/YOUR_ORG/terraform-gcp-platform-baseline.git//modules/cloud_run_service?ref=v0.1.0"
```

## Cost note

The default demo configuration is scale-to-zero and caps max instances. Enabling a
Serverless VPC Access connector is optional and is **not free**.
