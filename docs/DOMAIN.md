# Domain

This repository is a **grounded knowledge platform**: you ingest documents, the system chunks + indexes them, and then answers questions **only when it can cite evidence from the indexed sources**.

Core values:

- **Grounding first**: return citations with answers, or refuse.
- **Safety first**: defend against prompt injection and accidental data exfiltration.
- **Operational clarity**: record ingest lineage so you can audit drift and reproduce results.

---

## Core entities

### Document

A `doc` is the unit of ingestion and lifecycle management.

Metadata (stored in the `docs` table):

- `doc_id`: stable identifier
- `title`: human-friendly title
- `source`: a source label (filename, URL, system name)
- `classification`: `public|internal|confidential|restricted`
- `retention`: `none|30d|90d|1y|indefinite`
- `tags`: list of normalized strings
- `content_sha256`: hash of ingested text (drift tracking)
- `content_bytes`: size of ingested text
- `num_chunks`: number of stored chunks
- `doc_version`: increments on each ingest
- `created_at`, `updated_at`: unix timestamps

Retention semantics in this repo:

- `30d`, `90d`, `1y`: eligible for auto-purge when `updated_at` is older than the policy.
- `none`, `indefinite`: never auto-purged by the built-in purge command.

This conservative behavior prevents accidental deletion when retention is missing/unknown.

### Chunk

A chunk is a contiguous piece of document text.

- `chunk_id`: deterministic ID (`{doc_id}__{idx}`)
- `doc_id`: owning document
- `idx`: chunk order
- `text`: chunk text

### Embedding

One embedding per chunk.

- `dim`: vector dimension
- `vec`: float32 bytes

Backends:

- `hash` (default): deterministic local embedding
- `sentence-transformers`: higher quality, requires a local model (install with `uv sync --extra embeddings`)
- `none`: lexical-only retrieval

### IngestEvent

Each ingest produces an immutable lineage record (`ingest_events` table).

Captures:

- `content_sha256` and `prev_content_sha256`
- whether content changed (`changed`)
- chunking settings used
- embeddings backend/model used
- `doc_version`
- optional `notes`

This allows you to debug:

- “why did retrieval change?”
- “which settings were used when this doc was ingested?”

The UI exposes this per-doc and also as a global audit feed.

---

## Core workflows

### Ingest

1. Extract text (TXT/MD directly; PDF via PyMuPDF + optional OCR)
2. Chunk text
3. Embed chunks (optional)
4. Replace previous chunks/embeddings for the doc
5. Update doc metadata (hash, bytes, chunk count, version)
6. Insert an ingest event

### Query

1. Validate input length
2. Detect prompt injection / circumvention patterns
3. Retrieve top chunks (hybrid lexical+vector)
4. Answer using the configured provider
5. Return citations + answer
6. Refuse if evidence is insufficient

By default, the API enforces **citations required** (`CITATIONS_REQUIRED=1`).

### Maintenance (retention purge)

For private deployments with persisted storage, you can purge documents whose retention
policy has expired:

- Dry run:
  - `make purge-expired`
  - or `uv run python -m app.cli purge-expired`
- Apply deletes:
  - `make purge-expired-apply`
  - or `uv run python -m app.cli purge-expired --apply`

---

## Deployment modes

### Public demo mode

When `PUBLIC_DEMO_MODE=1`:

- uploads/eval/deletes/chunk viewing are disabled
- answering defaults to extractive
- rate limiting is enabled
- citations-required behavior is forced on

### Private mode

A private/internal deployment can enable:

- uploads: `ALLOW_UPLOADS=1`
- connectors (e.g. GCS sync): `ALLOW_CONNECTORS=1`
- eval: `ALLOW_EVAL=1`
- chunk view: `ALLOW_CHUNK_VIEW=1`
- doc delete: `ALLOW_DOC_DELETE=1`

These must never be enabled on a public URL.
