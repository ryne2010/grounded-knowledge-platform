# AGENTS.md

## Start here (agents)

1.  Read `harness.toml` to learn **how to validate changes** in this
    repo.
2.  Read the durable source of truth:
    -   `docs/PRODUCT/PRODUCT_BRIEF.md` (product intent + constraints)
    -   `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md` (non-negotiables)
    -   `docs/ARCHITECTURE/README.md` (C4 diagrams + models)
    -   `docs/DOMAIN.md` (what we're building and why)
    -   `docs/DESIGN.md` (architecture and dependency rules)
    -   `docs/CONTRACTS.md` (interfaces, invariants, compatibility)
3.  Follow `docs/WORKFLOW.md` for the standard execution loop.
4.  Use `agents/tasks/` to choose a task template (feature, bugfix,
    refactor, docs).
    - Optional: use `agents/subagents/` prompts to focus an agent on a specific workstream
      (frontend UX, Postgres hardening, GCS connector, etc.).
5.  Validate before you finalize:
    -   `python scripts/harness.py lint`
    -   `python scripts/harness.py test`
    -   `python scripts/harness.py typecheck` (if configured)

## Non-negotiables

-   **Repo-first:** do not invent architecture or rules that aren't
    encoded in the repo.
-   **Respect boundaries:** follow layering and allowed dependencies in
    `docs/DESIGN.md`.
-   **Protect contracts:** don't break interfaces or invariants in
    `docs/CONTRACTS.md` without an explicit ADR.
-   **Small diffs:** prefer small, cohesive changes that are easy to
    review.
-   **Always validate:** run the harness tasks relevant to your change.

## Escalate to a human when

-   Intent is ambiguous or requirements conflict.
-   A change requires a significant tradeoff that can't be validated
    mechanically.
-   You need to alter an invariant, boundary, or public contract.
-   The harness cannot be made green without skipping critical checks.

## Output format (final response)

Use `agents/checklists/CHANGE_SUMMARY.md` to produce: - what changed -
why it changed - how it was validated - risks/rollout notes - follow-ups
/ debt introduced
