# Sub-agent prompts

This folder contains **optional role prompts** to help @codex (or other agent runners) focus on a specific slice of work.

They are intentionally small and pragmatic:

- what to optimize for
- what constraints must be respected
- which files/modules are likely hotspots

If you don’t use sub-agents, you can ignore this folder.

## Available prompts

- `frontend_ux.md` – UI/UX implementation and polish
- `postgres_hardening.md` – Postgres/Cloud SQL performance and schema
- `connector_gcs.md` – GCS sync connector behavior
- `backend_fastapi_platform.md` – API/platform changes (auth, ingestion, storage)
- `eval_harness.md` – eval datasets, metrics, CI gates
- `infra_terraform_gcp.md` – Terraform on GCP (Cloud Run/Cloud SQL)
- `security_governance.md` – safety posture, least privilege, auditability
- `product_planner.md` – specs, backlog, sequencing

