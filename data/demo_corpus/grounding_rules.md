# GCP Data Architecture Principles

This document summarizes practical data-architecture guidance for Google Cloud workloads.

Design principles:
- Separate operational systems from analytical systems.
- Keep raw, curated, and serving layers explicit.
- Prefer schema contracts at ingestion boundaries.
- Track lineage and schema fingerprint changes over time.

Data quality posture:
- Validate required fields at ingest.
- Fail fast for contract-breaking changes.
- Surface warnings for additive or non-breaking drift.
- Keep validation outputs queryable for audits.

Governance and access:
- Use IAM groups for role assignment.
- Classify datasets by sensitivity and retention policy.
- Restrict broad data export permissions.
- Log access and admin actions for high-risk datasets.

Serving best practices:
- Design for reproducibility across environments.
- Keep transformations versioned and testable.
- Document assumptions near data contracts.
- Prefer deterministic jobs over ad-hoc manual patches.
