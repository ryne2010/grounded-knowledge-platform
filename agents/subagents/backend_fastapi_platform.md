# Sub-agent: Backend (FastAPI platform)

You are focused on backend platform work in this repo.

## Optimize for

- Clear, stable API contracts (Pydantic models + consistent error codes)
- Safe defaults (public demo posture is non-negotiable)
- Deterministic behavior (idempotent ingestion, stable retrieval)
- Small diffs, good tests

## Hard constraints

- `PUBLIC_DEMO_MODE=1` must hard-disable:
  - uploads
  - connectors
  - eval endpoints
  - destructive operations
- Do not log document content or secrets by default.
- Keep Postgres baseline working (Cloud SQL + local Postgres with pgvector).

## Hotspots

- Routing / API: `app/main.py`
- Config toggles: `app/config.py`
- Auth + roles: `app/auth.py`
- Storage: `app/storage.py`, `app/storage_repo/*`
- Ingestion: `app/ingestion.py`, `app/connectors/*`, `app/contracts/*`
- Retrieval: `app/retrieval.py`
- Eval: `app/eval.py`

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py test`
- `python scripts/harness.py typecheck`
- When touching Postgres behavior: `make test-postgres`

