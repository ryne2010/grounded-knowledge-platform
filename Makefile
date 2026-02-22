# Grounded Knowledge Platform — team-ready workflow (Makefile)
#
# This Makefile is intentionally "staff-level": it optimizes for teams.
#
# Design principles:
# - No manual `export ...` required (defaults come from `gcloud config`)
# - Reproducible: every value can be overridden on the command line
# - Remote Terraform state by default (GCS backend)
# - Plan/apply separation ("plan" is a first-class action)
# - Safe-by-default Cloud Run demo deployment (PUBLIC_DEMO_MODE=1)
#
# Typical flows:
#   make doctor
#   make bootstrap-state      # create tfstate bucket
#   make infra                # apply prerequisite infra (APIs/AR/service accounts)
#   make plan                 # terraform plan
#   make apply                # terraform apply
#   make deploy               # infra + build image (Cloud Build) + apply + smoke
#
# Overrides (team/CI friendly):
#   make deploy PROJECT_ID=my-proj REGION=us-central1 TAG=v1
#
# Notes:
# - For Apple Silicon (M1/M2/M3), we default to Cloud Build to avoid cross-arch Docker issues.
# - Remote state bucket is created via `gcloud storage` (override TF_STATE_BUCKET if needed).
# - CI should use Workload Identity Federation (WIF); see docs/TEAM_WORKFLOW.md.

SHELL := /bin/bash

# -----------------------------
# Config (defaults from gcloud)
# -----------------------------
PROJECT_ID ?= $(shell gcloud config get-value project 2>/dev/null)
REGION     ?= $(shell gcloud config get-value run/region 2>/dev/null)
REGION     ?= us-central1

# Environment label used for state prefix + labels.
ENV ?= dev

# Cloud Run service naming
SERVICE_NAME ?= gkp-$(ENV)

# Artifact Registry + image
AR_REPO     ?= gkp
IMAGE_NAME  ?= gkp
TAG         ?= latest

# Terraform root for the Cloud Run deployment
TF_DIR ?= infra/gcp/cloud_run_demo

# Remote Terraform state
# Bucket names must be globally unique; using PROJECT_ID is usually sufficient.
TF_STATE_BUCKET ?= $(PROJECT_ID)-tfstate
TF_STATE_PREFIX ?= gkp/$(ENV)
# Workspace IAM starter pack (optional; Google Groups)
WORKSPACE_DOMAIN ?=
GROUP_PREFIX ?= gkp
CLIENTS_OBSERVERS_GROUP_EMAIL ?=
ENABLE_CLIENTS_OBSERVERS_MONITORING_VIEWER ?= false

# Observability as code
ENABLE_OBSERVABILITY ?= true
DELETION_PROTECTION ?= false

# -----------------------------
# Local/API convenience (optional)
# -----------------------------
# Used for curl-driven operator actions against a running API.
GKP_API_URL ?= http://127.0.0.1:8080
GKP_API_KEY ?=

# Deploy smoke checks.
SMOKE_URL ?=
SMOKE_QUERY ?= Why use Cloud SQL for persistence?
SMOKE_TIMEOUT_S ?= 8
SMOKE_RETRIES ?= 2
SMOKE_RETRY_DELAY_S ?= 2
SMOKE_API_KEY ?=

# GCS connector convenience vars (private deployments only).
GCS_BUCKET ?=
GCS_PREFIX ?=
GCS_MAX_OBJECTS ?= 200
GCS_DRY_RUN ?= true


# Derived image URI (no exports required)
IMAGE := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(AR_REPO)/$(IMAGE_NAME):$(TAG)

# -----------------------------
# Helpers
# -----------------------------

define require
	@command -v $(1) >/dev/null 2>&1 || (echo "Missing dependency: $(1)"; exit 1)
endef

.PHONY: help init auth doctor config bootstrap-state tf-init infra grant-cloudbuild plan apply build deploy url verify smoke smoke-local logs destroy lock release-bump release-notes clean dist gcs-sync task-index queue codex-prompt backlog-export backlog-refresh backlog-audit bigquery-export profile-retrieval

