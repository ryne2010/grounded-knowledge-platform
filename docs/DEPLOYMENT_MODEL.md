# Deployment model

This project is designed around a **one-deployment-per-client** model.

Decision record: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`.

That means:

- **Hard boundaries are enforced by infrastructure**, not by in-app multi-tenancy.
- Each client gets their own:
  - Cloud Run service (unique URL)
  - Cloud SQL (Postgres) instance + database
  - logs/metrics/dashboards scoped to that service

This keeps the application logic simpler and aligns with least-privilege and auditability patterns.

## Recommended approach

### Option A (recommended): one GCP project per client

For real client work, a dedicated project per client is the cleanest boundary:

- simpler IAM
- simpler cost attribution
- simpler incident response

You can deploy the same Terraform root into each project.

> This repo assumes **one GCP project per client**. If you need multiple clients per project, treat it as a future enhancement.
