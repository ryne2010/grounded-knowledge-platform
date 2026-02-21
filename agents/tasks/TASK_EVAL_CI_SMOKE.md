# Task: CI smoke eval gate

Depends on: `agents/tasks/TASK_EVAL_PRODUCTIZATION.md` (or existing eval harness)

Spec: `docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/eval_harness.md`

## Goal

Add a small evaluation suite that runs in CI to catch obvious regressions:

- retrieval failures on a golden set
- refusal behavior regressions
- prompt-injection regression suite

## Requirements

- Add `data/eval/smoke.jsonl` (small, fast)
- CI job runs:
  - `uv run python -m app.cli eval --dataset data/eval/smoke.jsonl`
  - or equivalent API call in a test harness

- Define thresholds:
  - minimum pass rate
  - hard failures for safety regressions

- Keep it fast:
  - < 2 minutes wall clock

## Acceptance criteria

- CI fails when retrieval quality drops below the threshold.
- CI fails on prompt injection regressions.

## Validation

- GitHub Actions run shows eval step and gating behavior.
