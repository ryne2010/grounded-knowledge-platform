# Maintenance runbook

This runbook covers periodic operational tasks for private deployments.

> Public demo deployments on Cloud Run are intentionally ephemeral and read-only.

---

## Retention sweep

### What it does

Deletes documents whose retention policy has expired:

- `30d`, `90d`, `1y`: eligible for auto-purge when `updated_at` is older than the policy.
- `none`, `indefinite`: never auto-purged.

### Dry-run

```bash
make retention-sweep
```

### Apply deletes

```bash
make retention-sweep-apply
```

### Cloud Scheduler / Cloud Run Jobs (recommended)

In production, schedule this as a Cloud Run Job that runs:

```bash
uv run python -m app.cli retention-sweep --apply
```

---

## Index compatibility / drift

### Symptoms

- Retrieval suddenly gets worse after changing chunking/embedding settings
- You switch `EMBEDDINGS_BACKEND`/`EMBEDDINGS_MODEL` and results are inconsistent

### How it works

- The index stores an `index_signature` in the `meta` table.
- On ingest, the app checks compatibility and will raise an error if the index is incompatible.
- If only the embedding backend/model changed, the app will attempt a full embeddings rebuild.

### What to do

1. Check current signature:

   - UI: **Meta** page
   - API: `GET /api/meta` → `index_signature`

2. If the signature is wrong or missing (rare), re-ingest docs or rebuild the DB.

---

## Safety regression

Run the built-in prompt-injection safety suite:

```bash
make run-api
make safety-eval
```

If failures occur, review:

- `app/safety.py`
- `data/eval/prompt_injection.jsonl`

---

## Retrieval regression

Run the built-in retrieval quality suite:

```bash
make run-api
make eval
```

This prints hit@k and MRR.
