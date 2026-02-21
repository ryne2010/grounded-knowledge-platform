# Task: Streaming answers (SSE) with incremental citations

Spec: `docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md`
Suggested sub-agent: `agents/subagents/backend_fastapi_platform.md`

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

## Acceptance criteria

- The streaming endpoint produces well-formed SSE frames and completes with `done`.
- Citations-required behavior is preserved in streaming mode.
- The UI can cancel a streaming request without leaving the page in a broken state.

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
