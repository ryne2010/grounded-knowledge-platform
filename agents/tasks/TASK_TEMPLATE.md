# Task template

> Copy this file to create a new repeatable agent task.

Spec (optional): `docs/SPECS/<SPEC_NAME>.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/<subagent>.md`

## Goal

TODO: What outcome should be achieved?

## Context

TODO: Why are we doing this now? What user/problem does it solve?

## Scope

In scope:

- TODO

Out of scope (explicit non-goals):

- TODO

## Requirements

### Product / UX

- TODO

### API / contracts

- TODO

### Data model / migrations

- TODO

### Security / safety

- TODO

### Observability

- TODO

## Implementation plan

1. TODO
2. TODO
3. TODO

## Acceptance criteria

- TODO
- TODO

## Rollout / ops notes

- TODO (feature flag? demo-mode gating? backwards compatibility?)

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py test`
- `python scripts/harness.py typecheck`
- plus any task-specific commands

## Deliverables

- Code changes: TODO
- Tests: TODO
- Docs updates: TODO
- Change summary: `agents/checklists/CHANGE_SUMMARY.md`

## Escalation

Escalate when:

- intent ambiguity affects architecture/contracts
- validation can't be made green without skipping critical checks
- a public contract or invariant must change (requires ADR)

