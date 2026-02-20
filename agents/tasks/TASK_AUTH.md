# Task: Add authn/authz for private deployments

Owner: @codex

## Goal

Add optional authentication + authorization suitable for **Cloud Run** deployments so that:

- public demo remains anonymous + safe
- private deployments can protect UI + API
- dangerous endpoints (upload, doc delete, chunk view, eval) can be restricted by role

## Requirements

### Supported modes

- `AUTH_MODE=none` (default)
- `AUTH_MODE=api_key`
  - requests must include `X-API-Key: <key>`
  - server validates against `API_KEYS` env var (comma-separated) or `API_KEY` single

Stretch goal:

- `AUTH_MODE=oidc`
  - validate Google IAP / OIDC JWT (Cloud Run identity)

### Authorization

- introduce roles: `reader`, `editor`, `admin`
- map API keys to roles via env (`API_KEYS_JSON` or similar)
- enforce:
  - reader: query, docs list/detail, ingest events
  - editor: ingest text/file
  - admin: doc delete, chunk view, eval

### Safety invariants

- `PUBLIC_DEMO_MODE=1` must always behave like `AUTH_MODE=none` + read-only
- If `CITATIONS_REQUIRED=1`, do not allow answers without citations

## Implementation notes

- Add a small `app/auth.py` module:
  - FastAPI dependency for auth
  - request context with `principal` + `role`
- Add middleware to attach `principal` to request state
- Keep OpenAPI docs accessible in demo mode, but require auth in private auth modes

## Tests

- unit tests for:
  - missing key → 401
  - invalid key → 401
  - valid key reader → 200 on `/api/docs`, 403 on `/api/ingest/text`
  - valid key admin → allowed on delete

## Docs

- update `docs/CONTRACTS.md` with new env vars
- update `docs/DEPLOY_GCP.md` with Cloud Run env examples