help:
	@echo "Targets:"
	@echo "  doctor            Check prerequisites and print resolved config"
	@echo "  init              One-time setup: persist gcloud project/region (optional GCLOUD_CONFIG)"
	@echo "  auth              Authenticate gcloud user + ADC (interactive)"
	@echo "  config            (Optional) Create/activate a dedicated gcloud config (GCLOUD_CONFIG=...)"
	@echo "  bootstrap-state   Create the remote Terraform state bucket (GCS)"
	@echo "  tf-init           Terraform init with GCS backend-config"
	@echo "  infra             Apply prerequisite infra (APIs, Artifact Registry, service accounts)"
	@echo "  plan              Terraform plan (uses remote state)"
	@echo "  apply             Terraform apply (deploy Cloud Run)"
	@echo "  build             Build+push image with Cloud Build"
	@echo "  deploy            infra + build + apply + smoke"
	@echo "  url               Print Cloud Run service URL"
	@echo "  verify            Hit /health and /api/meta"
	@echo "  smoke             Post-deploy smoke suite (/health,/ready,/api/meta,/api/query)"
	@echo "  smoke-local       Smoke suite against local API (default $(GKP_API_URL))"
	@echo "  logs              Read recent Cloud Run logs"
	@echo "  destroy           Terraform destroy (does NOT delete tfstate bucket)"
	@echo "  lock              Generate lockfiles locally (uv.lock + pnpm-lock.yaml)"
	@echo ""
	@echo "Local dev / quality:"
	@echo "  db-up              Start local Postgres (Docker Compose)"
	@echo "  db-down            Stop local Postgres"
	@echo "  db-reset           Reset local Postgres volume (DANGEROUS)"
	@echo "  db-logs            Tail local Postgres logs"
	@echo "  db-psql            Open psql inside the local Postgres container"
	@echo "  py-install         Install Python deps (dev) via uv"
	@echo "  web-install        Install web deps via Corepack pnpm"
	@echo "  web-typecheck      Typecheck web (tsc)"
	@echo "  web-lint           Lint web (currently typecheck-only)"
	@echo "  run-api            Run API locally (http://127.0.0.1:8080)"
	@echo "  run-ui             Run UI locally (http://127.0.0.1:5173)"
	@echo "  web-dev            Alias for run-ui (Vite dev server)"
	@echo "  dev                Run API + UI concurrently"
	@echo "  dev-doctor         Run full local quality harness"
	@echo "  dev-ci             Run CI harness locally (same as GitHub Actions)"
	@echo "  test-postgres      Run Postgres integration tests (Docker + psycopg)"
	@echo "  profile-retrieval  Profile Postgres retrieval plans (EXPLAIN ANALYZE BUFFERS)"
	@echo "  eval-smoke         Run CI-style eval smoke gate locally"
	@echo "  gcs-sync           Trigger GCS connector sync via API (private deployments only)"
	@echo "  bigquery-export    Export docs/ingest/eval datasets (JSONL + optional BigQuery load)"
	@echo "  release-bump       Bump release version + roll CHANGELOG Unreleased (set VERSION=x.y.z)"
	@echo "  release-notes      Generate release notes from CHANGELOG (set VERSION=x.y.z)"
	@echo "  clean              Remove local caches/build artifacts"
	@echo "  dist               Create a clean source ZIP in dist/"
	@echo "  task-index         Regenerate docs/BACKLOG/TASK_INDEX.md"
	@echo "  queue              Regenerate docs/BACKLOG/QUEUE.md"
	@echo "  codex-prompt        Generate a codex prompt pack (TASK=agents/tasks/TASK_*.md)"
	@echo "  backlog-export     Export tasks as GitHub-issue artifacts in dist/github_issues/"
	@echo "  backlog-refresh    Regenerate task-index + queue"
	@echo "  backlog-audit      Audit planning artifacts + task metadata (codex-ready check)"
	@echo ""
	@echo "Resolved config (override with VAR=...):"
	@echo "  PROJECT_ID=$(PROJECT_ID)"
	@echo "  REGION=$(REGION)"
	@echo "  ENV=$(ENV)"
	@echo "  SERVICE_NAME=$(SERVICE_NAME)"
	@echo "  WORKSPACE_DOMAIN=$(WORKSPACE_DOMAIN)"
	@echo "  GROUP_PREFIX=$(GROUP_PREFIX)"
	@echo "  CLIENTS_OBSERVERS_GROUP_EMAIL=$(CLIENTS_OBSERVERS_GROUP_EMAIL)"
	@echo "  ENABLE_CLIENTS_OBSERVERS_MONITORING_VIEWER=$(ENABLE_CLIENTS_OBSERVERS_MONITORING_VIEWER)"
	@echo "  ENABLE_OBSERVABILITY=$(ENABLE_OBSERVABILITY)"
	@echo "  DELETION_PROTECTION=$(DELETION_PROTECTION)"
	@echo "  IMAGE=$(IMAGE)"
	@echo "  TF_STATE_BUCKET=$(TF_STATE_BUCKET)"
	@echo "  TF_STATE_PREFIX=$(TF_STATE_PREFIX)"

# -----------------------------
# Local development (no GCP required)
# -----------------------------

.PHONY: py-install web-install db-up db-down db-reset db-logs db-psql run-api run-ui web-dev dev web-build web-lint web-typecheck lint typecheck test test-postgres dev-doctor dev-ci


# Connectors (private deployments)
gcs-sync: ## Trigger GCS prefix sync via API (add/update only; disabled in PUBLIC_DEMO_MODE)
	@if [ -z "$(GCS_BUCKET)" ]; then \
		echo "ERROR: set GCS_BUCKET=..."; \
		exit 1; \
	fi
	@HDR=""; \
	if [ -n "$(GKP_API_KEY)" ]; then HDR="-H x-api-key:$(GKP_API_KEY)"; fi; \
	echo "POST $(GKP_API_URL)/api/connectors/gcs/sync (bucket=$(GCS_BUCKET) prefix=$(GCS_PREFIX) dry_run=$(GCS_DRY_RUN))"; \
	curl -sS -X POST "$(GKP_API_URL)/api/connectors/gcs/sync" \
	  -H "Content-Type: application/json" \
	  $$HDR \
	  -d '{"bucket":"$(GCS_BUCKET)","prefix":"$(GCS_PREFIX)","max_objects":$(GCS_MAX_OBJECTS),"dry_run":$(GCS_DRY_RUN)}'


