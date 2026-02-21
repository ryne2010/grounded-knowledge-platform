# Data model

This document describes the **Postgres baseline schema** (Cloud SQL / local Postgres).

Schema is defined via SQL migrations:
- `app/migrations/postgres/*.sql`
- applied by `app/migrations_runner.py` (tracks in `schema_migrations`)

---

## Current tables (Postgres baseline)

### `docs`
Top-level document metadata.

Key fields:
- `doc_id` (PK)
- `title`, `source`
- governance metadata:
  - `classification` (`public|internal|confidential|restricted`)
  - `retention` (`none|30d|90d|1y|indefinite`)
  - `tags_json` (JSON array stored as text)
- content fingerprint fields:
  - `content_sha256`
  - `content_bytes`
  - `doc_version`
- counters:
  - `num_chunks`

### `chunks`
Chunked text per document.

Key fields:
- `chunk_id` (PK)
- `doc_id` (FK → docs)
- `idx` (chunk order)
- `text`

### `embeddings`
Vector embedding per chunk (pgvector required).

Key fields:
- `chunk_id` (PK, FK → chunks)
- `dim`
- `vec` (`vector`)

Indexes:
- HNSW on `vec` for cosine distance (`vector_cosine_ops`)

### `ingest_events`
Lineage record per ingestion.

Captures:
- content hash changes (`content_sha256`, `prev_content_sha256`, `changed`)
- chunking settings (`chunk_size_chars`, `chunk_overlap_chars`)
- embedding config (`embedding_backend`, `embeddings_model`, `embedding_dim`)
- optional contract validation fields for tabular ingests:
  - `schema_fingerprint`, `contract_sha256`, `validation_status`, `validation_errors_json`, `schema_drifted`
- optional ingestion run linkage:
  - `run_id`

### `ingestion_runs`
Higher-level grouping for connector-triggered or batch ingestion operations.

Captures:
- run lifecycle (`started_at`, `finished_at`, `status`)
- trigger metadata (`trigger_type`, `trigger_payload_json`, `principal`)
- summary counters (`objects_scanned`, `docs_changed`, `docs_unchanged`, `bytes_processed`)
- retained actionable errors (`errors_json`)

### `meta`
Small key/value store for app metadata.

### `audit_events`
Append-only audit log for security-sensitive actions.

Captures:
- who (`principal`, `role`)
- what (`action`)
- target (`target_type`, `target_id`)
- when (`occurred_at`)
- safe metadata (`metadata_json`)
- request correlation (`request_id`)

### `schema_migrations`
Tracks applied SQL migration filenames.

---

### `eval_runs`
Persisted evaluation history (private deployments only):

- run identity and timing (`run_id`, `started_at`, `finished_at`, `status`)
- dataset provenance (`dataset_name`, `dataset_sha256`)
- config snapshot:
  - app version
  - embeddings backend/model
  - retrieval config (`k`, hybrid weights)
  - provider config (effective provider/model)
- aggregated metrics (`summary_json`: examples, pass/fail, pass rate, hit@k, mrr)
- run-to-run diff (`diff_from_prev_json`)
- per-case details (`details_json`)

---

## Design notes

- Postgres is the production baseline; SQLite is a local fallback only.
- Governance fields should be queryable (classification/retention/tags), even in a small demo.
- Keep ingestion idempotent by using content hashes and connector object fingerprints.
