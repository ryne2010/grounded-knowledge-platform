# C4 — Component diagram

The API is organized into a small set of modules with clear responsibilities.

```mermaid
flowchart LR
  subgraph API[FastAPI app]
    routes[HTTP routes<br/>app/main.py]
    auth[Auth + roles<br/>app/auth.py]
    safety[Safety gates<br/>app/safety.py]
    ingest[Ingestion<br/>app/ingestion.py]
    contracts[Contracts + validation<br/>app/contracts/*]
    connectors[Connectors (private)<br/>app/connectors/*]
    retrieval[Retrieval<br/>app/retrieval.py]
    answering[Answering<br/>app/answering.py]
    eval[Eval harness (private)<br/>app/eval.py]
    storage[Storage adapter<br/>app/storage.py + storage_repo/*]
    obs[Observability<br/>app/observability.py + otel.py]
  end

  routes --> auth
  routes --> safety
  routes --> ingest
  ingest --> contracts
  ingest --> storage
  connectors --> ingest
  routes --> retrieval
  retrieval --> storage
  routes --> answering
  answering --> retrieval
  routes --> eval
  eval --> retrieval
  routes --> obs
  storage --> pg[(Postgres / Cloud SQL)]
```

## Key invariants

- `PUBLIC_DEMO_MODE=1` disables privileged operations (uploads, connectors, eval).
- Citations are required by default; refusal is used when evidence is insufficient.
- Connectors are add/update only (no deletions) and require admin role.