# Local Postgres (Docker Compose)
# These targets provide a local Postgres that matches the Cloud SQL baseline.
#
# Requires Docker Desktop.

db-up: ## Start local Postgres (Docker Compose)
	docker compose up -d db

db-down: ## Stop local Postgres
	docker compose down

db-reset: ## Reset local Postgres volume (DANGEROUS)
	docker compose down -v

db-logs: ## Tail local Postgres logs
	docker compose logs -f db

db-psql: ## Open psql inside the local Postgres container
	docker compose exec db psql -U gkp -d gkp

py-install: ## Install Python deps (dev) via uv
	uv sync --dev --extra cloudsql --extra observability

web-install: ## Install web deps via Corepack pnpm
	cd web && corepack pnpm install --frozen-lockfile

run-api: ## Run API locally (http://127.0.0.1:8080)
	uv run uvicorn app.main:app --reload --port 8080

run-ui: ## Run UI locally (http://127.0.0.1:5173)
	cd web && corepack pnpm dev

web-dev: run-ui ## Alias for run-ui (Vite dev server)

dev: ## Run API + UI concurrently (two terminals is still recommended for logs)
	@bash -euo pipefail -c '\
	  (make run-api) & api_pid=$$!; \
	  (make run-ui) & ui_pid=$$!; \
	  trap "kill $$api_pid $$ui_pid 2>/dev/null || true" INT TERM EXIT; \
	  wait $$api_pid $$ui_pid; \
	'

web-build: ## Build web bundle into web/dist
	cd web && corepack pnpm build

web-typecheck: ## Typecheck web (tsc)
	cd web && corepack pnpm run typecheck

web-lint: ## Lint web (currently typecheck-only)
	cd web && corepack pnpm run lint

lint: ## Lint (ruff)
	uv run python scripts/harness.py lint

typecheck: ## Typecheck (mypy + tsc)
	uv run python scripts/harness.py typecheck

test: ## Run unit tests (pytest)
	uv run python scripts/harness.py test

test-postgres: ## Run Postgres integration tests (requires Docker + psycopg)
	uv run python -m pytest -q tests/test_cloudsql_postgres.py tests/test_cloudsql_runtime.py


# -----------------------------
# App CLI shortcuts (eval / safety / maintenance)
# -----------------------------
GOLDEN ?= data/eval/golden.jsonl
SMOKE_DATASET ?= data/eval/smoke.jsonl
SUITE  ?= data/eval/prompt_injection.jsonl
BASE   ?= http://127.0.0.1:8080
ENDPOINT ?= /api/query
K ?= 5
MIN_PASS_RATE ?= 0.80
BQ_PROJECT ?= $(PROJECT_ID)
BQ_DATASET ?=
BQ_TABLE_PREFIX ?= gkp_
BQ_LOCATION ?=
BQ_JSONL_DIR ?= dist/bigquery_export/raw
BQ_BATCH_SIZE ?= 500
BQ_JSONL_ONLY ?= true
PROFILE_TENANT_ID ?= default
PROFILE_TOP_K ?= 40
PROFILE_QUERY ?=
PROFILE_JSON_OUT ?=
PROFILE_INCLUDE_PLANS ?= false

.PHONY: eval eval-smoke safety-eval retention-sweep retention-sweep-apply purge-expired purge-expired-apply bigquery-export profile-retrieval

eval: ## Run retrieval evaluation on a golden set (JSONL)
	uv run python -m app.cli eval $(GOLDEN) --k $(K)

eval-smoke: ## Run fast eval smoke gate (retrieval threshold + refusal/safety regressions)
	uv run python scripts/eval_smoke_gate.py --dataset $(SMOKE_DATASET) --prompt-suite $(SUITE) --k $(K) --min-pass-rate $(MIN_PASS_RATE)

safety-eval: ## Run prompt-injection safety regression (JSONL)
	uv run python -m app.cli safety-eval $(SUITE) --base $(BASE) --endpoint $(ENDPOINT) --k $(K)

retention-sweep: ## Dry-run: list docs whose retention policy has expired
	uv run python -m app.cli retention-sweep

retention-sweep-apply: ## Delete docs whose retention policy has expired (DANGEROUS)
	uv run python -m app.cli retention-sweep --apply

purge-expired: retention-sweep ## Deprecated alias: use retention-sweep

purge-expired-apply: retention-sweep-apply ## Deprecated alias: use retention-sweep-apply

bigquery-export: ## Export docs/ingest/eval datasets to JSONL and optionally load BigQuery
	@set -euo pipefail; \
	CMD=(uv run python -m app.cli export-bigquery \
	  --jsonl-dir "$(BQ_JSONL_DIR)" \
	  --table-prefix "$(BQ_TABLE_PREFIX)" \
	  --batch-size "$(BQ_BATCH_SIZE)"); \
	if [ "$(BQ_JSONL_ONLY)" = "true" ]; then \
	  CMD+=(--jsonl-only); \
	else \
	  if [ -z "$(BQ_PROJECT)" ] || [ -z "$(BQ_DATASET)" ]; then \
	    echo "Set BQ_PROJECT and BQ_DATASET (or keep BQ_JSONL_ONLY=true)."; \
	    exit 1; \
	  fi; \
	  CMD+=(--project "$(BQ_PROJECT)" --dataset "$(BQ_DATASET)"); \
	  if [ -n "$(BQ_LOCATION)" ]; then \
	    CMD+=(--location "$(BQ_LOCATION)"); \
	  fi; \
	fi; \
	"$${CMD[@]}"

