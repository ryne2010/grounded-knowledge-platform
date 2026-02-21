# Task: “Explain this answer” drawer (retrieval transparency)

Spec: `docs/SPECS/UI_UX_PRODUCTION_POLISH.md`  
Related: `docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/frontend_ux.md`

## Goal

Add an “Explain this answer” drawer that makes retrieval transparent:

- shows which docs/chunks were retrieved
- shows lexical vs vector signals (high level)
- explains why a refusal happened

This should feel like a production SaaS admin: helpful, non-overwhelming, and safe.

## Requirements

### Public demo mode

- show retrieval *summary* (doc titles + snippets + “why these were chosen”)
- do NOT expose full chunk text unless `ALLOW_CHUNK_VIEW=1` (off in demo)
- do not show raw embeddings or internal prompts

### Private deployments

- allow more detail when enabled:
  - include chunk IDs and scores
  - optionally include “retrieval debug” payload behind `ALLOW_DEBUG=1` or similar

### API

- Option A (preferred): extend `/api/query` response with an `explain` object
- Option B: add `/api/query/explain` that takes a query + answer_id

The API should be stable enough to support UI without fragile coupling.

### UX

- The drawer is available after an answer is returned (or refusal).
- Clear sections:
  - “Evidence used”
  - “How retrieval works”
  - “Why the system refused” (when applicable)

## Acceptance criteria

- A user can tell, in < 30 seconds, **why** a particular doc was used.
- A refusal includes a clear reason (insufficient evidence vs blocked by safety).
- No private-only fields leak in public demo.

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py test`
- `make web-typecheck`
