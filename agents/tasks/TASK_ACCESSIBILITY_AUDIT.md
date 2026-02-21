# Task: Accessibility audit + fixes (UI)

Spec: `docs/SPECS/UI_UX_PRODUCTION_POLISH.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/frontend_ux.md`

## Goal

Ensure the UI meets a solid accessibility baseline appropriate for a production SaaS admin:

- keyboard navigation works on core flows
- focus states are visible and consistent
- dialogs are focus trapped and ESC closable
- forms have labels and helpful error messaging

## Scope

Primary flows:

- Ask (query + answer + citations)
- Docs list + doc detail
- Demo-mode banners and disabled states

## Requirements

- Add a lightweight a11y checklist doc (in-repo) capturing what was tested and what was fixed.
- Fix the top priority issues found (focus, labeling, roles).

Optional (nice-to-have):

- add `eslint-plugin-jsx-a11y` or similar linting for common mistakes
- add a minimal Playwright/RTL test asserting keyboard navigation for 1 key flow

## Deliverables

- Code fixes in `web/src/` as needed
- New doc:
  - `docs/QUALITY/A11Y_CHECKLIST.md` (create folder if missing)

## Acceptance criteria

- Core flows are usable with keyboard only.
- No “trap” scenarios where the user cannot escape a modal/dialog.
- The a11y checklist doc exists and is accurate.

## Validation

- `make web-typecheck`
- `python scripts/harness.py lint`
- `python scripts/harness.py test`

