# WORKFLOW.md

This document standardizes how humans and agents execute work in this
repo.

## The standard loop

1.  **Clarify intent**
    -   restate goal
    -   list constraints and non-goals
2.  **Plan**
    -   small steps
    -   explicit acceptance criteria
    -   validation strategy
3.  **Implement**
    -   smallest coherent diff first
    -   keep boundaries intact
4.  **Validate**
    -   run `python scripts/harness.py lint`
    -   run `python scripts/harness.py test`
    -   run `python scripts/harness.py typecheck` (if configured)

Optional (for sharing / releasing):

-   `make dist` to generate a clean source ZIP in `dist/` (excludes caches and secrets).
-   `make clean` to remove local caches/build artifacts.
5.  **Review**
    -   self-review using `agents/checklists/PR_REVIEW.md`
    -   optional reviewer agent pass for invariants/boundaries
6.  **Summarize**
    -   use `agents/checklists/CHANGE_SUMMARY.md`

## Autonomy gradient

Choose the right level of autonomy:

-   **Low risk** (docs, comments, minor refactors):
    -   proceed with minimal coordination
-   **Medium risk** (bugfixes, local features):
    -   follow the full loop; add targeted tests
-   **High risk** (architecture, contracts, security, data migrations):
    -   require ADR + human review; prefer design-first

## Definition of done

A change is "done" when: - intent is satisfied - invariants and
boundaries remain intact - relevant tests pass - change is documented if
it affects contracts/behavior - a clear change summary exists

## Escalation

Escalate to a human when: - intent ambiguity affects architecture or
contracts - tradeoffs cannot be validated mechanically -
security/privacy concerns exist - invariants must change

## Artifacts to update

Update these when relevant: - `docs/DOMAIN.md` for domain rules and
vocabulary - `docs/DESIGN.md` for boundaries/layering -
`docs/CONTRACTS.md` for interface guarantees - `docs/DECISIONS/` for
significant decisions - `docs/RUNBOOKS/` when operational behavior
changes
