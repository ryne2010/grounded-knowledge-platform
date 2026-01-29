# Security & Confidentiality for Knowledge Systems

Knowledge systems often store and retrieve **sensitive data** (legal matters, financial records, insurance policies, customer PII).

This document lists practical controls that make a knowledge platform production-ready.

## Data classification

Start by classifying what you store:

- **Public**: safe to share externally.
- **Internal**: business-only.
- **Confidential**: client data, contracts, privileged communications.
- **Regulated**: PII/PHI/PCI or other regulated data.

Classification drives where you can run the system:

- Public data → a public Cloud Run demo is fine.
- Confidential/regulated data → prefer on-prem or private cloud with strict access control.

## Access control

Key principles:

- **Least privilege**: users only see what they must see.
- **Matter / case scoping** (law firms): a user can only retrieve documents from matters they are assigned to.
- **Service accounts**: isolate machine access from human access.

## Encryption

- Encrypt data **at rest** (disk / database).
- Encrypt secrets (API keys, credentials) in a secrets manager.
- Consider envelope encryption / KMS-backed key management for high-sensitivity fields.

## Auditability

For sensitive deployments, log:

- document ingestion events
- queries (with redaction as needed)
- retrieved document identifiers
- authz decisions (who accessed what)

## Safety against prompt injection

Prompt injection is when a document tries to override system behavior.

Mitigations:

- never allow documents to change system instructions
- require citations for answers
- add **refusal mode** when evidence is weak
- for LLMs: keep a hard boundary between "instructions" and "evidence"

## Public demo posture

For a public demo:

- disable uploads
- disable eval endpoints
- keep answers extractive-only
- enable rate limiting

These settings are enforced by `PUBLIC_DEMO_MODE=1` in this repo.
