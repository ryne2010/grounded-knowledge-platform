# Spec: Eval harness productization

## Context

This repo positions “measurable quality” as a differentiator: retrieval quality and safety regressions should be detectable and reviewable over time.

Today, evaluation exists as a concept (demo datasets, planned tasks). We want a **small but real** eval system that supports:

- repeatable eval runs
- CI smoke gating
- operator-visible results (private deployments)

## Goals

- Define a durable eval dataset format for **retrieval quality** and **safety**.
- Provide a repeatable eval runner (CLI + optional API).
- Persist eval runs + results in Postgres (private deployments only).
- Add a CI smoke gate that prevents obvious regressions.

## Non-goals

- Full benchmark suite with model comparisons
- Expensive LLM judging by default (keep costs low)
- Public demo eval endpoints

## Proposed design

### User experience

- **Public demo:**
  - No eval endpoints
  - Optional “read-only” page that explains evaluation philosophy (docs)

- **Private deployment:**
  - Admin can run an eval.
  - Admin can view:
    - latest run summary
    - failures (which query, which expected doc evidence)
    - trendline over time (optional)

### Dataset format

Store datasets under `data/eval/`:

- `dataset.jsonl` (one case per line)

Example case:

```json
{"id":"q-001","query":"How do I reset my password?","expect":{"type":"must_cite","doc_ids":["doc-123"]}}
```

Supported expectation types:

- `must_cite`: response must cite at least one of `doc_ids`
- `must_refuse`: response must be a refusal (no evidence)

### API surface

- CLI (baseline):
  - `gkp_cli eval run --dataset data/eval/dataset.jsonl --out dist/eval/<run_id>.json`

Optional private API:

- `POST /api/eval/run` (admin only; disabled in `PUBLIC_DEMO_MODE`)
- `GET /api/eval/runs` (admin only)
- `GET /api/eval/runs/{id}` (admin only)

### Data model

Add tables (private deployments):

- `eval_runs`
  - `id`, `started_at`, `finished_at`, `dataset_name`, `git_sha`, `mode`, `summary_json`
- `eval_results`
  - `run_id`, `case_id`, `status` (`pass`/`fail`), `details_json`

### Security / privacy

- Eval endpoints are **admin-only**.
- Eval endpoints are disabled unless `ALLOW_EVAL=1`.
- Eval endpoints are disabled in `PUBLIC_DEMO_MODE`.

### Observability

- Log eval runs with request id + run id.
- Emit basic metrics (future OTEL): run duration, pass rate.

### Rollout / migration

- Start with the CLI runner.
- Add CI smoke gate using a tiny dataset.
- Add persistence + UI in private deployments.

## Alternatives considered

- LLM-as-a-judge scoring: useful, but introduces cost and non-determinism.
- Full IR metrics suite (nDCG, MRR): can be added later.

## Acceptance criteria

- A dataset can be run locally and in CI.
- CI fails when pass rate drops below a configured threshold.
- In private deployments, eval runs and results can be persisted and viewed.

## Validation plan

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
