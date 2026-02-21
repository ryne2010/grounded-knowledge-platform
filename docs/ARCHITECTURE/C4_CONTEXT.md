# C4 — Context diagram

The Grounded Knowledge Platform is a per-client deployment that serves two modes:

- **Public demo** (anonymous, read-only, extractive-only, demo corpus only)
- **Private deployment** (auth enabled, ingestion/connectors/eval optional)

Decision record: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

```mermaid
flowchart LR
  user[Public Viewer<br/>(anonymous)] -->|Ask questions| gkp[Grounded Knowledge Platform]
  curator[Knowledge Curator<br/>(editor)] -->|Ingest + metadata| gkp
  operator[Client Operator<br/>(admin)] -->|Operate + sync + eval| gkp

  gkp -->|Reads/writes| pg[(Cloud SQL / Postgres)]
  gkp -->|Optional sync (private)| gcs[(Cloud Storage bucket)]
  gkp -->|Logs/metrics| obs[(Cloud Logging / Monitoring)]

  subgraph GCP Project (per client)
    gkp
    pg
    gcs
    obs
  end
```

## Notes

- The public demo is intentionally “boring and safe”: no uploads, no connectors, no eval endpoints.
- Private deployments can enable richer features behind auth, but the default posture remains citations-first.