profile-retrieval: ## Profile Postgres retrieval plans (EXPLAIN ANALYZE BUFFERS)
	@set -euo pipefail; \
	CMD=(uv run python -m app.cli profile-retrieval \
	  --tenant-id "$(PROFILE_TENANT_ID)" \
	  --top-k "$(PROFILE_TOP_K)"); \
	if [ -n "$(PROFILE_QUERY)" ]; then \
	  CMD+=(--query "$(PROFILE_QUERY)"); \
	fi; \
	if [ "$(PROFILE_INCLUDE_PLANS)" = "true" ]; then \
	  CMD+=(--include-plans); \
	fi; \
	if [ -n "$(PROFILE_JSON_OUT)" ]; then \
	  CMD+=(--json-out "$(PROFILE_JSON_OUT)"); \
	fi; \
	"$${CMD[@]}"

dev-doctor: ## Run full local quality harness
	bash scripts/doctor.sh

dev-ci: ## Run CI harness locally (same as GitHub Actions)
	bash scripts/ci.sh

# -----------------------------
# Init (team onboarding)
# -----------------------------
# `make init` is the recommended onboarding step for new teammates.
#
# It persists `PROJECT_ID` and `REGION` into your active gcloud configuration so you can run:
#   make deploy
# without copy/pasting `export ...` blocks.
#
# Usage (recommended for teams):
#   make init GCLOUD_CONFIG=personal-portfolio PROJECT_ID=my-proj REGION=us-central1
#
# Usage (current gcloud config):
#   make init PROJECT_ID=my-proj REGION=us-central1
#
# Notes:
# - This target does NOT create projects or enable billing.
# - This target does NOT run Terraform; it only configures gcloud defaults and prints next steps.
# - If you switch gcloud configs in this command, re-run your next make command in a fresh invocation.
init:
	$(call require,gcloud)
	@bash -euo pipefail -c '\
	  echo "== Init: configure gcloud defaults =="; \
	  cfg="$${GCLOUD_CONFIG:-}"; \
	  proj="$(PROJECT_ID)"; \
	  region="$(REGION)"; \
	  if [ -n "$$cfg" ]; then \
	    if gcloud config configurations describe "$$cfg" >/dev/null 2>&1; then \
	      :; \
	    else \
	      echo "Creating gcloud configuration: $$cfg"; \
	      gcloud config configurations create "$$cfg" >/dev/null; \
	    fi; \
	    echo "Activating gcloud configuration: $$cfg"; \
	    gcloud config configurations activate "$$cfg" >/dev/null; \
	  fi; \
	  if [ -z "$$proj" ]; then proj="$$(gcloud config get-value project 2>/dev/null || true)"; fi; \
	  if [ -z "$$region" ]; then region="$$(gcloud config get-value run/region 2>/dev/null || true)"; fi; \
	  if [ -z "$$proj" ]; then \
	    echo "ERROR: PROJECT_ID is not set."; \
	    echo "Fix: make init PROJECT_ID=<your-project-id> REGION=<region> [GCLOUD_CONFIG=name]"; \
	    exit 1; \
	  fi; \
	  if [ -z "$$region" ]; then \
	    echo "ERROR: REGION is not set."; \
	    echo "Fix: make init PROJECT_ID=<your-project-id> REGION=<region> [GCLOUD_CONFIG=name]"; \
	    exit 1; \
	  fi; \
	  echo "Setting gcloud defaults..."; \
	  gcloud config set project "$$proj" >/dev/null; \
	  gcloud config set run/region "$$region" >/dev/null; \
	  # Fix ADC quota project warning if ADC exists (non-fatal). \
	  gcloud auth application-default set-quota-project "$$proj" >/dev/null 2>&1 || true; \
	  active="$$(gcloud config configurations list --filter=is_active:true --format=value\(name\) 2>/dev/null | head -n1)"; \
	  echo ""; \
	  echo "Configured:"; \
	  echo "  project: $$proj"; \
	  echo "  region:  $$region"; \
	  echo "  gcloud config: $${active:-default}"; \
	  echo ""; \
	  acct="$$(gcloud auth list --filter=status:ACTIVE --format=value\(account\) 2>/dev/null | head -n1 || true)"; \
	  if [ -z "$$acct" ]; then \
	    echo "Auth status: not logged in"; \
	    echo "Next: make auth"; \
	  else \
	    echo "Auth status: $$acct"; \
	  fi; \
	  echo ""; \
	  echo "Next steps:"; \
	  echo "  make doctor"; \
	  echo "  make deploy"; \
	  echo ""; \
	  echo "Tip: if you changed gcloud configs, run the next make command in a fresh invocation." \
	'


# Interactive auth helper (explicit on purpose).
# This will open browser windows for OAuth flows.
auth:
	$(call require,gcloud)
	@echo "This will open a browser window for gcloud login + ADC."
	gcloud auth login
	gcloud auth application-default login

