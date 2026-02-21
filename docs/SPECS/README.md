# Specs

This folder is for **durable, reviewable specs**.

Guidelines:

- Keep specs small and decision-oriented.
- Prefer concrete acceptance criteria and explicit non-goals.
- If a spec changes architecture/contracts, add an ADR in `docs/DECISIONS/`.

Suggested workflow:

1. Start from `SPEC_TEMPLATE.md`.
2. Link the spec from a task doc in `agents/tasks/`.
3. When implemented, update the spec with any learnings/tradeoffs.

## Current specs

- `UI_UX_PRODUCTION_POLISH.md`
- `CLOUDSQL_HARDENING.md`
- `CONNECTOR_GCS_INGESTION.md`
- `PUBSUB_EVENT_INGESTION.md`
- `SCHEDULER_PERIODIC_SYNC.md`

Additional specs (private deployment maturity):

- `AUTH_PRIVATE_DEPLOYMENTS.md`
- `EVAL_HARNESS_PRODUCTIZATION.md`
- `OBSERVABILITY_OPS.md`
- `GOVERNANCE_METADATA.md`
- `BIGQUERY_EXPORT.md`
