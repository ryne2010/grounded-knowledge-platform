# Architecture

This repo is a **production-minded reference implementation** of a grounded knowledge system (RAG) with:

- **Citations-first answers** (every claim is tied to retrieved sources)
- **Refusal behavior** when evidence is insufficient
- **Safe public demo posture** (read-only, extractive-only, demo corpus only)
- A pragmatic governance layer (classification, retention, tags)
- A DevSecOps baseline for GCP deployments (Terraform + Cloud Run + Cloud SQL)

Decision record: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

Deeper architecture docs (C4 + models): `docs/ARCHITECTURE/README.md`

---

## High-level flow

```text
                 ┌──────────────────────────────┐
                 │ Document sources              │
                 │ (demo corpus, uploads, GCS)   │
                 └──────────────┬───────────────┘
                                │ ingest
                                v
┌────────────────────────────────────────────────────────┐
│ Ingestion pipeline                                      │
│  - parse text/pdf/tabular                               │
│  - optional OCR (tesseract)                             │
│  - optional contract validation (CSV/XLSX)              │
│  - chunking + hashing                                   │
│  - embeddings (pgvector baseline for Postgres)          │
│  - lineage record (ingest_events)                       │
└──────────────┬─────────────────────────────────────────┘
               │ writes
               v
┌────────────────────────────────────────────────────────┐
│ Storage + indexes (Postgres baseline)                   │
│  - docs / chunks / embeddings / ingest_events           │
│  - FTS (GIN) + pgvector (HNSW)                          │
└──────────────┬─────────────────────────────────────────┘
               │ query
               v
┌────────────────────────────────────────────────────────┐
│ Retrieval + safety                                      │
│  - prompt-injection scan                                │
│  - hybrid retrieval (lexical + vector)                  │
│  - evidence pack + citations                            │
└──────────────┬─────────────────────────────────────────┘
               │ context
               v
┌────────────────────────────────────────────────────────┐
│ Answering                                               │
│  - Public demo: extractive-only                          │
│  - Private: optional LLM providers behind auth           │
│  - citations required / refusal                          │
└──────────────┬─────────────────────────────────────────┘
               │
               v
┌────────────────────────────────────────────────────────┐
│ API + UI                                                │
│  - FastAPI REST endpoints                                │
│  - React/Vite UI (built assets served by API container)  │
│  - structured logs + optional OTEL                       │
└────────────────────────────────────────────────────────┘
```

---

## Deployment mapping (GCP)

Recommended baseline:
- **Cloud Run** for the service (API + UI)
- **Cloud SQL (Postgres)** for persistence (production baseline)
- **Artifact Registry** for images
- **Terraform** for repeatable provisioning
- **Cloud Logging/Monitoring** for ops visibility

See:
- `docs/DEPLOY_GCP.md`
- `docs/DEPLOYMENT_MODEL.md`
- `infra/`

