# Architecture

This repo is a **production-minded reference implementation** of a grounded knowledge system (RAG) with:
- **citations-first answers** (every claim is tied to retrieved sources)
- **refusal behavior** when evidence is insufficient
- optional **OCR** for scanned PDFs
- optional **local/opensource LLMs** (Ollama) for sensitive deployments
- a lightweight **governance layer** (classification tags + retention) and optional **RBAC** (JWT claims → allowed tags)

The goal is to demonstrate **staff-level engineering habits**: clear contracts, safe defaults, observability, and deployable infra.

---

## High-level flow

```
                ┌─────────────────────────┐
                │  Document sources       │
                │  (md/txt/pdf, etc.)     │
                └──────────┬──────────────┘
                           │ ingest
                           v
┌──────────────────────────────────────────────────────┐
│ Ingestion pipeline                                   │
│  - file parsing (PDF/text/markdown)                  │
│  - optional OCR (tesseract)                          │
│  - metadata extraction (classification, retention)   │
│  - chunking + hashing                                │
└──────────┬───────────────────────────────────────────┘
           │ writes
           v
┌──────────────────────────────────────────────────────┐
│ Storage + Index                                      │
│  - SQLite metadata store                             │
│  - embeddings (hash | sentence-transformers)         │
│  - vector search (sqlite + cosine-ish)               │
└──────────┬───────────────────────────────────────────┘
           │ query
           v
┌──────────────────────────────────────────────────────┐
│ Retrieval + Governance enforcement                    │
│  - filter by retention/classification                │
│  - optional RBAC: JWT → allowed_tags filter          │
│  - top-k retrieval + snippets                         │
└──────────┬───────────────────────────────────────────┘
           │ context
           v
┌──────────────────────────────────────────────────────┐
│ Answering                                             │
│  - Extractive (demo-safe)                             │
│  - Optional LLMs (OpenAI/Gemini/Ollama)               │
│  - Citations required                                 │
│  - Refusal if weak evidence                           │
└──────────┬───────────────────────────────────────────┘
           │
           v
┌──────────────────────────────────────────────────────┐
│ API + UI                                               │
│  - FastAPI REST endpoints                              │
│  - React/TanStack UI                                   │
│  - structured logs (request_id, latency, status)       │
└──────────────────────────────────────────────────────┘
```

---

## Public demo mode

`PUBLIC_DEMO_MODE=1` forces **safe defaults**:
- disables uploads and admin/eval endpoints
- forces `LLM_PROVIDER=extractive`
- clamps query knobs (`top_k`, max chars)
- enables simple rate limiting

This allows a public Cloud Run demo without exposing sensitive behaviors.

---

## Security and governance posture

**Governance metadata** exists at the document level:
- `classification_tags` (e.g., `public`, `confidential`, `legal`)
- `retention_policy` + `retention_until`

**RBAC (optional)**:
- `RBAC_ENABLED=1` enables JWT verification
- JWT claim `allowed_tags` (configurable) maps to allowed document tags
- enforcement happens **before retrieval** so citations cannot leak restricted docs

See: `SECURITY.md` and `docs/TEAM_WORKFLOW.md`.

---

## Deployment mapping (GCP)

Recommended “staff-level” deployment:
- **Cloud Run** for API + UI
- **Artifact Registry** for images
- **Cloud Build** for consistent builds (macOS-friendly)
- **GCS remote state** for Terraform
- Optional: **Serverless VPC Access connector** (costs money; off by default)

The Terraform example lives in `infra/gcp/cloud_run_demo/` and is designed to be driven via `make`.
