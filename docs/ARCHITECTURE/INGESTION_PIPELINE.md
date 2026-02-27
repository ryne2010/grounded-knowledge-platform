# Ingestion pipeline

Ingestion converts source material into:

- `docs` (top-level metadata)
- `chunks` (retrieval units)
- `embeddings` (optional, but pgvector is the Postgres baseline)
- `ingest_events` (lineage + reproducibility record)

Public demo posture: ingestion endpoints are disabled.

---

## Inputs

**Private deployments** may ingest via:

- UI upload (single file: txt/md/pdf/csv/tsv/xlsx/xlsm)
- UI directory upload (best-effort batch over txt/md/pdf/csv/tsv/xlsx/xlsm)
- UI paste text
- CLI (`python -m app.cli ...`)
- Connector sync (GCS prefix batch)

---

## Steps (high level)

1. **Parse**
   - Detect file type and extract text.
   - For PDFs, optional OCR if enabled.

2. **Normalize metadata**
   - classification / retention / tags normalized to canonical values.
   - metadata stored in `docs`.

3. **Contract validation (tabular only)**
   - optional YAML contract validates schema and basic quality checks.
   - results recorded in `ingest_events`:
     - schema fingerprint
     - contract hash
     - validation status/errors
     - drift flag

4. **Chunk**
   - deterministic chunking using configured size/overlap.
   - chunk order stored via `idx`.

5. **Embed**
   - generate embeddings (if enabled)
   - store in pgvector `embeddings.vec`

6. **Record lineage**
   - write an `ingest_event` including content hash and settings snapshot.

7. **Invalidate retrieval cache**
   - ensures subsequent queries reflect the new corpus state.

---

## Connector: GCS sync (private only)

Endpoint:
- `POST /api/connectors/gcs/sync` (admin only)

Behavior:
- batch sync from a `bucket` + `prefix`
- **add/update only** (no deletions/tombstones)
- idempotency via object fingerprinting:
  - content hash, etag/generation where available

Design constraint:
- Demo mode hard-disables connectors even if the endpoint is called.

### Optional: event-driven ingestion (Pub/Sub)

Private deployments may also support a push path:

- Cloud Storage notifications → Pub/Sub push → `POST /api/connectors/gcs/notify`

Spec:

- `docs/SPECS/PUBSUB_EVENT_INGESTION.md`

---

## Operator outcomes (what “good” looks like)

- rerunning ingestion is safe (no duplicates)
- lineage is sufficient to explain how content changed
- validation/drift signals are visible and actionable
- errors are actionable, not mysterious stack traces
