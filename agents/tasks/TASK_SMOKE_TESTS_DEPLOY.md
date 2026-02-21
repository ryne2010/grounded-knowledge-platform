# Task: Post-deploy smoke tests (Makefile shortcuts)

Spec: `docs/SPECS/OBSERVABILITY_OPS.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/infra_terraform_gcp.md`

## Goal

Add a lightweight, repeatable “deploy verification” workflow:

- after `make deploy`, run a smoke test suite against the URL:
  - `/health`, `/ready`
  - `/api/meta`
  - a simple `/api/query` request (demo-safe)

## Requirements

- Make targets:
  - `make smoke ENV=prod` (or similar)
  - configurable base URL

- For public demo:
  - smoke query uses demo corpus and is extractive-only
  - no ingestion operations

- Output:
  - clear pass/fail summary
  - prints URL being tested

## Acceptance criteria

- A deploy can be verified in < 30 seconds.
- Failures are actionable (show status codes + key response fields).

## Validation

- local run against `make dev` API
