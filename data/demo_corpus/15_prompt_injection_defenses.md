# Prompt Injection Defenses

## Threat
Retrieved documents are untrusted input and may contain instructions intended to override system behavior.

## Defenses
- Treat retrieved text as evidence, not instructions.
- Require citations for answers.
- Add refusal behavior when:
  - prompt injection is detected
  - evidence is insufficient
- Maintain regression tests (prompt injection suite) and run in CI.

## Demo posture
Public demo refuses a wider set of suspicious prompts (conservative).
