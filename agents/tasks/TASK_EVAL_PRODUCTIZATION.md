# Task: Evaluation Productization

Spec: `docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`

Owner: @codex
Suggested sub-agent: `agents/subagents/eval_harness.md`

## Objective

Turn eval from a “CLI-only” tool into a **first-class product capability**:

- persist eval runs
- view history + diffs in UI
- enable lightweight CI smoke eval

## Scope

- Data model:
  - new `eval_runs` table (inputs, outputs, metrics, version stamps)
- API:
  - create/run eval
  - list eval runs
  - get eval run details
- UI:
  - history page
  - run detail page with diffs and metrics

## Non-goals

- No advanced statistical significance analysis
- No hosted model benchmarking beyond what the current providers support

## Acceptance criteria

- Eval run metadata includes:
  - app version
  - embeddings backend/model
  - retrieval config (k, hybrid weights)
  - provider config (extractive/openai/gemini)
- UI shows:
  - pass/fail on each case
  - aggregate metrics
  - trend over time (at least simple sparkline)

## Validation

- Unit tests for eval persistence
- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
