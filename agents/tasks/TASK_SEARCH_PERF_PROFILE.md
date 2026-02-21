# Task: Retrieval performance profiling (Postgres)

Related:
- `docs/SPECS/CLOUDSQL_HARDENING.md`
- `docs/ARCHITECTURE/DATA_MODEL.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/postgres_hardening.md`

## Goal

Provide operator-friendly tooling and documentation to verify that retrieval is using indexes and scales beyond the demo corpus.

## Requirements

- Add a small profiling utility (CLI or script) that:
  - runs representative retrieval queries
  - captures `EXPLAIN (ANALYZE, BUFFERS)` for lexical and vector queries
  - outputs a summarized report (not raw dumps only)

- Add documentation:
  - what “good” plans look like (index usage)
  - common failure modes (seq scan, missing extension, bad stats)
  - how to remediate (VACUUM/ANALYZE, reindex, migration)

## Deliverables

- `docs/RUNBOOKS/RETRIEVAL_PERF.md` (new)
- a script/CLI command accessible via Makefile target:
  - `make profile-retrieval` (example)

## Acceptance criteria

- Profiling output clearly indicates whether indexes are being used for FTS and pgvector queries.
- Runbook explains remediation steps for common slow-plan scenarios.

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py test`
