# Release Runbook

This repo supports two primary workflows:

- **local dev** on an M2 Max MacBook Pro
- **production** on Cloud Run

---

## Before you release

1. Run the local harness:

```bash
make dev-doctor
```

2. Ensure the UI builds:

```bash
make web-build
```

3. Check schema compatibility

- This project uses lightweight forward migrations in `app/storage.py:init_db`.
- Any new schema change should be **additive** (new tables/columns) unless you also implement a data migration.

---

## Deploy to Cloud Run

The repo includes deployment automation:

- `make build`
- `make deploy`

Recommended safe public settings:

```bash
PUBLIC_DEMO_MODE=1
ALLOW_UPLOADS=0
ALLOW_EVAL=0
ALLOW_CHUNK_VIEW=0
ALLOW_DOC_DELETE=0
RATE_LIMIT_ENABLED=1
```

---

## Post-deploy smoke test

1. `GET /health`
2. `GET /api/meta` (verify flags)
3. `POST /api/query` against a known answerable question
4. Confirm citations are returned and refusal behavior is correct

---

## Rollback

- Cloud Run supports quick rollback by redeploying a previous revision.
- If a release introduced schema changes, additive migrations should remain compatible with rollback (avoid destructive migrations).
