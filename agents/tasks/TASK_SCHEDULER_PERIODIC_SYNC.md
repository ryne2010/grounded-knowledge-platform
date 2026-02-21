# Task: Periodic GCS sync via Cloud Scheduler

Spec: `docs/SPECS/SCHEDULER_PERIODIC_SYNC.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/infra_terraform_gcp.md`

## Goal

For private deployments, support a periodic “sync this prefix” ingestion cadence using **Cloud Scheduler**.

This is an ops-quality feature: once set, ingestion stays fresh without manual intervention.

## Preconditions

- Connector sync endpoint exists: `POST /api/connectors/gcs/sync`
- Auth is configured for private deployments:
  - recommended: `AUTH_MODE=oidc` (scheduler service account)
  - acceptable: `AUTH_MODE=api_key` (static header)

## Requirements

### Terraform

- Add optional Cloud Scheduler job:
  - configurable cron schedule
  - configurable JSON body for bucket/prefix
  - targets the Cloud Run service URL

- IAM:
  - scheduler service account can invoke Cloud Run

### App/Auth

- If using OIDC:
  - validate the JWT
  - map the scheduler principal to `admin`

### Observability

- Log scheduled trigger events with:
  - job name
  - bucket/prefix
  - returned `run_id`

### Docs

- Update `docs/RUNBOOKS/CONNECTORS_GCS.md` with:
  - how to configure a scheduled sync
  - how to pause/disable

## Acceptance criteria

- A configured schedule triggers sync runs automatically.
- Sync runs show up in ingestion run history.

## Validation

- Terraform fmt/validate
- Manual test in a private project:
  - force-run scheduler once
  - confirm a sync run is created

