# TASK: Data contracts + schema drift for tabular ingests

## Goal

Add **optional, contract-driven validation** for tabular ingests (`.csv`, `.tsv`, `.xlsx`, `.xlsm`) so the platform can:

- Validate column presence/types/required fields
- Detect schema drift between ingests
- Record contract + validation outcomes in ingest lineage
- Surface validation status in the UI

This is intentionally scoped to be a **portfolio-grade** implementation that demonstrates data-platform patterns (contracts, drift, lineage) without turning the project into a full data-quality framework.

## Non-goals

- Full Great Expectations parity
- Complex type inference across every file format
- Row-level quarantine or repair workflows
- Multi-tenant access control (covered by auth tasks)

## Contract format

### YAML schema (v1)

Example:

```yaml
version: 1
name: customer_events
owner: data-platform
columns:
  - name: event_id
    type: string
    required: true
    unique: true
  - name: occurred_at
    type: timestamp
    required: true
  - name: lat
    type: float
  - name: lon
    type: float
checks:
  min_rows: 1
  max_null_fraction:
    occurred_at: 0.0
```

Notes:

- Start with a minimal set of types: `string`, `int`, `float`, `bool`, `timestamp`, `date`.
- Allow extra columns by default; add `strict: true` later if needed.

## API / CLI

- `POST /api/ingest/file` accepts an **optional** `contract_file` form field.
- CLI:
  - `gkp_cli ingest-file <path> --contract <contract.yml>`
  - `gkp_cli ingest-folder <dir> --contract <contract.yml>` (applies to matching tabular files)

## Storage / lineage

Add columns to `ingest_events`:

- `schema_fingerprint` (sha256 of normalized header/types)
- `contract_sha256`
- `validation_status` (`pass` | `warn` | `fail`)
- `validation_errors_json` (array of strings / structured objects)

Optionally add doc-level “latest schema” fields for faster UI.

## UI

- **Ingest** page: optional contract upload (only shown when a tabular file is selected).
- **Doc detail → Lineage**: display validation status and drift indication.
- **Dashboard**: add a “recent validation failures” widget.

## Drift detection behavior

- When ingesting tabular content, compute a `schema_fingerprint`.
- If previous ingest exists for the doc, compare fingerprints:
  - If changed → mark as `drifted=true` in the new ingest event (or infer in UI).

## Security & safety

- Parse YAML with a safe loader (`yaml.safe_load`).
- Enforce max contract size (e.g. 64KB).
- Validate contract against a Pydantic model.
- Never execute expressions from YAML.

## Acceptance criteria

- Contract validation runs for tabular ingests when a contract is supplied.
- Clear error messages for missing required columns / invalid types.
- Validation + schema fingerprints are written to ingest lineage.
- UI shows pass/warn/fail and indicates drift.
- Tests cover:
  - happy path
  - missing required column
  - drift detection between two ingests
  - contract parsing failure

## Implementation plan

1. Add `app/contracts/tabular_contract.py` (Pydantic models + normalization).
2. Add validation + schema fingerprinting in `app/ingestion.py` for tabular flows.
3. Extend ingest endpoints + CLI to accept optional contract.
4. Add additive migrations for `ingest_events`.
5. Extend API response models + UI rendering.
6. Add tests for contract validation + drift.
7. Add docs: `docs/DATA_CONTRACTS.md`.
