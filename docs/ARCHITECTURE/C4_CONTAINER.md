# C4 — Container diagram

This repo deploys as a **single container** on Cloud Run:

- serves the API (FastAPI)
- serves the built frontend assets (React/Vite static files)
- connects to Cloud SQL Postgres (pgvector required)

```mermaid
flowchart TB
  browser[Browser] -->|HTTPS| run[Cloud Run Service<br/>API + UI in one container]

  run -->|Unix socket / TCP<br/>DATABASE_URL| sql[(Cloud SQL Postgres<br/>pgvector + FTS)]
  run -->|Optional (private): list/download objects| gcs[(Cloud Storage bucket)]
  run -->|Logs/metrics/traces| logging[(Cloud Logging / Monitoring)]

  ci[GitHub Actions] -->|Terraform plan/apply<br/>policy gates| tf[Terraform]
  tf --> run
  tf --> sql
  tf --> gcs

  build[Cloud Build / Docker build] -->|push image| ar[(Artifact Registry)]
  ar --> run
```

## Container boundaries

- **Web UI**: built with `pnpm build` into `web/dist`, served by the API container.
- **API**: FastAPI app that enforces demo-mode gates and auth on privileged endpoints.
- **DB**: Postgres schema stores docs/chunks/embeddings/ingest lineage.

## Why a single container?

- Simplifies Cloud Run deployment and the “public demo” posture.
- Keeps the portfolio project realistic: one service, one database, clear ops boundaries.