# Validate tools + config.
# We intentionally DO NOT attempt to auto-enable billing or auto-create projects.
# -----------------------------
# Doctor (prerequisite checks)
# -----------------------------
# `make doctor` is the preferred first step for teammates.
#
# It prints the resolved configuration and checks that you have the tools needed for:
# - Cloud deploy lane (Terraform + gcloud)
# - Optional local dev lane (uv + Node/pnpm)
#
# The target exits non-zero if the **Cloud deploy** prerequisites are missing.
doctor:
	@set -e; \
	fail=0; \
	echo "== Doctor: Grounded Knowledge Platform =="; \
	echo ""; \
	echo "Resolved config (override with VAR=...):"; \
	echo "  PROJECT_ID=$(PROJECT_ID)"; \
	echo "  REGION=$(REGION)"; \
	echo "  ENV=$(ENV)"; \
	echo "  SERVICE_NAME=$(SERVICE_NAME)"; \
	echo "  WORKSPACE_DOMAIN=$(WORKSPACE_DOMAIN)"; \
	echo "  GROUP_PREFIX=$(GROUP_PREFIX)"; \
	echo "  CLIENTS_OBSERVERS_GROUP_EMAIL=$(CLIENTS_OBSERVERS_GROUP_EMAIL)"; \
	echo "  ENABLE_CLIENTS_OBSERVERS_MONITORING_VIEWER=$(ENABLE_CLIENTS_OBSERVERS_MONITORING_VIEWER)"; \
	echo "  ENABLE_OBSERVABILITY=$(ENABLE_OBSERVABILITY)"; \
	echo "  IMAGE=$(IMAGE)"; \
	echo "  TF_STATE_BUCKET=$(TF_STATE_BUCKET)"; \
	echo "  TF_STATE_PREFIX=$(TF_STATE_PREFIX)"; \
	echo ""; \
	echo "Cloud deploy prerequisites (required):"; \
	if command -v gcloud >/dev/null 2>&1; then \
	  echo "  ✓ gcloud: $$(gcloud --version 2>/dev/null | head -n1)"; \
	else \
	  echo "  ✗ gcloud not found. Install: https://cloud.google.com/sdk/docs/install"; \
	  fail=1; \
	fi; \
	if command -v terraform >/dev/null 2>&1; then \
	  echo "  ✓ terraform: $$(terraform version | head -n1)"; \
	else \
	  echo "  ✗ terraform not found. Install: https://developer.hashicorp.com/terraform/downloads"; \
	  fail=1; \
	fi; \
	if [ -z "$(PROJECT_ID)" ]; then \
	  echo "  ✗ gcloud project not set. Run: gcloud config set project <PROJECT_ID>"; \
	  fail=1; \
	else \
	  echo "  ✓ gcloud project set"; \
	fi; \
	if [ -z "$(REGION)" ]; then \
	  echo "  ⚠ gcloud run/region not set. Recommended: gcloud config set run/region us-central1"; \
	else \
	  echo "  ✓ gcloud run/region: $(REGION)"; \
	fi; \
	if command -v gcloud >/dev/null 2>&1; then \
	  acct=$$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | head -n1); \
	  if [ -n "$$acct" ]; then \
	    echo "  ✓ gcloud user auth: $$acct"; \
	  else \
	    echo "  ⚠ gcloud user not authenticated. Run: gcloud auth login"; \
	  fi; \
	  if gcloud auth application-default print-access-token >/dev/null 2>&1; then \
	    echo "  ✓ ADC credentials: OK"; \
	  else \
	    echo "  ⚠ ADC not configured. Run: gcloud auth application-default login"; \
	  fi; \
	fi; \
	echo ""; \
	echo "Local dev prerequisites (optional; only needed for local UI/API dev):"; \
	if command -v uv >/dev/null 2>&1; then \
	  echo "  ✓ uv: $$(uv --version)"; \
	else \
	  echo "  ⚠ uv not found. Install: https://docs.astral.sh/uv/"; \
	fi; \
	if command -v node >/dev/null 2>&1; then \
	  echo "  ✓ node: $$(node -v)"; \
	else \
	  echo "  ⚠ node not found. Install: https://nodejs.org/"; \
	fi; \
	if command -v corepack >/dev/null 2>&1; then \
	  echo "  ✓ corepack: $$(corepack --version)"; \
	  echo "  ✓ pnpm (via corepack): $$(corepack pnpm --version)"; \
	else \
	  echo "  ✗ corepack not found. Install Node.js 20+ (includes corepack)."; \
	fi; \
	if command -v docker >/dev/null 2>&1; then \
	  if docker info >/dev/null 2>&1; then \
	    echo "  ✓ docker: $$(docker --version)"; \
	  else \
	    echo "  ⚠ docker installed but daemon not running. Start Docker Desktop."; \
	  fi; \
	else \
	  echo "  ⚠ docker not found (optional; only needed for local container runs)"; \
	fi; \
	if command -v jq >/dev/null 2>&1; then \
	  echo "  ✓ jq: $$(jq --version)"; \
	else \
	  echo "  ⚠ jq not found (optional; install: brew install jq)"; \
	fi; \
	echo ""; \
	if [ "$$fail" -ne 0 ]; then \
	  echo "Doctor found missing required items for Cloud deploy targets."; \
	  exit $$fail; \
	fi; \
	echo "Doctor OK."
