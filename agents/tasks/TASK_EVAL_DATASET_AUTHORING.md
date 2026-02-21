# Task: Eval dataset authoring guide + tooling

Spec: `docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/eval_harness.md`

## Goal

Make it easy to add high-quality eval cases:

- clear dataset format and examples
- repeatable authoring workflow
- guidance on avoiding flaky cases

## Requirements

- Docs:
  - `docs/EVAL_DATASETS.md` (new)
  - includes:
    - JSONL schema
    - examples for “answerable” and “should refuse”
    - how to update the dataset safely

- Tooling:
  - CLI helper to validate dataset format:
    - `app.cli validate-eval-dataset path.jsonl`

- Golden set discipline:
  - cases reference demo corpus docs where possible
  - avoid ambiguous questions

## Acceptance criteria

- A new contributor can add a case and run `make eval-smoke` locally.
- Dataset validator catches malformed rows and missing fields.

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
