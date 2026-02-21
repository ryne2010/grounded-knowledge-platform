# Periodic connector sync (Cloud Scheduler)

Status: **Draft** (2026-02-21)

Owner: Repo maintainers

Related tasks:

- `agents/tasks/TASK_SCHEDULER_PERIODIC_SYNC.md`

## Context

Some private deployments want a “set it and forget it” ingestion cadence:

- sync a bucket/prefix every N minutes/hours
- without a human manually calling `make gcs-sync`

This spec defines a minimal Cloud Scheduler job that triggers the existing GCS sync.

## Safety posture

- **Disabled in `PUBLIC_DEMO_MODE`**
- Scheduler only exists in **private deployments**

## Design options

### Option A (recommended): Scheduler → Cloud Run (OIDC)

- Cloud Scheduler makes an authenticated HTTP request to Cloud Run.
- Uses an OIDC token from a scheduler service account.
- Cloud Run verifies the token and authorizes the caller as admin.

Pros:

- avoids static API keys
- demonstrates least-privilege IAM

Cons:

- requires implementing OIDC auth mode (or at least validating Google-signed JWT)

### Option B: Scheduler → Cloud Run (API key)

- Scheduler sends `x-api-key` header.

Pros:

- simplest

Cons:

- secret distribution/rotation burden
- easy to misconfigure

This repo should prefer Option A when feasible.

## Proposed API surface

Use the existing endpoint:

- `POST /api/connectors/gcs/sync`

Scheduler payload should be a fixed JSON blob:

```json
{
  "bucket": "my-bucket",
  "prefix": "knowledge/",
  "max_objects": 200,
  "dry_run": false,
  "classification": "internal",
  "retention": "indefinite",
  "tags": ["client-a"],
  "notes": "scheduler"
}
```

## Infrastructure requirements (Terraform)

- Cloud Scheduler job (cron)
- Scheduler service account
- IAM:
  - service account can invoke Cloud Run
  - (optionally) service account can read GCS objects if ingestion runs under caller identity

## Observability

- Log each scheduled trigger with:
  - job name
  - run_id from the sync response
- Metric: scheduled sync success rate

## Non-goals

- Complex schedules per-prefix (one job per prefix is acceptable)
- Multi-region failover

