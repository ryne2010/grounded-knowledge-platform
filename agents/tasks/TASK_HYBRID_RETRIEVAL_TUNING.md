# Task: Hybrid retrieval tuning (FTS + pgvector)

Related specs:
- `docs/SPECS/CLOUDSQL_HARDENING.md`
- `docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/postgres_hardening.md`

## Goal

Make hybrid retrieval:

- predictable (stable rankings)
- tunable (configurable weights)
- scalable for small-to-medium corpora on Postgres baseline

## Requirements

### Retrieval strategy

- Lexical:
  - Postgres FTS on `chunks.text`
  - avoid full-table scans; confirm index usage

- Vector:
  - pgvector cosine distance query
  - HNSW baseline index

- Merge/rerank:
  - define a stable merge strategy and document it
  - implement weighting knobs (env vars or config)

### Diagnostics

- Add lightweight instrumentation:
  - candidate counts (lexical/vector)
  - retrieval latency breakdown
  - optional debug payload behind feature flag

### Determinism

- same corpus + same query + same config should produce stable results

## Acceptance criteria

- `make test-postgres` exercises retrieval and passes consistently.
- Retrieval config can be changed without code changes (documented env vars).
- A small “retrieval smoke eval” dataset can catch ranking regressions (pairs well with CI smoke eval task).

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py test`
- `python scripts/harness.py typecheck`
- `make test-postgres`
