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

## Defense in depth (recommended)

- Put an additional rate limiter / WAF in front of the service (Cloudflare, Cloud Armor, etc.)
- Set Cloud Run `--max-instances` to cap burst cost and reduce abuse impact
- Configure budgets and billing alerts in your cloud account
- Review logging settings so you don't store sensitive request bodies inadvertently
