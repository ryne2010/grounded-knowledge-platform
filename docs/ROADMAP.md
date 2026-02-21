# Roadmap

This repo is intended to be a **production-grade, citations-first grounded knowledge platform**:

- ingest documents with **governance metadata** (classification, retention, tags)
- answer questions with **evidence-backed citations** (or refuse)
- ship with **measurable quality** (eval harness + safety regression)
- deploy with a **DevSecOps baseline** on GCP (Terraform + Cloud Run + policy gates + runbooks)

Planning front doors:
- Product: `docs/PRODUCT/PRODUCT_BRIEF.md` + `docs/PRODUCT/FEATURE_MATRIX.md`
- Architecture (C4): `docs/ARCHITECTURE/README.md`
- Backlog (epics): `docs/BACKLOG/EPICS.md`

The roadmap below is written to support **agent-driven delivery**: each major item maps to a task template in
`agents/tasks/` with clear acceptance criteria.

---

## Assumptions

Decision record: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

- Public hosting is supported and **safe by default** (`PUBLIC_DEMO_MODE=1`).
- Live/public deployments are **extractive-only** (no external LLM calls).
- Local dev can use **Ollama**.
- Production uses **Cloud SQL Postgres** (baseline).
- **One GCP project per client** (deployment boundary).
- Public demo uses **only the bundled demo corpus** (`data/demo_corpus/`).
- No edge WAF assumed; rely on app rate limiting + Cloud Run instance caps.

## What’s already in place (baseline)

### Product

- Document ingestion: TXT/MD/PDF (+ optional OCR) into Postgres (or SQLite), chunking, optional embeddings.
- Hybrid retrieval (lexical + vector) with caching + invalidation hooks.
- Safety posture: prompt-injection detection and conservative refusal mode.
- Citations-first answering: API enforces citations required by default.
- Public demo mode: read-only, extractive-only, rate limiting, safe caps.
- Evaluation harness:
  - retrieval quality on a golden set (JSONL)
  - prompt-injection regression suite

### Engineering / harness

- Agent “front door”: `AGENTS.md`
- Durable architecture docs: `docs/DOMAIN.md`, `docs/DESIGN.md`, `docs/CONTRACTS.md`
- Mechanical validation harness: `scripts/harness.py` + `harness.toml`
- Role/task templates + checklists: `agents/`

### GCP / DevSecOps

- Terraform-first Cloud Run deployment (remote state, plan/apply separation).
- CI workflows for lint/typecheck/test/build.
- IaC hygiene gates: terraform fmt/validate + tflint + tfsec + checkov + conftest.
- WIF bootstrapping guidance for GitHub Actions.
- Runbooks + incident/release checklists.

---

## Near-term priorities (next 1–2 iterations)

### 1) UI/UX “production polish”

Goal: the app should feel like a real internal tool, not a demo.

Deliverables:

- Design system pass (spacing, typography, color tokens, consistent buttons/forms)
- Better empty states + skeleton loaders + toasts
- Accessibility (keyboard nav, focus states, ARIA)
- Mobile responsive layout
- “Explain this answer” drawer: retrieval breakdown, citations, refusal reason
- Suggested demo queries + lightweight tour (reduce “time to wow”)
- Accessibility audit + baseline checklist

Tracked as: `agents/tasks/TASK_UI_UX_POLISH.md`

Related:
- `agents/tasks/TASK_DEMO_GUIDED_TOUR.md`
- `agents/tasks/TASK_ACCESSIBILITY_AUDIT.md`

Spec: `docs/SPECS/UI_UX_PRODUCTION_POLISH.md`

### 2) Cloud SQL (Postgres) hardening

Goal: make Postgres a **true production baseline** (not just “it works”).

Deliverables:

- versioned migration runner + tracking
- Postgres-native lexical search (FTS) so retrieval doesn’t require loading the full corpus into memory
- pgvector-backed vector search (production baseline)
- local integration test target (`make test-postgres`) and runbook guidance

Tracked as: `agents/tasks/TASK_CLOUDSQL.md`

Spec: `docs/SPECS/CLOUDSQL_HARDENING.md`

### 3) Connector-style ingestion

Goal: support the kinds of ingestion patterns described in the case studies (file feeds, cloud storage events, replays).

Deliverables:

- GCS connector (batch) + idempotent ingest
- Optional Pub/Sub push path for event-driven ingest
- Optional Cloud Scheduler job for periodic sync
- Replay/backfill CLI wrappers
- Ingest lineage enriched with connector source metadata

Tracked as: `agents/tasks/TASK_CONNECTORS_GCS.md`

Related:
- `agents/tasks/TASK_PUBSUB_PUSH_INGEST.md`
- `agents/tasks/TASK_SCHEDULER_PERIODIC_SYNC.md`

Spec: `docs/SPECS/CONNECTOR_GCS_INGESTION.md`

### 4) Per-deployment client boundaries + optional auth

Goal: support **one deployment per client** (hard boundary by infrastructure), while still demonstrating
least-privilege access patterns when needed.

Deliverables:

- Per-client deploy workflow (service naming + state prefix conventions)
- Optional API-key auth for private/internal deployments (reader/editor/admin)
- Audit log events for security-sensitive actions (ingest/delete/config changes)

Non-goal (by default): in-app multi-tenancy/workspaces. That can be added later if the product requires it.

Tracked as: `agents/tasks/TASK_AUTH.md` (today). Optional future: `agents/tasks/TASK_MULTITENANCY_RBAC.md` (only if you ever host multiple workspaces in one deployment).

### 4b) DevSecOps supply-chain scanning (repo hygiene)

Goal: make the repo feel production-grade in a real organization:

- dependency update automation (Dependabot)
- code scanning (CodeQL)
- container vulnerability scanning (report-first)

Tracked as:

- `agents/tasks/TASK_DEPENDABOT_CODE_SCANNING.md`
- `agents/tasks/TASK_CONTAINER_IMAGE_SCANNING.md`

---

## Mid-term priorities

### 5) Evaluation “productization”

Goal: make evaluation results visible and trendable.

Deliverables:

- Persist eval runs (inputs, outputs, metrics, version stamps)
- UI views for eval run history + diffs
- CI job to run a small smoke eval suite

Tracked as: `agents/tasks/TASK_EVAL_PRODUCTIZATION.md`

Related:
- `agents/tasks/TASK_EVAL_CI_SMOKE.md`

### 6) Analytics export / warehouse integration

Goal: connect this system to a governed data platform lifecycle.

Deliverables:

- Export docs/ingest_events/eval_runs to BigQuery (or Postgres)
- Basic dbt-style model notes (raw→curated→marts) for observability datasets

Tracked as: `agents/tasks/TASK_BIGQUERY_EXPORT.md`

---

## How to execute this roadmap (agent workflow)

1. Write/refresh specs in `docs/SPECS/`.
2. Create a focused task doc in `agents/tasks/` with:
   - objective
   - scope / non-goals
   - acceptance criteria
   - implementation notes
   - validation commands
3. Implement in small diffs, keeping the harness green:

```bash
make dev-doctor
```
