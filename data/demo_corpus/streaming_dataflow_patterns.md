# Streaming Pipelines: Pub/Sub and Dataflow

For near-real-time analytics on GCP, a common architecture is Pub/Sub plus Dataflow.

Reference flow:
- Producers publish events to Pub/Sub topics.
- Dataflow validates, enriches, and routes events.
- Valid events land in BigQuery serving tables.
- Invalid events route to dead-letter topics for triage.

Reliability patterns:
- Use idempotent keys to handle duplicate deliveries.
- Define clear retry and dead-letter policies.
- Keep schema evolution backward compatible for stream consumers.
- Monitor lag, throughput, and error ratios continuously.

Data architect checklist:
- Define event contract ownership per domain team.
- Version event schemas and publish migration guidance.
- Separate operational and analytical retention requirements.
- Align SLAs between producers, stream processors, and consumers.
