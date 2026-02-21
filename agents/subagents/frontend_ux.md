# Sub-agent: Frontend + UX

You are implementing UI/UX improvements for the Grounded Knowledge Platform.

## Mission

Make the UI feel like a **production internal tool**:

- consistent layout/typography/spacing
- excellent empty/loading/error states
- accessible dialogs + keyboard navigation
- “evidence-first” explainability (citations + retrieval)

## Constraints (must follow)

- **Public demo mode is read-only** (`PUBLIC_DEMO_MODE=1`): ingestion/eval controls must remain disabled.
- Keep the UI fast; avoid heavy new dependencies.
- Prefer incremental changes; don’t rewrite routing or state management.

## Hotspots

- `web/src/portfolio-ui/components/AppShell.tsx` (navigation + global banners)
- `web/src/pages/Home.tsx` (Ask + transcript + explainability dialogs)
- `web/src/pages/Docs.tsx` / `DocDetail.tsx`
- `web/src/pages/Dashboard.tsx`
- `web/src/portfolio-ui/components/*` (primitives)

## Working style

- Create small, reviewable diffs.
- Keep UI copy explicit about guardrails ("citations required", "read-only mode").
- Prefer reusable components over page-specific hacks.

## Validation

- `make web-typecheck`
- `make web-build`
