# Spec: BigQuery export + modeling

## Context

Private deployments may want to integrate the knowledge platform into a broader data platform lifecycle.

This repo should demonstrate a small but credible export pattern:

- operational tables (ingestion runs, queries, eval results)
- exported to BigQuery
- modeled into raw → curated → marts

## Goals

- Provide a repeatable export mechanism (private deployments only).
- Document the dataset/table schema mapping.
- Provide example SQL models (raw→curated→marts) that tell the “data architect” story.

## Non-goals

- Real-time streaming into BigQuery
- Full dbt project scaffolding
- Public demo export

## Proposed design

### User experience

- Operators can enable exports for private deployments.
- Export can be run manually or on a schedule (Cloud Scheduler).

### API surface

Baseline is CLI-driven:

- `gkp_cli export-bigquery --project ... --dataset ...`

Optional API (private only):

- `POST /api/exports/bigquery/run` (admin)

### Data model

No required DB changes.

Export maps Postgres tables to BigQuery tables, with partitioning where appropriate (e.g., by date).

### Security / privacy

- Export is admin-only and disabled unless explicitly enabled.
- Service account used for export should have least privilege to write into a single dataset.

### Observability

- Export logs include job id and rows exported.
- Failures are surfaced in logs and (optionally) alert policies.

### Rollout / migration

- Start with a minimal export set:
  - query logs
  - ingestion runs
  - eval runs
- Add modeling examples (SQL files) for a portfolio-grade narrative.

## Alternatives considered

- Export via Dataflow: heavy for this repo.
- Export via CDC: great, but unnecessary complexity.

## Acceptance criteria

- A private deployment can export key operational datasets into BigQuery.
- Modeling examples are documented and realistic (partitioning, clustering, naming).

## Validation plan

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
