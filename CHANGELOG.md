# Changelog

All notable changes to this repository will be documented here.

The project follows (roughly) [Keep a Changelog](https://keepachangelog.com/) and semantic versioning.

## Unreleased

### Added

- Optional API authentication and role-based authorization (`AUTH_MODE`, API keys, `reader/editor/admin` roles).
- Streaming query endpoint (`POST /api/query/stream`) with SSE events (`retrieval`, `token`, `citations`, `done`, `error`).
- PWA support for the web app:
  - install manifest + icons
  - service worker with safe caching strategies
  - offline UX banners/states in key pages
- Data contracts for tabular ingest (`contract_file`) with schema fingerprinting, validation results, and drift tracking in lineage.
- Optional OpenTelemetry setup for FastAPI with targeted spans for safety scan, retrieval, and answer generation.
- Provider-native streaming hooks for OpenAI/Gemini in SSE query mode.
- OTEL metric instruments for request and query-stage latency.
- Storage repository abstraction with initial Postgres/Cloud SQL scaffolding and local Postgres integration tests.
- Cloud SQL Terraform module wiring and Cloud Run integration options.
- New runbook: `docs/RUNBOOKS/CLOUDSQL.md`.
- Release tooling script: `scripts/release_tools.py` (`bump`, `notes`).
- New release process guide: `docs/RELEASES.md`.
- Dependabot configuration for weekly Python (`pip`) and web (`npm`) dependency update PRs.
- CodeQL workflow for Python + JavaScript/TypeScript code scanning on `main` and PRs.
- Container image vulnerability scanning workflow (Trivy) on PRs and `main` with SARIF + JSON outputs.
- BigQuery export module + CLI (`export-bigquery`) for private deployments, with idempotent JSONL snapshots and optional direct BigQuery loads for `docs`, `ingest_events`, and `eval_runs`.
- New runbook: `docs/RUNBOOKS/BIGQUERY_EXPORT.md`.
- BigQuery modeling guide (`docs/BIGQUERY_MODELING.md`) with raw->curated->marts conventions.
- Example BigQuery model SQL under `infra/bigquery_models/{raw,curated,marts}` for ingestion freshness, query latency, eval pass rates, and ops/governance marts.

### Changed

- `/api/meta` now reports auth and storage backend context (`auth_mode`, `database_backend`).
- Ingest lineage APIs/UI now surface contract validation status, errors, and schema drift indicators.
- Runtime storage operations now switch to Postgres when `DATABASE_URL` is configured.
- Docs and deployment guides updated for auth, OTEL, streaming, PWA, data contracts, and Cloud SQL.
- Makefile now includes `release-bump` and `release-notes` targets for consistent release/version workflows.
- `SECURITY.md` now documents the repo's continuous security posture (Dependabot + CodeQL) and alert triage model.
- `SECURITY.md` now includes container image scan posture and optional strict severity-gate config.
- Product docs now mark BigQuery export as available for private deployments.
- Portfolio alignment docs now reflect implemented BigQuery export + modeling assets.
- Service worker API caching is now restricted to low-risk read endpoints (`/api/meta`, `/api/docs`, `/api/stats`) to avoid persisting sensitive/private API responses.
- Makefile now includes `web-dev` as an explicit alias for the Vite UI dev server workflow.
- Streaming API contract docs now explicitly define terminal `done` semantics and document optional `done.explain` payload parity with `/api/query`.
- Cloud SQL contract/runbook docs now explicitly document `DATABASE_URL` Postgres behavior, `pgvector` baseline requirements, and migration tracking via `schema_migrations`.
- Connector contract docs now explicitly pin GCS sync `max_objects` bounds (`1..5000`) and reaffirm add/update-only behavior.
- Hybrid retrieval now supports runtime tuning knobs (`RETRIEVAL_*`) for candidate limits/weights, logs optional diagnostics (`RETRIEVAL_DEBUG_STATS`), and surfaces candidate limits in eval metadata.

### Fixed

- SQLite ingest-event ordering now uses a deterministic tie-breaker for same-second ingests.
- Streaming SSE tests now read response bodies correctly from streaming responses.
- Added explicit invariant regression tests to keep demo mode safety constraints and citations-required behavior enforced.
- Streaming regression tests now include direct SSE frame helper validation and stronger `done`/event-order assertions.
- Cloud SQL integration tests now verify Postgres migrations are recorded and required retrieval indexes (`GIN` FTS + `HNSW` pgvector) exist.
- Added GCS sync safety regression tests for public-demo gating, admin-only access, and max-object bounds; idempotent reruns now assert per-result `changed=false`.
- Hybrid retrieval ranking now uses deterministic tie-break ordering across SQLite and Postgres for equal-score candidates.

## 0.10.0

### Fixed

- Fixed a runtime `NameError` in the readiness probe logging path.
- Fixed a type-check edge case in retrieval eval metrics (MRR).
- Fixed SQLite FTS5 index maintenance to avoid duplicate rows by relying on triggers.

### Added

- `make clean` and `make dist` targets:
  - `make clean` removes local caches/build artifacts.
  - `make dist` creates a clean source ZIP that excludes build artifacts and secrets.
- `scripts/package_repo.py` and `scripts/clean.sh` to support the targets above.
- Docs UI: added retention + status columns (expired/active/kept).

### Changed

- Web install now uses `pnpm install --frozen-lockfile` for reproducible builds.

## 0.9.0

- Prior hardened release.