config:
	@test -n "$(GCLOUD_CONFIG)" || (echo "Set GCLOUD_CONFIG=... (e.g., personal-portfolio)"; exit 1)
	@$(MAKE) init GCLOUD_CONFIG="$(GCLOUD_CONFIG)" PROJECT_ID="$(PROJECT_ID)" REGION="$(REGION)"


# Create the GCS bucket used for Terraform remote state.
# Safe to re-run; will not overwrite an existing bucket.
bootstrap-state: doctor
	@echo "Ensuring tfstate bucket exists: gs://$(TF_STATE_BUCKET)"
	@if gcloud storage buckets describe "gs://$(TF_STATE_BUCKET)" >/dev/null 2>&1; then \
		echo "Bucket already exists."; \
	else \
			echo "Creating bucket..."; \
			gcloud storage buckets create "gs://$(TF_STATE_BUCKET)" --location="$(REGION)" --uniform-bucket-level-access --public-access-prevention; \
			echo "Enabling versioning..."; \
			gcloud storage buckets update "gs://$(TF_STATE_BUCKET)" --versioning; \
		fi

# Terraform init with explicit backend config.
# Backend config is kept out of repo files to minimize environment-specific config.
tf-init: doctor bootstrap-state
	@echo "Terraform init (remote state)"
	terraform -chdir=$(TF_DIR) init -reconfigure \
		-backend-config="bucket=$(TF_STATE_BUCKET)" \
		-backend-config="prefix=$(TF_STATE_PREFIX)"

# Apply prerequisite infra only (APIs, Artifact Registry, service accounts).
# This creates the Artifact Registry repo BEFORE we build/push the container.
infra: tf-init
	terraform -chdir=$(TF_DIR) apply -auto-approve \
		-var "project_id=$(PROJECT_ID)" \
		-var "region=$(REGION)" \
		-var "env=$(ENV)" \
		-var "workspace_domain=$(WORKSPACE_DOMAIN)" \
		-var "group_prefix=$(GROUP_PREFIX)" \
		-var "clients_observers_group_email=$(CLIENTS_OBSERVERS_GROUP_EMAIL)" \
		-var "enable_clients_observers_monitoring_viewer=$(ENABLE_CLIENTS_OBSERVERS_MONITORING_VIEWER)" \
		-var "enable_observability=$(ENABLE_OBSERVABILITY)" \
		-var "deletion_protection=$(DELETION_PROTECTION)" \
		-var "service_name=$(SERVICE_NAME)" \
		-var "artifact_repo_name=$(AR_REPO)" \
		-var "image=$(IMAGE)" \
		-target=module.core_services \
		-target=module.artifact_registry \
		-target=module.service_accounts

# Cloud Build needs permission to push to Artifact Registry.
# This IAM binding is safe to re-run.
grant-cloudbuild: doctor
	@PROJECT_NUMBER=$$(gcloud projects describe "$(PROJECT_ID)" --format='value(projectNumber)'); \
	echo "Granting Cloud Build writer on Artifact Registry (project $$PROJECT_NUMBER)"; \
	gcloud projects add-iam-policy-binding "$(PROJECT_ID)" \
	  --member="serviceAccount:$${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
	  --role="roles/artifactregistry.writer" >/dev/null

# Standard plan/apply separation for team workflows.
plan: tf-init
	terraform -chdir=$(TF_DIR) plan \
		-var "project_id=$(PROJECT_ID)" \
		-var "region=$(REGION)" \
		-var "env=$(ENV)" \
		-var "workspace_domain=$(WORKSPACE_DOMAIN)" \
		-var "group_prefix=$(GROUP_PREFIX)" \
		-var "clients_observers_group_email=$(CLIENTS_OBSERVERS_GROUP_EMAIL)" \
		-var "enable_clients_observers_monitoring_viewer=$(ENABLE_CLIENTS_OBSERVERS_MONITORING_VIEWER)" \
		-var "enable_observability=$(ENABLE_OBSERVABILITY)" \
		-var "deletion_protection=$(DELETION_PROTECTION)" \
		-var "service_name=$(SERVICE_NAME)" \
		-var "artifact_repo_name=$(AR_REPO)" \
		-var "image=$(IMAGE)"

apply: tf-init
	terraform -chdir=$(TF_DIR) apply -auto-approve \
		-var "project_id=$(PROJECT_ID)" \
		-var "region=$(REGION)" \
		-var "env=$(ENV)" \
		-var "workspace_domain=$(WORKSPACE_DOMAIN)" \
		-var "group_prefix=$(GROUP_PREFIX)" \
		-var "clients_observers_group_email=$(CLIENTS_OBSERVERS_GROUP_EMAIL)" \
		-var "enable_clients_observers_monitoring_viewer=$(ENABLE_CLIENTS_OBSERVERS_MONITORING_VIEWER)" \
		-var "enable_observability=$(ENABLE_OBSERVABILITY)" \
		-var "deletion_protection=$(DELETION_PROTECTION)" \
		-var "service_name=$(SERVICE_NAME)" \
		-var "artifact_repo_name=$(AR_REPO)" \
		-var "image=$(IMAGE)"

