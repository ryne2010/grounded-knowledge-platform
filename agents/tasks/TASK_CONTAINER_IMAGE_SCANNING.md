# Task: DevSecOps — container image vulnerability scanning

Spec: `docs/SPECS/OBSERVABILITY_OPS.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/security_governance.md`

## Goal

Add CI scanning of the built container image to surface vulnerabilities early.

## Requirements

- Add a GitHub Actions workflow that:
  - builds the image (or pulls the build artifact)
  - runs a vulnerability scanner (e.g., Trivy)
  - uploads results as artifacts and/or GitHub Security tab (SARIF) if supported

- Keep the baseline posture pragmatic:
  - report vulnerabilities by default
  - optionally fail CI only on critical/high (configurable)

## Acceptance criteria

- Workflow runs on PRs and produces a vulnerability report.
- Results are visible (artifact or security tab).

## Validation

- Workflow passes on main.

