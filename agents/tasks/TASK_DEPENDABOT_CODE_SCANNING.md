# Task: DevSecOps — dependency updates + code scanning

Spec: `docs/SPECS/OBSERVABILITY_OPS.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/security_governance.md`

## Goal

Improve baseline DevSecOps posture by adding:

- Dependabot (Python + npm) for automated dependency update PRs
- Code scanning (CodeQL) for JS/TS + Python

This is especially valuable for a public repo and helps the project feel production-grade.

## Requirements

### Dependabot

- Add `.github/dependabot.yml` with:
  - `pip` (uv/pyproject) updates weekly
  - `npm` (pnpm lockfile under `web/`) updates weekly
  - sensible PR limits

### Code scanning

- Add a GitHub Actions workflow for CodeQL:
  - triggers: push to main + PRs
  - languages: javascript-typescript + python

### Noise control

- Keep alerts actionable:
  - avoid failing CI for low/unknown severity by default
  - but ensure findings are visible

### Docs

- Update `SECURITY.md` with the new CI posture.

## Acceptance criteria

- Dependabot opens update PRs (visible in repo settings).
- CodeQL workflow runs on PRs and main.

## Validation

- Workflows lint (YAML) and pass in CI.

