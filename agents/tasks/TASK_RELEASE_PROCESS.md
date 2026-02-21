# Task: Release process (versioning + changelog discipline)

Spec: `docs/SPECS/OBSERVABILITY_OPS.md`

Owner: @codex  
Suggested sub-agent: `agents/subagents/product_planner.md`

## Goal

Make the repo feel like a production service with repeatable releases:

- semantic versioning or date-based versioning
- changelog entries per release
- optional GitHub Actions release workflow

## Requirements

- Define version strategy:
  - how `app/version.py` is updated
  - how `CHANGELOG.md` entries are added

- Add Make targets:
  - `make release-bump` (optional)
  - `make release-notes` (optional)

- Docs:
  - `docs/RELEASES.md` (new)

## Acceptance criteria

- A contributor can cut a release with a documented sequence.
- Release notes are consistent and discoverable.

## Validation

- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
- `make backlog-refresh`

