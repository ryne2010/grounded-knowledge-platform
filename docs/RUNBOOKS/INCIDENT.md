# Incident Runbook

This runbook is tuned for **Grounded Knowledge Platform** on **Cloud Run**.

---

## Fast triage checklist

1. **Scope**
   - Is it all requests or only certain endpoints (e.g., `/api/query`, `/api/ingest/*`)?
   - Is it only one region/service revision?

2. **Logs**
   - Use Cloud Run logs.
   - Correlate errors with `X-Request-Id` (also logged as `request_id`).

3. **Recent changes**
   - Did a new revision deploy recently?
   - Was an env var changed (e.g., feature gates)?

4. **User impact**
   - Are responses failing (5xx) or refusing unexpectedly (refusal spikes)?
   - Is latency elevated?

---

## Common failure modes + mitigations

### 429 spikes (rate limiting)

- Cause: traffic increase or abuse of `/api/query`.
- Mitigation:
  - If public: keep `PUBLIC_DEMO_MODE=1` and increase `RATE_LIMIT_MAX_REQUESTS` cautiously.
  - Consider enabling Cloud Armor / IAP for additional protection.

### Ingest failures

- Cause: file too large (`413`), invalid metadata (`400`), missing PDF deps, embedding model download issues.
- Mitigation:
  - Check `MAX_UPLOAD_BYTES`.
  - For private deployments only: verify `ALLOW_UPLOADS=1`.
  - If embeddings backend is optional and failing, switch `EMBEDDINGS_BACKEND=hash`.

### Retrieval quality regression

- Cause: doc re-ingested with different chunk/embedding settings.
- Mitigation:
  - Inspect doc **ingest lineage** in UI (`/docs/{doc_id}`) to confirm settings changes.
  - Re-ingest with known-good settings.

### Data loss / missing docs (Cloud Run)

- Cause: SQLite is stored on ephemeral filesystem.
- Mitigation:
  - For production durability, migrate to a persistent DB (Cloud SQL) or external storage.

---

## Post-incident

- Identify:
  - triggering change
  - blast radius
  - mitigation taken
- Create follow-ups:
  - regression test
  - monitoring / alerts
  - docs updates
