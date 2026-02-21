# Personas and journeys

This doc is about **UI/UX intent**: who uses the system and what the “happy paths” look like.

Public demo posture constraints: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

---

## Personas

### 1) Public Viewer (anonymous)
**Goal:** Decide if the system feels trustworthy and usable in a few minutes.

- Reads answers and verifies citations.
- Expects refusal when evidence is missing.
- Must not be able to upload or mutate data.

**Primary screens:** Home / Search, Doc Detail (read-only), Meta/About.

---

### 2) Client Operator (admin)
**Goal:** Deploy and operate the system in a single client project.

- Runs connector syncs (GCS).
- Monitors ingest health, errors, and regression signals.
- Owns backups/restore drills and incident response.

**Primary screens:** Dashboard, Ingest (connector UI), Maintenance, Logs/Runbooks.

---

### 3) Knowledge Curator (editor)
**Goal:** Keep the corpus relevant, organized, and governed.

- Uploads documents or pastes text (private deployments only).
- Applies governance metadata (classification, retention, tags).
- Uses contracts for tabular ingests and responds to drift warnings.

**Primary screens:** Ingest, Docs, Doc Detail (metadata editor), Drift/Lineage views.

---

### 4) Knowledge Consumer (reader)
**Goal:** Get fast answers with confidence.

- Asks questions repeatedly.
- Opens citations and scans the source context.
- Expects consistent behavior and stable performance.

**Primary screens:** Search, Doc Viewer/Citations, “Explain this answer”.

---

## Journeys

### A) Public demo “wow path” (2–5 minutes)

1. Open the homepage (neutral SaaS admin shell, clear navigation).
2. Ask a question that should be answerable from the demo corpus:
   - “What are the reliability guardrails for Cloud Run?”
   - “Why does Cloud Run need Cloud SQL for persistence?”
   - “What is the BigQuery lakehouse bronze/silver/gold model?”
3. Read the answer and verify:
   - citations are present
   - citations are clickable
   - the cited source text matches the claim
4. Ask a question that is **not** supported by the corpus.
   - Expected behavior: **refusal**, with a helpful explanation like “I don’t have evidence in the provided documents.”
5. Optional: open the Meta/About page to see the current posture:
   - demo mode enabled
   - extractive-only
   - demo corpus only

UX emphasis:
- Fast page loads, crisp empty states, visible “demo mode” banner.
- Citations are treated as first-class UI (not a footnote).

---

### B) Private operator journey (10–20 minutes)

1. Deploy into a client GCP project (Cloud Run + Cloud SQL + Terraform).
2. Configure auth (`AUTH_MODE=api_key`) and restrict privileged endpoints.
3. Enable connectors (`ALLOW_CONNECTORS=1`) and trigger a GCS sync:
   - confirm add/update-only behavior
   - confirm idempotency: rerun yields no duplicates
4. Monitor ingest results:
   - ingestion events visible
   - errors have actionable messages
5. Run an eval suite (`ALLOW_EVAL=1`) and compare results to the previous run.
6. Confirm dashboards/log views are sufficient for incident response.
7. Practice “rollback”:
   - redeploy previous revision
   - verify query path still works

---

### C) Private curator journey (ongoing)

1. Upload or paste new content (editor role).
2. Apply metadata (classification, retention, tags).
3. For tabular content, attach a contract:
   - validation failures stop ingestion (fail fast)
   - additive drift is recorded and visible
4. Re-run syncs/replays when upstream files change.

---

### D) Private consumer journey (ongoing)

1. Ask questions and verify citations quickly.
2. Use “Explain this answer” to understand:
   - which documents were retrieved
   - why they were chosen (FTS + vector signals)
   - why a refusal happened (low evidence)

---

## UX non-negotiables

- Every answer must have citations (or a refusal).
- Public demo cannot mutate data.
- Privileged operations are clearly labeled and gated (admin/editor only).
- Errors are actionable and do not leak content or secrets.
