# UI/UX Production Polish

Status: **Draft** (2026-02-21)

Owner: Repo maintainers

Related tasks:

- `agents/tasks/TASK_UI_UX_POLISH.md`
- `agents/tasks/TASK_DEMO_GUIDED_TOUR.md`
- `agents/tasks/TASK_ACCESSIBILITY_AUDIT.md`

## Context

This repo is intentionally **production-minded** (safe defaults, runbooks, CI, Cloud Run deploy posture).
The UI should *also* read as production-grade — but with a **modern SaaS admin** vibe:

- polished and modern (not “internal tool grey”)
- fast, accessible, and trustworthy
- designed for **public hosting** while still supporting private “admin” deployments

We already have a functional React UI (TanStack Router + React Query + Tailwind + Radix primitives).
This spec defines the polish pass to elevate the look/feel to a production SaaS admin experience.

## North star

A new user should instantly feel:

- “This is a real product” (consistent layout, spacing, typography)
- “This is safe to trust” (clear citations + data provenance)
- “This is well-operated” (status indicators, guardrails, helpful errors)

## Design principles

1. **SaaS admin layout**
   - Desktop: left sidebar navigation + top utility bar
   - Mobile: condensed nav (no cramped desktop nav)
   - Clear page headers (title + description + primary action)

2. **Neutral, not loud**
   - No custom brand kit is required for the portfolio demo (neutral palette + simple mark)
   - Restraint: keep the document and citations as the “hero” content

3. **Trust through explainability**
   - Citations are first-class (always visible, easy to open)
   - “Why this answer?” is a supported UX pattern, not a debug feature

4. **Accessibility baseline**
   - Keyboard navigation everywhere
   - Visible focus styles
   - Screen-reader friendly labeling
   - Avoid “color-only” meaning

## Information architecture

Primary sections:

- **Ask** (streaming, extractive answer + citations)
- **Search** (browse corpus by query)
- **Docs** (inventory + doc detail page)
- **Ingest / Connectors** (private-only, disabled in public demo)
- **Maintenance** (private-only, safe-by-default)
- **Meta** (diagnostics / environment visibility)

## UI components checklist

- App shell
  - sidebar nav (active state, icons optional)
  - top bar (status, environment badges, theme toggle)
- Feedback + state
  - loading skeletons
  - empty states with clear calls-to-action
  - error surfaces with actionable troubleshooting
- Trust
  - citation cards (doc title, source, chunk preview)
  - “open doc” affordance
  - “copy quote + citation” affordance
- Forms
  - consistent labels + helper text
  - inline validation
  - safe defaults (esp. ingestion/config)

## Required UX behaviors

- **PUBLIC_DEMO_MODE** must be obvious in the UI:
  - A badge (“public read-only demo”) in the top bar
  - Ingest/eval/maintenance actions visible but disabled with explanation

- **Demo-friendly onboarding** should exist (public demo):
  - Suggested queries users can click to run
  - A lightweight guided tour (optional) that explains:
    - what the corpus is
    - how to verify citations
    - why refusals happen
- **Citations required** must be visible:
  - If no citations found -> refusal UX with explanation and suggestions
- **Streaming** must feel stable:
  - token-by-token updates without layout jumping
  - clear “answer complete” affordance

## Quality bar (acceptance criteria)

- A11y:
  - keyboard navigation works on all primary flows
  - dialogs are focus-trapped and ESC closable
- Performance:
  - no obvious layout shift during streaming
  - list views remain responsive (virtualization optional later)
- Consistency:
  - standard spacing scale, consistent component variants
- Branding:
  - consistent header/labels, cohesive typography
  - neutral by default (no bespoke palette)

- Demo onboarding:
  - A first-time visitor can reach “citations verified” in < 2 minutes without reading docs

## Implementation notes

- Prefer existing `web/src/portfolio-ui` primitives and patterns.
- Keep changes compatible with `PUBLIC_DEMO_MODE` safety defaults.
- Avoid introducing new heavy UI frameworks unless the value is clear.

