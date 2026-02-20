# Task: Streaming answers (SSE) with incremental citations

Owner: @codex

## Goal

Improve UX for long answers by streaming tokens and showing citations as soon as they are available.

## Requirements

### API

- Add `POST /api/query/stream`
  - Server-Sent Events (SSE)
  - Events:
    - `retrieval` (optional debug payload)
    - `token` (partial answer)
    - `citations` (final citations)
    - `done`
    - `error`

### Providers

- Extractive provider can stream sentence-by-sentence
- OpenAI / Gemini providers:
  - use their native streaming SDKs
  - ensure citations are still computed and emitted

### Safety

- keep prompt injection detection as pre-check
- if the system refuses, stream a refusal message and `done`

### UI

- Home page:
  - switch between “streaming” and “non-streaming” query modes
  - render tokens incrementally
  - render citations when received
  - allow cancel

## Tests

- unit tests for SSE framing
- regression test: citations-required behavior still enforced

## Docs

- update `docs/CONTRACTS.md` with event schema
- add a short tutorial section in `docs/TUTORIAL.md`