# Build + push image using Cloud Build (recommended on macOS and in CI).
# This avoids cross-architecture issues and keeps the workflow consistent.
build: doctor infra grant-cloudbuild
	@echo "Building + pushing via Cloud Build: $(IMAGE)"
	# Use the repo's cloudbuild.yaml so we don't rely on a root Dockerfile.
	gcloud builds submit --config cloudbuild.yaml --substitutions "_IMAGE=$(IMAGE)" .

# One-command demo deployment.
# Safe to run repeatedly; converges infrastructure.
deploy: build apply smoke

url: tf-init
	@terraform -chdir=$(TF_DIR) output -raw service_url

verify: tf-init
	@URL=$$(terraform -chdir=$(TF_DIR) output -raw service_url); \
	echo "Service URL: $$URL"; \
	curl -fsS "$$URL/health" >/dev/null && echo "OK: /health"; \
	curl -fsS "$$URL/api/meta" >/dev/null && echo "OK: /api/meta"

smoke: ## Post-deploy smoke checks (use SMOKE_URL=... to override Terraform output URL)
	@set -euo pipefail; \
	URL="$(SMOKE_URL)"; \
	if [ -z "$$URL" ]; then \
	  $(MAKE) tf-init >/dev/null; \
	  URL="$$(terraform -chdir=$(TF_DIR) output -raw service_url)"; \
	fi; \
	echo "Smoke URL: $$URL"; \
	CMD=(uv run python scripts/deploy_smoke.py \
	  --base-url "$$URL" \
	  --question "$(SMOKE_QUERY)" \
	  --timeout-s "$(SMOKE_TIMEOUT_S)" \
	  --retries "$(SMOKE_RETRIES)" \
	  --retry-delay-s "$(SMOKE_RETRY_DELAY_S)"); \
	if [ -n "$(SMOKE_API_KEY)" ]; then CMD+=(--api-key "$(SMOKE_API_KEY)"); fi; \
	"$${CMD[@]}"

smoke-local: ## Smoke checks against local API (default: GKP_API_URL)
	@set -euo pipefail; \
	echo "Smoke URL: $(GKP_API_URL)"; \
	CMD=(uv run python scripts/deploy_smoke.py \
	  --base-url "$(GKP_API_URL)" \
	  --question "$(SMOKE_QUERY)" \
	  --timeout-s "$(SMOKE_TIMEOUT_S)" \
	  --retries "$(SMOKE_RETRIES)" \
	  --retry-delay-s "$(SMOKE_RETRY_DELAY_S)"); \
	if [ -n "$(SMOKE_API_KEY)" ]; then CMD+=(--api-key "$(SMOKE_API_KEY)"); fi; \
	"$${CMD[@]}"

logs: doctor
	gcloud run services logs read "$(SERVICE_NAME)" --region "$(REGION)" --limit 100

# Destroy only the Terraform-managed resources (NOT the state bucket).
destroy: tf-init
	terraform -chdir=$(TF_DIR) destroy -auto-approve \
		-var "project_id=$(PROJECT_ID)" \
		-var "region=$(REGION)" \
		-var "env=$(ENV)" \
		-var "workspace_domain=$(WORKSPACE_DOMAIN)" \
		-var "group_prefix=$(GROUP_PREFIX)" \
		-var "clients_observers_group_email=$(CLIENTS_OBSERVERS_GROUP_EMAIL)" \
		-var "enable_clients_observers_monitoring_viewer=$(ENABLE_CLIENTS_OBSERVERS_MONITORING_VIEWER)" \
		-var "enable_observability=$(ENABLE_OBSERVABILITY)" \
		-var "deletion_protection=$(DELETION_PROTECTION)" \
		-var "service_name=$(SERVICE_NAME)" \
		-var "artifact_repo_name=$(AR_REPO)" \
		-var "image=$(IMAGE)"

# Generate lockfiles locally for team reproducibility.
# We don't auto-run this in CI because it depends on registry access.
lock:
	@echo "Generating uv.lock (Python)"
	uv lock
	@echo "Generating pnpm-lock.yaml (web)"
	cd web && corepack pnpm install --frozen-lockfile
	@echo "Done. Commit uv.lock and pnpm-lock.yaml for team reproducibility."


# Release helpers.
# VERSION is required (semantic version X.Y.Z).
# RELEASE_DATE is optional (YYYY-MM-DD; defaults to today's date in the script).
# RELEASE_NOTES_OUT is optional; defaults to dist/release_notes_<VERSION>.md.

release-bump: ## Bump version and roll CHANGELOG "Unreleased" into a dated release section
	@test -n "$(VERSION)" || (echo "Set VERSION=x.y.z"; exit 1)
	@if [ -n "$(RELEASE_DATE)" ]; then \
	  uv run python scripts/release_tools.py bump --version "$(VERSION)" --date "$(RELEASE_DATE)"; \
	else \
	  uv run python scripts/release_tools.py bump --version "$(VERSION)"; \
	fi

release-notes: ## Extract release notes for VERSION from CHANGELOG.md
	@test -n "$(VERSION)" || (echo "Set VERSION=x.y.z"; exit 1)
	@OUT="$(RELEASE_NOTES_OUT)"; \
	if [ -z "$$OUT" ]; then OUT="dist/release_notes_$(VERSION).md"; fi; \
	uv run python scripts/release_tools.py notes --version "$(VERSION)" --output "$$OUT"; \
	echo "Release notes written to $$OUT"


