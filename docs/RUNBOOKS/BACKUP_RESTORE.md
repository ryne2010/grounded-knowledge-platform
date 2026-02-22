# Runbook: Cloud SQL Backup/Restore + Restore Drills

## Scope

This runbook covers backup/restore operations for Cloud SQL Postgres in private deployments.

This repo's baseline is:
- one GCP project per client
- Cloud SQL Postgres for durable production storage
- public demo remains safe/read-only and is not used for mutable restore drills

## Backup posture in Terraform

`infra/gcp/cloud_run_demo` configures Cloud SQL backups with:
- automated daily backups enabled
- backup retention count (`cloudsql_retained_backups`, default `14`)
- PITR toggle (`cloudsql_enable_point_in_time_recovery`, default `true`)
- transaction-log retention (`cloudsql_transaction_log_retention_days`, default `7`)
- backup start time (`cloudsql_backup_start_time`, default `03:00` UTC)

## RTO/RPO planning assumptions

Use these as planning targets, not hard guarantees:

- Backup restore path (daily backups):
  - target RPO: up to 24 hours (depends on backup schedule)
  - target RTO: 30-120 minutes (depends on data size/instance tier)
- PITR restore path (transaction logs retained):
  - target RPO: minutes to tens of minutes (depends on chosen restore point)
  - target RTO: 30-120 minutes

## Preconditions

- `gcloud` authenticated to the client project
- Cloud SQL Admin + Cloud Run Admin permissions
- known `SOURCE_INSTANCE` and `RESTORE_INSTANCE` names
- a known-good smoke query for your corpus (for post-restore verification)

Set variables:

```bash
PROJECT_ID="your-project"
REGION="us-central1"
SOURCE_INSTANCE="gkp-prod-pg"
RESTORE_INSTANCE="gkp-restore-drill-$(date +%Y%m%d)"
DB_NAME="gkp"
DB_USER="gkp_app"
```

## Step 1: Confirm source backup settings

```bash
gcloud sql instances describe "$SOURCE_INSTANCE" \
  --project "$PROJECT_ID" \
  --format="yaml(settings.backupConfiguration)"
```

Confirm:
- `enabled: true`
- `pointInTimeRecoveryEnabled: true` (if using PITR path)
- retention values match policy

## Step 2: Choose restore strategy

### Option A (recommended): PITR clone to staging instance

Pick a restore timestamp in UTC RFC3339 format (before incident/corruption):

```bash
RESTORE_POINT_UTC="2026-02-22T14:30:00Z"
```

Restore:

```bash
gcloud sql instances clone "$SOURCE_INSTANCE" "$RESTORE_INSTANCE" \
  --project "$PROJECT_ID" \
  --point-in-time "$RESTORE_POINT_UTC"
```

### Option B: Backup ID restore

List successful backups:

```bash
gcloud sql backups list \
  --project "$PROJECT_ID" \
  --instance "$SOURCE_INSTANCE" \
  --filter="status=SUCCESSFUL" \
  --sort-by="~endTime"
```

Then restore backup `BACKUP_ID` into an existing staging instance:

```bash
gcloud sql backups restore "$BACKUP_ID" \
  --project "$PROJECT_ID" \
  --backup-instance "$SOURCE_INSTANCE" \
  --restore-instance "$RESTORE_INSTANCE"
```

## Step 3: Wait for restored instance readiness

```bash
gcloud sql instances describe "$RESTORE_INSTANCE" \
  --project "$PROJECT_ID" \
  --format="value(state)"
```

Proceed only when state is `RUNNABLE`.

## Step 4: Service-level post-restore smoke verification

Recommended: verify through a staging API deployment that points at the restored instance.

If your staging Cloud Run service is already wired to the restored DB:

```bash
make smoke \
  SMOKE_URL="https://<staging-service-url>" \
  SMOKE_QUERY="question with known answer in staging corpus" \
  SMOKE_API_KEY="<admin-or-reader-api-key-if-required>"
```

Alternative local verification via Cloud SQL Auth Proxy:

1. Set/reset a temporary password on the restored instance user.
2. Run `cloud-sql-proxy` for `"$RESTORE_INSTANCE"` on local port `5433`.
3. Start the API locally with `DATABASE_URL=postgresql://...@127.0.0.1:5433/$DB_NAME`.
4. Run:

```bash
make smoke-local \
  GKP_API_URL="http://127.0.0.1:8081" \
  SMOKE_QUERY="question with known answer in restored corpus"
```

Restore verification is successful when:
- `/health`, `/ready`, and `/api/meta` pass
- `/api/query` returns an answer with citations for the known-good query

## Step 5: Record drill results

Capture and store:
- drill date/time
- restore method (PITR or backup ID)
- source + restored instance IDs
- measured RTO and achieved RPO
- smoke test output and any gaps

Recommended cadence:
- quarterly
- after major schema/storage changes
- before high-risk releases

## Step 6: Cleanup drill resources

Delete temporary restored instance after drill sign-off:

```bash
gcloud sql instances delete "$RESTORE_INSTANCE" \
  --project "$PROJECT_ID" \
  --quiet
```

## Limitations

- Restore drills are still operator-driven (not fully automated in Terraform).
- Cloud SQL restore is instance-scoped; cutover/traffic-switch remains manual.
- Large datasets can exceed planning RTO targets.
- PITR window is bounded by `cloudsql_transaction_log_retention_days`.
