# Reference Architecture — Grounded Knowledge Platform

This document describes a practical architecture for building a **grounded knowledge system** that can run:

- as a safe, read-only public demo
- as a private / on-prem deployment for confidential content

The key design principle is: **answers must be supported by evidence from retrieved documents**.

## Components

### 1) Ingestion

Ingestion converts raw documents into indexed, queryable chunks.

Typical steps:

1. **Parse**: load `.txt`, `.md`, and `.pdf` content.
2. **OCR (optional)**: for scanned PDFs, run local OCR to extract text.
3. **Chunking**: split text into overlapping chunks (e.g., ~1,200 chars, 200 char overlap).
4. **Metadata**: store `doc_id`, title, and source label.
5. **Embeddings (optional)**: compute an embedding vector per chunk for semantic search.

This repo stores chunks + embeddings in **SQLite** for simplicity.

### 2) Retrieval

Retrieval selects the best document chunks for a question.

This implementation supports **hybrid retrieval**:

- **Lexical search** using SQLite FTS5 BM25 (or a BM25 fallback)
- **Vector similarity** using cosine similarity over embeddings

The final score is a combination of lexical and vector scores.

### 3) Answering (grounded)

The safest default is an **extractive** answerer:

- it selects sentences directly from the retrieved chunks
- it includes citations
- if evidence is insufficient, it refuses

For private deployments, you can optionally enable an LLM (e.g., `LLM_PROVIDER=ollama`) *while keeping retrieval and evidence local*.

### 4) Safety controls

For public demos, the recommended controls are:

- `PUBLIC_DEMO_MODE=1` (forces extractive answers, disables uploads)
- clamp retrieval knobs (e.g., max `top_k`)
- rate limiting per client IP
- no external API calls by default

## Tradeoffs (why this is a good "resume project")

This kind of system demonstrates:

- cloud-native deployment (Cloud Run)
- event-driven patterns and operational maturity
- security posture (RBAC / encryption / auditability)
- applied AI without hallucination risk (grounding + refusal)