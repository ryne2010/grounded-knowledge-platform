# Demo script

This is a repeatable “show me” script for interviews and demos.

Public demo posture constraints: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

Demo corpus lives at: `data/demo_corpus/`

---

## 5-minute public demo walkthrough

**Goal:** demonstrate grounded answers (citations) and refusal behavior.

1) Open the UI (Search / Home)

- Call out the **Demo Mode** banner and the read-only posture.

2) Ask an answerable question and verify citations

Suggested questions (match the demo corpus docs):

- “What are the reliability guardrails for Cloud Run?”
  - Expect citations from `cloud_run_basics.md`

- “Why does Cloud Run need Cloud SQL for persistence?”
  - Expect citations from `cloud_sql_persistence.md`

- “What are the bronze/silver/gold layers in a BigQuery lakehouse?”
  - Expect citations from `bigquery_lakehouse.md`

3) Ask an unanswerable question

Example:

- “What is our internal PTO policy?”
- “Who is the CEO of Company X?”

Expected behavior:

- refusal (“I don’t have evidence in the provided documents”)
- no hallucinated citations

4) Open a cited source (Doc Detail)

- Click a citation and show the source snippet in context.
- Emphasize: **trust comes from verifiability**.

---

## 10–15 minute private deployment walkthrough (optional)

**Goal:** show operational maturity: ingestion + governance + eval + runbooks.

Preconditions:
- Private deployment (auth enabled).
- `ALLOW_CONNECTORS=1` and `ALLOW_UPLOADS=1` as needed.

1) Trigger a GCS sync (admin)

- Show add/update-only behavior (no deletions).
- Re-run sync to demonstrate idempotency (no duplicates).

2) Review ingest lineage

- Open the dashboard or doc detail.
- Show ingest events with:
  - content hash
  - chunking settings
  - embedding config
  - contract validation fields for tabular ingests

3) Run eval (admin)

- Trigger an eval run.
- Show pass/fail and any regressions.

4) Operations posture

- Open runbook docs:
  - `docs/RUNBOOKS/`
- Show deployment docs:
  - `docs/DEPLOY_GCP.md`

5) Close with the safety model

- Explain why the public demo is extractive-only.
- Explain how private deployments can enable richer features behind auth.
