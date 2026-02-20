# Task: Make the Web UI an offline-friendly PWA

Owner: @codex

## Goal

Align the Web UI with the “offline-first PWA” capabilities described in the job apps/case studies:

- installable PWA (manifest + icons)
- offline-friendly navigation (cached shell)
- graceful degraded mode when API is unreachable
- (stretch) persist recent Q&A + citations in local storage so the UI remains useful offline

## Requirements

### PWA fundamentals

- Add a `manifest.webmanifest` with:
  - app name/short name
  - icons (192/512 + maskable)
  - theme/background colors matching current design
  - start_url `/`
  - display `standalone`

- Service worker:
  - Cache the app shell (HTML + JS + CSS + assets)
  - Use a safe caching strategy:
    - `stale-while-revalidate` for static assets
    - `network-first` for API calls (do **not** cache `/api/query` responses by default)

- Local dev:
  - PWA should work in `make web-dev` (dev mode may have limited SW support)

### Offline UX

- Add a non-intrusive offline banner (e.g. “Offline mode”) when:
  - `navigator.onLine === false` OR
  - API calls fail with network errors

- In offline mode:
  - Docs list/search show an explicit “offline” state
  - Ask page:
    - disable “Ask” submit
    - offer to view recent saved answers (if implemented)

### Local persistence (stretch)

- Persist the last ~20 Q&A sessions (question + answer + citations + timestamp) in local storage.
- Provide a small “History” drawer on the Ask page.
- Ensure PII / secrets are not persisted unintentionally:
  - do **not** persist API keys
  - keep storage scoped to the browser only

## Non-goals

- Full offline ingestion (uploading files) — not required.
- Caching `/api/query` results by default.

## Implementation notes

- Use Vite PWA plugin (or manual manifest + SW). Keep dependency footprint minimal.
- Keep safety invariants:
  - Public demo mode must remain safe and read-only.
  - Do not cache sensitive endpoints.

## Validation

- `make web-build`
- Manual test:
  - load site once
  - go offline
  - refresh: shell should still load
  - navigate between pages
  - confirm API-backed pages show offline messaging

## Docs

- Update `docs/TUTORIAL.md` with:
  - how to install PWA locally
  - offline limitations
