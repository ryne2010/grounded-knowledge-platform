# Spec: Auth for private deployments

## Context

The public deployment of this repo is intentionally **anonymous** and **safe-by-default** (no uploads, no connectors, extractive-only, demo corpus only).

Private, per-client deployments need a simple, Cloud Run-friendly way to protect:

- the UI
- the API
- “dangerous” endpoints (uploads, deletes, connector sync, eval)

We do **not** want to add a heavy identity solution for the portfolio baseline.

## Goals

- Support a minimal auth path that works well on Cloud Run:
  - `AUTH_MODE=api_key`
  - role-based authorization (`reader`, `editor`, `admin`)
- Keep **public demo behavior unchanged**:
  - `PUBLIC_DEMO_MODE=1` always behaves anonymous + read-only
- Make it obvious how to extend to stronger enterprise auth later (OIDC/IAP), without implementing it now.

## Non-goals

- Full enterprise SSO / RBAC UI
- Multi-tenant auth (one deployment per client)
- Fine-grained per-document ACLs (future)

## Proposed design

### User experience

- **Public demo**: no login prompts.
- **Private deployment**:
  - UI loads normally, but API calls require an API key.
  - If the API key is missing/invalid, the UI shows a “Private deployment: authentication required” screen.

### API surface

- Request header: `X-API-Key: <key>`
- Environment configuration:
  - `AUTH_MODE=none|api_key` (default: `none`)
  - `API_KEYS_JSON` (recommended): JSON mapping of key → role
  - `API_KEYS` or `API_KEY` (fallback): shared key(s) mapped to `admin`

Authorization rules:

- `reader`: query + read-only docs views
- `editor`: ingest endpoints (when enabled)
- `admin`: deletes, chunk view, eval, connector sync

### Data model

No DB changes required.

(Optionally later: add an `audit_events` table that records admin actions. That is tracked separately.)

### Security / privacy

- `PUBLIC_DEMO_MODE=1` hard-overrides:
  - read-only behavior
  - uploads/connectors/eval must remain disabled
- Never log API keys.
- Avoid “security by obscurity” (always enforce server-side).

### Observability

- For 401/403 responses, log a structured event:
  - `event=auth.denied`, `reason`, `path`, and request id
- Add counters (future OTEL metrics): denied requests per path.

### Rollout / migration

- Default stays `AUTH_MODE=none`.
- Private deployments enable `AUTH_MODE=api_key`.
- Document exact env examples in `docs/DEPLOY_GCP.md`.

## Alternatives considered

- Full OIDC/IAP JWT verification: more “real”, but adds complexity and requires a stronger demo story.
- Basic auth: workable, but less Cloud Run idiomatic and harder to rotate safely.

## Acceptance criteria

- When `AUTH_MODE=api_key`:
  - missing/invalid key → 401
  - valid `reader` key → can query + view docs, cannot ingest or run connectors
  - valid `admin` key → can access admin-only endpoints
- When `PUBLIC_DEMO_MODE=1`:
  - behavior remains anonymous + read-only even if auth env vars are set

## Validation plan

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
