# Codex execution playbook

This repo is designed for **agent-driven delivery**.

This playbook defines how to execute the tasks in `agents/tasks/` using a coding agent (e.g., `@codex`) while preserving
repo contracts and keeping diffs reviewable.

## Inputs

Before starting any task:

1. Read `AGENTS.md`
2. Confirm the non-negotiables:
   - `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
3. Confirm product intent:
   - `docs/PRODUCT/PRODUCT_BRIEF.md`
   - `docs/PRODUCT/FEATURE_MATRIX.md`
4. Confirm architecture boundaries:
   - `docs/ARCHITECTURE/README.md`
   - `docs/DESIGN.md`
   - `docs/CONTRACTS.md`

Optional (recommended for maintainers):

- `make backlog-audit`

## Picking a task

- Start from `docs/BACKLOG/MILESTONES.md` (recommended ordering).
- If you prefer a numbered checklist, use `docs/BACKLOG/QUEUE.md`.
- Use `docs/BACKLOG/TASK_INDEX.md` to find the task file.
- Each task should ideally have:
  - a spec in `docs/SPECS/` (or a product/architecture doc acting as the spec)
  - explicit acceptance criteria
  - explicit validation commands

If a task is missing a spec, create a spec first (small doc) and link it from the task.

## Suggested execution pattern (per task)

1. Create a branch:

   - `task/<short-name>`

2. Run a baseline check locally:

   - `make dev-doctor`

3. Use a focused sub-agent prompt (optional):

   - `agents/subagents/frontend_ux.md`
   - `agents/subagents/postgres_hardening.md`
   - `agents/subagents/infra_terraform_gcp.md`
   - etc.

3b. (Optional) Generate a single “prompt pack” file for @codex:

   - `make codex-prompt TASK=agents/tasks/<TASK_FILE>.md`

4. Implement in the smallest coherent slice:

   - prefer one vertical slice that can be validated end-to-end
   - avoid large refactors mixed with feature work

5. Validate:

   - `python scripts/harness.py lint`
   - `python scripts/harness.py test`
   - `python scripts/harness.py typecheck`
   - plus any task-specific commands (`make test-postgres`, etc.)

6. Update docs if you changed a contract or behavior.

7. Produce a change summary:

   - use `agents/checklists/CHANGE_SUMMARY.md`

## Guardrails (do not violate)

- **Public demo mode stays safe**:
  - no uploads
  - no connectors
  - no eval endpoints
  - extractive-only
  - demo corpus only

- Avoid broad changes that are hard to review:
  - prefer small diffs and frequent PRs

- If you must change a public contract or invariant:
  - write an ADR first (see `docs/DECISIONS/ADR_TEMPLATE.md`)

## When to split tasks

Split tasks when:

- UI work requires backend contract changes (split into backend + UI tasks)
- a task touches multiple architectural layers
- you cannot validate in one harness run

## Review checklist

Before merging:

- Does this change preserve `docs/DESIGN.md` boundaries?
- Did it break demo mode constraints?
- Did it add tests for any new logic?
- Is observability adequate for new critical paths?

