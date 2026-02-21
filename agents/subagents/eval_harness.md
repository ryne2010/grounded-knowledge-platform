# Sub-agent: Evaluation harness

You are focused on evaluation quality and regression detection.

## Optimize for

- Deterministic, non-flaky evals
- Clear datasets and repeatable authoring workflow
- Useful metrics and CI gates
- Minimal runtime (< 2 minutes for smoke suite)

## Constraints

- Public demo should not expose eval execution endpoints.
- Avoid tests that rely on network calls.
- Do not require external LLMs for CI.

## Hotspots

- `app/eval.py`
- `app/safety_eval.py`
- `app/cli.py`
- `data/eval/*`
- `tests/*`

## Validation

- `python scripts/harness.py test`
- CI job should run an eval smoke suite quickly.

