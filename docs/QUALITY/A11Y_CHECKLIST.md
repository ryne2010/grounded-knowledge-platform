# Accessibility checklist

Status: **Completed** (2026-02-21)

Task:

- `agents/tasks/TASK_ACCESSIBILITY_AUDIT.md`

## Tested flows

- [x] Ask page: question input, suggested queries, submit/reset/cancel controls
- [x] Ask page dialogs: guided tour + explain drawer + retrieval dialog
- [x] Citations list keyboard access (open doc context link, copy citation button)
- [x] Docs list filter + table links to doc detail
- [x] Doc detail metadata/chunk filter/actions + dialogs
- [x] Demo mode banner and disabled-state messaging in navigation

## Common checks

- [x] Interactive controls reachable by keyboard
- [x] Visible focus indicator on core controls/links
- [x] Dialogs are focus-trapped and ESC closable
- [x] Dialogs provide a keyboard-reachable close affordance
- [x] Core form fields have explicit labels
- [x] Error and status messaging is announced via `role=\"alert\"`/`role=\"status\"` where relevant
- [x] Disabled states include explanatory text (not color-only)

## Fixes applied

- Added a global skip link to main content in app shell and a stable `main` target.
- Added/strengthened focus-visible styles for primary navigation and utility links.
- Added explicit label wiring for:
  - docs filter input
  - doc-detail chunk filter input
- Added announcement roles for key error/status surfaces in Ask/Docs/Doc Detail flows.
- Added default close button to dialog content with `aria-label=\"Close dialog\"`.
- Added polite live-region semantics to top status/offline banners.

## Notes / residual risk

- Data tables are virtualization-heavy and not optimized yet for advanced screen-reader table narration.
- Accessibility linting (`eslint-plugin-jsx-a11y`) is not enabled yet; this checklist is currently manual + code-review based.
