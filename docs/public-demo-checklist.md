# Public demo deployment checklist (safe, low-cost)

This checklist is optimized for running a **public-facing demo** of the Grounded Knowledge Platform with:
- no user uploads
- no external LLM/API calls
- scale-to-zero behavior
- minimal cost exposure

## Safety-first app config

- [ ] Set `PUBLIC_DEMO_MODE=1` (forces extractive-only, disables uploads/eval)
- [ ] Keep `ALLOW_UPLOADS` unset/false (demo mode overrides this anyway)
- [ ] Keep `LLM_PROVIDER=extractive` (demo mode overrides this anyway)
- [ ] Ensure citations-required behavior is enabled (`CITATIONS_REQUIRED=1`, forced in demo mode)
- [ ] Use local embeddings (`EMBEDDINGS_BACKEND=hash` is recommended for a public demo)
  - `sentence-transformers` is supported but requires an optional dependency + local model and increases image size
- [ ] Ensure the demo corpus is **open-source/public** content only (`data/demo_corpus/`)

## Cloud Run deployment guardrails

- [ ] Deploy with `min_instances = 0` (scale to zero)
- [ ] Set a **hard cap**: `max_instances = 1`
- [ ] Use small resources: `cpu = 1`, `memory = 256Mi`
- [ ] Set a reasonable request timeout (e.g. 10–30s) to avoid runaway requests
- [ ] Limit concurrency if needed (optional): start with 20–40

## Network + access

- [ ] Prefer Cloud Run public URL + **read-only endpoints** only
- [ ] If you want an extra safety layer, put Cloudflare (free) or a simple reverse proxy/WAF in front
- [ ] **Do not** enable a Serverless VPC Access connector unless you need private networking (it is not free)

## Rate limiting and abuse prevention

- [ ] Keep `RATE_LIMIT_ENABLED=1`
- [ ] Optionally set `RATE_LIMIT_SCOPE=api` to rate-limit all API endpoints (not just `/api/query`)
- [ ] Tune `RATE_LIMIT_MAX_REQUESTS` to something reasonable (e.g. 20–60 per minute)
- [ ] Keep `MAX_QUESTION_CHARS` capped (default 2000)
- [ ] Keep `MAX_TOP_K` capped (default 8)

## Logging and privacy

- [ ] Confirm logs do **not** include document text or full user questions
- [ ] Verify request logs include `request_id`, status, latency (structured JSON)
- [ ] Set log retention appropriately (in GCP Logging settings) if you expect any traffic

## Billing hygiene

- [ ] Create a **budget + alerts** in GCP billing
- [ ] Keep Artifact Registry storage small (delete old images)
- [ ] Keep Cloud Build usage minimal (reuse cached builds where possible)

## Smoke test

- [ ] Open `/` and confirm the UI loads
- [ ] Call `/api/meta` and verify:
  - `public_demo_mode: true`
  - `uploads_enabled: false`
  - `eval_enabled: false`
  - `llm_provider: extractive`
- [ ] Call `/api/query` with a few questions and confirm citations/refusal behavior
- [ ] Confirm `/api/ingest/file` returns 403
