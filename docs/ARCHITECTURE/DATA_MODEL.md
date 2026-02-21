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

### `meta`
Small key/value store for app metadata.

### `schema_migrations`
Tracks applied SQL migration filenames.

---

## Planned tables (roadmap)

These are defined in the backlog but not all are implemented yet.

### `ingestion_runs`
A higher-level grouping for connector-triggered ingestion operations:

- run status (running/succeeded/failed)
- trigger source (manual UI, CLI, connector)
- summary counts (docs changed, errors, bytes)
- linkage to a list of `ingest_events`

### `audit_events`
Append-only audit log for security-sensitive actions:

- who (principal)
- what (action type)
- when
- target (doc_id, connector, config)
- outcome (success/failure)

### `eval_runs`
Persisted evaluation history:

- dataset hash / version
- app version / git sha
- retrieval config snapshot
- metrics
- per-case outputs (optional, possibly stored separately)

---

## Design notes

- Postgres is the production baseline; SQLite is a local fallback only.
- Governance fields should be queryable (classification/retention/tags), even in a small demo.
- Keep ingestion idempotent by using content hashes and connector object fingerprints.

