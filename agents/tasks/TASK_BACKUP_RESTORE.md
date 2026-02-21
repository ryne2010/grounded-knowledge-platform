# Task: Backup/restore runbook + drills (Cloud SQL)

Spec: `docs/SPECS/OBSERVABILITY_OPS.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/infra_terraform_gcp.md`

## Goal

Private deployments should have a real operational story for Cloud SQL:

- automated backups enabled
- documented restore procedure
- periodic restore drill guidance

## Requirements

- Terraform:
  - ensure backups are configured (retention, PITR if desired)
  - document any limitations

- Docs:
  - `docs/RUNBOOKS/BACKUP_RESTORE.md` (new)
  - include:
    - RTO/RPO assumptions
    - step-by-step restore
    - validation checks after restore

- Optional:
  - `make restore-drill` script that documents the workflow (even if manual steps remain)

## Acceptance criteria

- A reader can follow the runbook to restore into a staging instance.
- Post-restore smoke tests verify the service.

## Validation

- `make tf-check`
