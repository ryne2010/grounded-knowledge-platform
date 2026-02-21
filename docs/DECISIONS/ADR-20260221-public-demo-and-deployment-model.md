# ADR: Public demo posture and deployment model

## Context

This repository is intended to be deployed as a **public** demo and to feel like a production-grade platform.

Key constraints:

- Public hosting (anonymous users).
- Live/public deployments must be **extractive-only** (no external LLM calls).
- Local development may use **Ollama**.
- Production persistence is **Cloud SQL Postgres** (baseline).
- Boundary model is **one GCP project per client** (not in-app multi-tenancy).
- Public demo uses **only** the bundled demo corpus (`data/demo_corpus/`).
- No edge WAF / CDN is assumed for the baseline demo.
- UI uses a **neutral** palette (no custom brand kit required).
- Private deployments may enable ingestion connectors; connector sync is **add/update only**.

## Decision

We will:

1. Treat `PUBLIC_DEMO_MODE=1` as the default posture for any public demo deployment.
2. Keep live/public deployments extractive-only by default (`LLM_PROVIDER=extractive`).
3. Use Cloud SQL Postgres as the production storage baseline (SQLite remains for local fallback).
4. Model client isolation at the infrastructure boundary (one project per client), not via tenant-aware application logic.
5. Restrict the public demo to the bundled demo corpus and keep ingestion endpoints disabled.
6. Keep the portfolio UI neutral (no bespoke palette), while still feeling like a modern SaaS admin.
7. Allow private deployments to enable connectors (e.g. GCS sync), and keep connector behavior add/update only.

## Consequences

- The public demo is safer, cheaper, and harder to abuse.
- Private/client deployments can enable uploads and richer features behind auth, but the demo remains read-only.
- Multi-tenancy is treated as an optional future enhancement, not required for the primary roadmap.

## Alternatives considered

- Add an edge WAF/rate limiting layer: rejected for the baseline demo; the app uses built-in rate limiting and Cloud Run instance caps.
- Multi-tenant single deployment: rejected as the primary model; one project per client is simpler for IAM, cost, and incident response.