# -----------------------------------------------------------------------------
# Staff-level IaC hygiene (lint / security / policy)
#
# These targets are optional locally (CI always runs them). They are convenient
# for "pre-flight" checks before a PR.
#
# We try to use locally-installed tools if present; otherwise we fall back to
# running the tool in a container (requires Docker).
# -----------------------------------------------------------------------------

POLICY_DIR := infra/gcp/policy

.PHONY: tf-fmt tf-validate tf-lint tf-sec tf-checkov tf-policy tf-check

tf-fmt: ## Terraform fmt check (no changes)
	@terraform -chdir=$(TF_DIR) fmt -check -recursive

tf-validate: ## Terraform validate (no remote backend required)
	@terraform -chdir=$(TF_DIR) init -backend=false -upgrade >/dev/null
	@terraform -chdir=$(TF_DIR) validate

tf-lint: ## tflint (falls back to docker)
	@if command -v tflint >/dev/null 2>&1; then \
	  echo "Running tflint (local)"; \
	  (cd $(TF_DIR) && tflint --init && tflint); \
	else \
	  echo "tflint not found; running via Docker"; \
	  docker run --rm -v "$$(pwd)/$(TF_DIR):/workspace" -w /workspace ghcr.io/terraform-linters/tflint:latest --init && \
	  docker run --rm -v "$$(pwd)/$(TF_DIR):/workspace" -w /workspace ghcr.io/terraform-linters/tflint:latest; \
	fi

tf-sec: ## tfsec (falls back to docker)
	@if command -v tfsec >/dev/null 2>&1; then \
	  echo "Running tfsec (local)"; \
	  tfsec $(TF_DIR); \
	else \
	  echo "tfsec not found; running via Docker"; \
	  docker run --rm -v "$$(pwd):/src" aquasec/tfsec:latest /src/$(TF_DIR); \
	fi


tf-checkov: ## checkov (falls back to docker)
	@# Keep skip list aligned with .github/workflows/terraform-hygiene.yml.
	@# These checks are intentionally out-of-scope for this baseline demo stack.
	@if command -v checkov >/dev/null 2>&1; then \
	  echo "Running checkov (local)"; \
	  checkov -d $(TF_DIR) --skip-check "CKV_GCP_84,CKV_GCP_26,CKV2_GCP_18,CKV_GCP_79,CKV_GCP_6,CKV_GCP_83,CKV_SECRET_4"; \
	else \
	  echo "checkov not found; running via Docker"; \
	  docker run --rm -v "$$(pwd):/src" bridgecrew/checkov:latest \
	    -d "/src/$(TF_DIR)" \
	    --skip-check "CKV_GCP_84,CKV_GCP_26,CKV2_GCP_18,CKV_GCP_79,CKV_GCP_6,CKV_GCP_83,CKV_SECRET_4"; \
	fi

tf-policy: ## OPA/Conftest policy gate for Terraform (falls back to docker)
	@if command -v conftest >/dev/null 2>&1; then \
	  echo "Running conftest (local)"; \
	  conftest test --parser hcl2 --policy $(POLICY_DIR) $$(find "$(TF_DIR)" -path "$(TF_DIR)/.terraform" -prune -o -type f -name "*.tf" -print); \
	else \
	  echo "conftest not found; running via Docker"; \
	  docker run --rm -v "$$(pwd):/project" -w /project openpolicyagent/conftest:latest test --parser hcl2 --policy $(POLICY_DIR) $$(find "$(TF_DIR)" -path "$(TF_DIR)/.terraform" -prune -o -type f -name "*.tf" -print); \
	fi

tf-check: tf-fmt tf-validate tf-lint tf-sec tf-checkov tf-policy ## Run all Terraform hygiene checks

# -----------------------------
# Packaging / housekeeping
# -----------------------------

.PHONY: release-bump release-notes clean dist task-index queue codex-prompt backlog-export backlog-refresh backlog-audit

clean: ## Remove local caches/build artifacts (safe)
	bash scripts/clean.sh

dist: ## Create a clean source ZIP in dist/
	python scripts/package_repo.py

task-index: ## Regenerate docs/BACKLOG/TASK_INDEX.md
	python scripts/generate_task_index.py

queue: ## Regenerate docs/BACKLOG/QUEUE.md
	python scripts/generate_execution_queue.py

codex-prompt: ## Generate a codex prompt pack for a task (TASK=agents/tasks/TASK_*.md)
	@test -n "$(TASK)" || (echo "Set TASK=agents/tasks/TASK_*.md"; exit 1)
	python scripts/prepare_codex_prompt.py $(TASK)

backlog-export: ## Export TASK_*.md as GitHub-issue artifacts in dist/github_issues/
	python scripts/export_github_issues.py

backlog-refresh: task-index queue ## Regenerate backlog indices (task-index + queue)
	@echo "Backlog refreshed: docs/BACKLOG/TASK_INDEX.md + docs/BACKLOG/QUEUE.md"

backlog-audit: ## Audit planning artifacts + task metadata (codex-ready check)
	python scripts/backlog_audit.py
