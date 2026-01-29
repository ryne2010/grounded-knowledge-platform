# Event-Driven Data Platform Patterns (GCP)

This document outlines patterns for building **event-driven data platforms** on Google Cloud.

The focus is on reliability: idempotency, replayability, schema drift handling, and observability.

## A common workflow

1. A file arrives (e.g., an emailed Excel export saved to a bucket).
2. A trigger publishes a message to a queue/topic.
3. A worker validates and parses the file.
4. Cleaned data is loaded to an analytical store.
5. Downstream consumers (dashboards, alerts, ML jobs) respond.

## Building blocks on GCP

### Pub/Sub

Use Pub/Sub when you need:

- fan-out to multiple consumers
- durable buffering
- decoupling producers from consumers

### Cloud Tasks

Use Cloud Tasks for:

- controlled retry semantics
- rate-limited processing
- idempotent background work

### BigQuery

BigQuery is a strong fit for:

- analytical querying
- partitioned tables and cost control
- geospatial queries

## Reliability patterns

### Idempotency

Every ingestion run should have a stable identifier (e.g., file hash + source + effective date).
If the same file is delivered twice, processing should produce the same final state.

### Backfills and replays

You should be able to:

- reprocess a date range
- re-run from raw files
- compare outputs across versions

### Schema drift

Spreadsheet feeds drift over time. Typical mitigations:

- enforce a canonical schema
- capture unknown columns as metadata
- add data-quality gates and alerts

## Observability

The minimum viable operational signals:

- pipeline latency (time from arrival to load)
- error rate and retry counts
- row counts and basic distributions
- alerting on missing deliveries or unusual changes