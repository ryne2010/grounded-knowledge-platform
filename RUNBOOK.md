# Runbook

This runbook is written for **team operations** (local dev, Cloud Run demo, and troubleshooting).

## Quick links

- **Local dev:** `README.md`
- **GCP deploy:** `docs/DEPLOY_GCP.md`
- **Team workflow:** `docs/TEAM_WORKFLOW.md`
- **Security/threat notes:** `SECURITY.md`

---

## Local development

### Start the API

```bash
uv sync --dev
uv run uvicorn app.main:app --reload --port 8080
```

### Start the UI

```bash
cd web
pnpm install
pnpm dev
```

### Ingest the demo corpus

```bash
uv run python -m app.cli ingest-folder data/demo_corpus
```

---

## Cloud Run demo operations

### Deploy (recommended)

```bash
make deploy
```

### View URL

```bash
make url
```

### View logs

```bash
make logs
```

### Verify endpoints

```bash
make verify
```

---

## Troubleshooting

### 1) Cloud Run returns 500

1. Read logs:
   ```bash
   make logs
   ```
2. If the UI shows an error like `[req <id>] HTTP 500: ...`, use that request id to locate the log entry.
3. Look for `request_id` in structured JSON logs.
4. Confirm demo-safe settings are active (Terraform sets these by default):
   - `PUBLIC_DEMO_MODE=1`
   - `LLM_PROVIDER=extractive`
   - `SQLITE_PATH=/tmp/index.sqlite`

### 2) Cloud Build fails to push the image

Most common cause: Cloud Build lacks Artifact Registry permissions.

Fix:
```bash
make grant-cloudbuild
make build
```

### 3) Terraform init fails (backend)

If the backend bucket does not exist:
```bash
make bootstrap-state
make tf-init
```

If you changed `TF_STATE_BUCKET` or `TF_STATE_PREFIX`, re-run init:
```bash
make tf-init
```

### 4) Rate limiting triggers in demo

For public demos we default to conservative limits.
If needed, adjust the Terraform env vars in `infra/gcp/cloud_run_demo/main.tf`.

---

## Rollback

Cloud Run rollback is typically done by redeploying an earlier image tag.

Recommended workflow:
1. Tag images immutably (`TAG=v2026-01-29-1`, etc.)
2. Update `TAG` in your deploy command:

```bash
make deploy TAG=v2026-01-29-1
```

---

## Decommission

To destroy Terraform-managed resources:

```bash
make destroy
```

Note:
- This **does not** delete the Terraform state bucket.
- Teams typically keep the state bucket to preserve audit history and prevent orphaned state.
