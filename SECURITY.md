# Security notes

This repository is a **reference implementation**. If you deploy it publicly, treat it like an Internet-facing service.

## Safe public demo configuration

Use `PUBLIC_DEMO_MODE=1` for public demos. When enabled, the service:

- **Disables ingestion endpoints** (no file/text uploads)
- **Disables eval endpoints**
- Forces **extractive-only** answering (no external LLM calls)
- Enables basic in-app rate limiting and clamps query parameters

This significantly reduces the risk of abuse and unintended data storage.

## Sensitive / confidential deployments

If you ingest sensitive documents:

- Prefer a **local embeddings backend** (`EMBEDDINGS_BACKEND=sentence-transformers`)
- Prefer a **local LLM provider** (`LLM_PROVIDER=ollama`) or use `extractive`
- Avoid sending retrieved content to third-party APIs unless you have explicit approval
- Keep `ALLOW_CHUNK_VIEW=0` unless you explicitly need to browse raw chunks. (Retrieval debug will not include full chunk text unless chunk viewing is enabled.)

## Defense in depth (recommended)

- Use **PUBLIC_DEMO_MODE=1** for any Internet-facing deployment (read-only + extractive-only).
- Keep Cloud Run `--max-instances` low (cost and abuse control).
- Keep `RATE_LIMIT_ENABLED=1` (application-level rate limiting).
- Configure budgets and billing alerts in your cloud account.
- Review logging settings so you don't log sensitive content.
- Prefer **one GCP project per client** to keep IAM and cost boundaries clean.
