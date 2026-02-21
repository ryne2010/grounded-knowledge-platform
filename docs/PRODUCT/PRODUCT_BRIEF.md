# Product Brief — Grounded Knowledge Platform

A production-minded, citations-first knowledge system that turns a small set of documents into a **grounded reference experience**:

- Ingest documents (file upload, paste text, and connector-driven ingestion for private deployments)
- Retrieve evidence (hybrid lexical + vector) from Postgres/Cloud SQL
- Produce **evidence-backed answers with citations** (or refuse when evidence is insufficient)
- Maintain measurable quality via an evaluation harness (retrieval + safety regressions)
- Operate safely as a **public Cloud Run demo** (read-only, extractive-only, demo corpus only)

Decision record: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

---

## Problem statement

Teams often have “policy/procedure knowledge” trapped in documents:
- the answer exists, but the search/lookup time is high
- answers drift or become inconsistent between individuals
- there is no measurable way to detect regressions in retrieval/answer quality
- operational posture (security, cost, logging, deployments) is ad-hoc

This repo aims to demonstrate a **staff-level** approach:
- grounded answers (citations required)
- safe public demo posture
- production-style infrastructure and operational hygiene
- measurable quality controls (eval harness)

---

## Target users

### Public demo (anonymous)
- Wants to evaluate the experience quickly (quality of citations, refusal behavior, UX polish).
- Must not be able to upload content or trigger privileged operations.

### Private deployments (one client per GCP project)
- **Client Operator (admin):** deploys and operates the system; runs connector sync; responds to incidents.
- **Knowledge Curator (editor):** ingests/curates docs, adds metadata, validates contracts for tabular ingests.
- **Knowledge Consumer (reader):** asks questions, reads citations, downloads/opens source documents.

---

## Product goals

1) **Grounding and trust**
   - Every answer is supported by citations (or the system refuses).
   - Citations are navigable and easy to verify.

2) **Safe public demo**
   - Public URL is safe-by-default:
     - demo corpus only
     - extractive-only answering
     - rate limiting + Cloud Run instance caps
     - no uploads, no connectors, no eval endpoints

3) **Production-minded operation**
   - Cloud SQL Postgres is the persistence baseline for real deployments.
   - Terraform-based deployment patterns exist (Cloud Run + Cloud SQL + IAM + policies).
   - Logs/metrics support incident response and regression detection.

4) **Measurable quality**
   - Evaluation harness exists to detect regressions in retrieval and safety behavior.
   - Private deployments can persist eval runs and trend results (planned).

---

## Deployment modes

### Public demo mode (default posture)
- `PUBLIC_DEMO_MODE=1`
- `LLM_PROVIDER=extractive`
- `BOOTSTRAP_DEMO_CORPUS=1` (from `data/demo_corpus/`)
- No connectors (`ALLOW_CONNECTORS=0`) and no uploads (`ALLOW_UPLOADS=0`)
- Citations required (`CITATIONS_REQUIRED=1`)
- Rate limiting on `/api/query`

### Private deployment mode
- Auth enabled (recommended): `AUTH_MODE=api_key` or future `oidc`
- Uploads/connectors/eval can be enabled explicitly:
  - `ALLOW_UPLOADS=1`
  - `ALLOW_CONNECTORS=1`
  - `ALLOW_EVAL=1`
- Still enforce citations-required by default.

**Boundary model:** one GCP project per client (no in-app multi-tenancy).

---

## Success metrics

**Public demo**
- “Time to wow” < 2 minutes (open → ask → citations → verify source)
- Refusals are consistent and understandable for unsupported questions
- No privileged operations reachable without auth
- Cost guardrails prevent surprise spend (max instances, rate limiting)

**Private deployments**
- Ingestion is idempotent (no duplicates from reruns)
- Retrieval quality stays stable (eval regressions detectable)
- p95 query latency remains within a reasonable threshold for small corpora
- Operator workflows are documented (deploy, sync, backup/restore)

---

## Scope boundaries

- **Public demo must remain safe and read-only.**
- Private deployments may be richer, but must still prefer safe defaults.
- Avoid “portfolio-only hacks” that do not generalize to real operations.
