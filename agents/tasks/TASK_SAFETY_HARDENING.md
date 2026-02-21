# Task: Safety hardening (prompt injection + exfiltration)

Related:
- `docs/ARCHITECTURE/SECURITY_MODEL.md`
- `docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/security_governance.md`

## Goal

Improve safety posture for both public demo and private deployments:

- robust prompt injection handling
- no evidence → refuse consistently
- reduce risk of “citation-based exfiltration” when chunk view is enabled

## Requirements

- Expand prompt-injection detection test suite:
  - obvious injection strings
  - subtle instruction hijacks
  - “system prompt reveal” attempts

- Harden refusal heuristics:
  - refusal when citations are weak
  - refusal reason categories: `insufficient_evidence|safety_block|internal_error`

- UI messaging:
  - refusal is clear and non-alarming
  - demo mode clearly explains limitations (extractive-only)

## Acceptance criteria

- Safety eval suite catches regressions.
- No new UI path reveals full chunk text in public demo mode.

## Validation

- `python scripts/harness.py test`
- `python scripts/harness.py lint`
