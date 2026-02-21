# Task: Doc viewer + citations UX (production feel)

Spec: `docs/SPECS/UI_UX_PRODUCTION_POLISH.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/frontend_ux.md`

## Goal

Make citations *verifiable* and *pleasant* to inspect:

- citations are clickable and take the user to the supporting source
- a doc viewer renders document text with highlighted cited spans/snippets
- the experience works in **public demo mode** without exposing full chunks

## Requirements

### UI behaviors

- In search results / answer view:
  - citations list shows: doc title + snippet + (optional) score indicator
  - click citation → navigates to Doc Detail and auto-scrolls to the cited chunk/snippet

- In Doc Detail:
  - show doc metadata (title/source/classification/retention/tags)
  - show “Citations in this doc” section when navigated via a citation
  - highlight the cited snippet(s) in context
  - provide “copy citation” button (copy quote + doc title + doc_id)

### Safety / gating

- Public demo:
  - may show **snippets** tied to citations
  - must **not** expose full chunk text unless `ALLOW_CHUNK_VIEW=1` (which should remain off in demo)

- Private deployments:
  - chunk view may be enabled explicitly; if enabled, provide “view full chunk” affordance
  - dangerous operations (delete doc) remain admin-only and gated

### Accessibility

- keyboard navigable citation list
- focus state when jumping to cited content
- avoid “scroll-jank” (smooth scroll, stable layout)

## Deliverables

- UI:
  - citation component improvements
  - Doc Detail citation-jump behavior
  - snippet highlighting in doc view
- Tests:
  - at least one UI unit test (or integration test) that verifies “click citation → scroll to highlight”
- Docs:
  - update `docs/SPECS/UI_UX_PRODUCTION_POLISH.md` if any behavior changes

## Acceptance criteria

- Citations are clickable and navigate to the correct doc context.
- Doc Detail highlights cited snippets without exposing full chunks in public demo mode.
- Keyboard navigation and focus states are correct when jumping to cited content.

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
- `make web-typecheck`
