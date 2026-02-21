# Task: UI/UX Production Polish (Modern SaaS Admin)

Spec: `docs/SPECS/UI_UX_PRODUCTION_POLISH.md`
Owner: @codex
Suggested sub-agent: `agents/subagents/frontend_ux.md`


## Objective

Elevate the web UI to a **production-quality modern SaaS admin** experience:

- polished + neutral (no custom brand kit required)
- consistent component system + spacing/typography
- strong empty/loading/error states
- trust-first citations UX
- a11y baseline

## Scope

- App shell upgrades
  - desktop sidebar nav + top utility bar
  - mobile-friendly nav (no cramped desktop header)
  - environment badges (public demo / rate limit / citations required)
- UX polish
  - skeletons + toasts
  - consistent forms + validation
  - clear disabled-state explanations in `PUBLIC_DEMO_MODE`
- Citations UX
  - citation cards with “open doc” + “copy quote”
  - optional “why this answer?” drawer/panel (non-debug)
- A11y + keyboard navigation pass

## Non-goals (for this task)

- full rebrand / marketing site
- auth UI (OIDC login) — can be a future task

## Acceptance criteria

- All primary flows usable via keyboard
- No obvious layout shift during streaming
- Pages share consistent headers, spacing, and component variants
- Demo-mode guardrails are obvious and explained

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
- `make web-typecheck`

## Notes

- Prefer improvements inside `web/src/portfolio-ui` so changes propagate consistently.
- Keep the UI safe by default; do not expose ingestion controls in public demo mode.
