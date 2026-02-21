# Task: Cost guardrails (no edge WAF assumed)

Related:
- `docs/COST_HYGIENE.md`
- `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

Spec: `docs/SPECS/OBSERVABILITY_OPS.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/infra_terraform_gcp.md`

## Goal

Keep the public demo cheap and hard to abuse, without relying on Cloud Armor/Cloudflare.

## Requirements

- Terraform guardrails:
  - Cloud Run max instances cap (already exists; verify)
  - request concurrency and timeout defaults
  - budgets and budget alerts (optional but recommended)

- App guardrails:
  - rate limiting on query (already exists; verify)
  - payload size limits

- Docs:
  - `docs/RUNBOOKS/COST_INCIDENT.md` (new)
  - how to respond if costs spike (reduce max instances, restrict invokers temporarily)

## Acceptance criteria

- A new deployment has obvious guardrails with documented knobs.
- “Cost incident” runbook is clear and realistic.

## Validation

- `make tf-check`
