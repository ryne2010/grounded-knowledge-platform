# Security model

This document is a practical “how we stay safe” view, not a formal compliance report.

Decision record: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

Related:
- `SECURITY.md`
- `docs/IAM_STARTER_PACK.md`
- `docs/DEPLOY_GCP.md`

---

## Deployment boundary

- **One GCP project per client** is the primary isolation boundary.
- This keeps IAM, billing, incident response, and audit scope clean.

Non-goal: in-app multi-tenancy/workspaces (optional future only).

---

## Public demo posture (safe-by-default)

`PUBLIC_DEMO_MODE=1` enforces:

- anonymous access
- read-only behavior (no uploads, no connectors, no eval endpoints)
- extractive-only answering
- citations-required
- rate limiting on query
- “dangerous” endpoints hard-disabled even if called directly

We do **not** assume an edge WAF (no Cloud Armor/Cloudflare in the baseline demo).

Defense in depth:
- Cloud Run max instances caps
- request size limits
- conservative timeouts
- no secrets required for demo operation

---

## Private deployments (recommended posture)

Private deployments should enable auth:

- `AUTH_MODE=api_key` (baseline)
- future: `AUTH_MODE=oidc` (Cloud Run identity / IAP style)

Roles:
- `reader`: query + read-only browsing
- `editor`: ingest uploads/text (when enabled)
- `admin`: connectors, eval, deletes, maintenance operations

Principle: privileged operations are gated **twice**
- role checks (auth)
- feature flag checks (`ALLOW_*`) + demo-mode hard disable

---

## Data and content safety

Threats to consider:
- **prompt injection** attempts to override system instructions
- **data exfiltration** through citations or chunk viewing
- **abuse/cost attacks** via repeated expensive requests

Mitigations:
- prompt-injection detector + conservative refusal
- citations-required defaults; refusal when evidence is weak
- chunk viewing disabled by default; never enabled for public demo
- query rate limiting and Cloud Run instance caps

---

## Secrets and keys

- Production should store secrets in **Secret Manager** (not checked into the repo).
- DB credentials should be rotated on a reasonable cadence.
- Avoid logging secrets or document content in plaintext logs.

---

## Auditability

- Append-only `audit_events` capture admin actions (connector sync, deletes, metadata updates, eval runs).
- Keep operational workflows documented in `docs/RUNBOOKS/`.
