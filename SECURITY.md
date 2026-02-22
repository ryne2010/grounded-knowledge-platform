# Security notes

This repository is a **reference implementation**. If you deploy it publicly, treat it like an Internet-facing service.

## Safe public demo configuration

Use `PUBLIC_DEMO_MODE=1` for public demos. When enabled, the service:

- **Disables ingestion endpoints** (no file/text uploads)
- **Disables eval endpoints**
- Forces **extractive-only** answering (no external LLM calls)
- Enables basic in-app rate limiting and clamps query parameters

This significantly reduces the risk of abuse and unintended data storage.

## Sensitive / confidential deployments

If you ingest sensitive documents:

- Prefer a **local embeddings backend** (`EMBEDDINGS_BACKEND=sentence-transformers`)
- Prefer a **local LLM provider** (`LLM_PROVIDER=ollama`) or use `extractive`
- Avoid sending retrieved content to third-party APIs unless you have explicit approval
- Keep `ALLOW_CHUNK_VIEW=0` unless you explicitly need to browse raw chunks. (Retrieval debug will not include full chunk text unless chunk viewing is enabled.)

## Defense in depth (recommended)

- Use **PUBLIC_DEMO_MODE=1** for any Internet-facing deployment (read-only + extractive-only).
- Keep Cloud Run `--max-instances` low (cost and abuse control).
- Keep `RATE_LIMIT_ENABLED=1` (application-level rate limiting).
- Configure budgets and billing alerts in your cloud account.
- Review logging settings so you don't log sensitive content.
- Prefer **one GCP project per client** to keep IAM and cost boundaries clean.

## Continuous security posture (GitHub)

This repo includes baseline DevSecOps automation:

- **Dependabot** (`.github/dependabot.yml`)
  - Weekly Python dependency updates (`pip` / `pyproject.toml` + `uv.lock`)
  - Weekly web dependency updates (`npm` for `web/` + `pnpm-lock.yaml`)
  - Minor/patch updates are grouped to reduce PR noise

- **Code scanning (CodeQL)** (`.github/workflows/codeql.yml`)
  - Runs on pushes to `main`, pull requests targeting `main`, and weekly schedule
  - Analyzes both `python` and `javascript-typescript`
  - Findings are surfaced in GitHub Security code-scanning alerts

- **Container image scanning (Trivy)** (`.github/workflows/container-image-scan.yml`)
  - Builds the app container image from `docker/Dockerfile` on `main` and PRs
  - Produces SARIF + JSON reports
  - Uploads SARIF to GitHub Security and keeps JSON/SARIF as workflow artifacts
  - Optional strict gate via repository variable `IMAGE_SCAN_FAIL_ON_SEVERITY` (for example `CRITICAL,HIGH`)

Noise control:
- CodeQL alerts are visible in GitHub Security, but by default findings are triaged there rather than blocking merges by severity.
- Container scan reports are non-blocking by default; enable strict blocking with `IMAGE_SCAN_FAIL_ON_SEVERITY`.
- Workflow failures still fail CI when scanning execution itself fails.
