# Data Contracts (Tabular Ingests)

This repo supports optional contract-driven validation for tabular ingests:
- `.csv`
- `.tsv`
- `.xlsx`
- `.xlsm`

## Contract format (YAML v1)

```yaml
version: 1
name: customer_events
owner: data-platform
columns:
  - name: event_id
    type: string
    required: true
  - name: occurred_at
    type: timestamp
    required: true
checks:
  min_rows: 1
  max_null_fraction:
    occurred_at: 0.0
```

Supported types:
- `string`
- `int`
- `float`
- `bool`
- `timestamp`
- `date`

## API usage

`POST /api/ingest/file` accepts an optional multipart field:
- `contract_file` (YAML, max 64KB)

Behavior:
- if contract is provided, validation runs before ingest commit
- failing validation returns `400`
- schema fingerprint is always recorded for tabular ingests
- drift is flagged when the new schema fingerprint differs from the previous ingest for the same doc

## CLI usage

Single file:

```bash
uv run python -m app.cli ingest-file path/to/file.csv --contract path/to/contract.yaml
```

Folder:

```bash
uv run python -m app.cli ingest-folder data/ --contract path/to/contract.yaml
```

The folder command applies contracts only to tabular files.

## Lineage fields

`ingest_events` now includes:
- `schema_fingerprint`
- `contract_sha256`
- `validation_status` (`pass|warn|fail`)
- `validation_errors`
- `schema_drifted`

These are surfaced in the Doc Detail lineage table and dashboard validation widget.
