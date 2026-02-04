# Team workflow

This doc explains the **team-friendly patterns** used in this repo.

## Goals

## Onboarding (new teammate)

Recommended first steps:

```bash
# 1) Persist GCP defaults (no exports)
make init GCLOUD_CONFIG=personal-portfolio PROJECT_ID=YOUR_PROJECT_ID REGION=us-central1

# 2) Authenticate (only needed once per machine/user)
make auth

# 3) Verify prerequisites
make doctor

# 4) Deploy the safe Cloud Run demo
make deploy
```

Notes:
- `make init` writes to your active gcloud configuration; if you use `GCLOUD_CONFIG=...` it will create/activate a dedicated config.
- If you change gcloud configs during `make init`, run your next Make command in a fresh invocation.

---

## Pre-commit (catch lint/YAML/Terraform fmt before CI)

This repo includes a `pre-commit` configuration (`.pre-commit-config.yaml`) that runs:
- `ruff` (Python lint)
- `mypy` (Python typecheck)
- `terraform fmt -check` (infra formatting)
- basic YAML + whitespace sanity checks

Setup (one-time per machine):

```bash
uv sync --dev

brew install pre-commit
pre-commit install
```

Run manually:

```bash
pre-commit run --all-files
```

Teaching point:
- Pre-commit makes the “fast feedback loop” local, so CI failures are mostly for things you *couldn’t* reasonably catch on your laptop (integration, permissions, environment drift).

---

- A new teammate can run the project locally and deploy to a sandbox GCP project quickly.
- Infrastructure changes are reviewable (`plan`/`apply` separation) and state is shared safely (remote state).
- Deployments are reproducible (lockfiles, deterministic builds, clear Makefile targets).

---

## Source-control conventions

Recommended:
- `main` is always deployable
- feature branches for changes
- PRs require:
  - `make plan` output attached or pasted (for IaC changes)
  - CI green (lint/test)

---

## Configuration: prefer defaults, allow overrides

The Makefile reads:
- `PROJECT_ID` from `gcloud config get-value project`
- `REGION` from `gcloud config get-value run/region`

But every value can be overridden:

```bash
make deploy PROJECT_ID=my-proj REGION=us-central1 TAG=v1
```

This is key for teams and CI.

---

## Terraform: remote state by default

Why remote state:
- prevents two engineers from corrupting state
- enables auditability and consistent environments

Implementation:
- Terraform directory includes `backend.tf` with `backend "gcs" {}`
- the Makefile passes backend config at init time:
  - bucket: `$(PROJECT_ID)-tfstate` (overrideable)
  - prefix: `gkp/$(ENV)` (override with `TF_STATE_PREFIX=...`)

Bootstrap:

```bash
make bootstrap-state
```

---

## Team IAM (Google Groups)

For realistic enterprise/government workflows, this repo supports group-based IAM in code.

Enable it by providing a Google Workspace domain (Google Groups):

```bash
make plan WORKSPACE_DOMAIN=yourdomain.com
```

See:
- `docs/IAM_STARTER_PACK.md`

---

## CI authentication (WIF)

For CI/CD, use Workload Identity Federation instead of JSON keys.

- baseline example: repo 3 `examples/github_actions_wif/`
- recommended roles:
  - Terraform deploy SA: minimum required roles for Cloud Run/AR/Secret Manager
  - build SA: artifact registry writer

---

## Reproducible dependencies

For team-grade reproducibility, commit lockfiles:

- `uv.lock` (Python)
- `pnpm-lock.yaml` (web)

Generate locally:

```bash
make lock
```

---

## Secrets and sensitive configuration

For a public demo, this repo defaults to:
- no uploads
- extractive-only answering
- no external API keys

If you enable external LLMs:
- prefer Secret Manager in GCP
- never commit API keys to source control

---

## Where to look

- `ARCHITECTURE.md` — system diagram and tradeoffs
- `RUNBOOK.md` — troubleshooting / rollback
- `docs/DEPLOY_GCP.md` — deploy workflow
