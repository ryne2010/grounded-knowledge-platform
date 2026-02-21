# Backlog

This folder is the “planning front door” for the repo:

- what we’re building (epics)
- how work is sliced (tasks)
- how to execute in an agent-driven workflow

This backlog is derived from the project narrative in:
- resumes (GCP engineer + data architect)
- case studies (Grounded Knowledge Platform, EventPulse, EdgeWatch)
- job applications (cloud/platform + data architecture responsibilities)

See:
- Epics: `docs/BACKLOG/EPICS.md`
- Milestones (recommended order): `docs/BACKLOG/MILESTONES.md`
- Execution queue (numbered steps): `docs/BACKLOG/QUEUE.md`
- Dependencies: `docs/BACKLOG/DEPENDENCIES.md`
- Task index: `docs/BACKLOG/TASK_INDEX.md`
- Codex execution playbook: `docs/BACKLOG/CODEX_PLAYBOOK.md`

## How to work this backlog

1) Start from an epic in `EPICS.md`.
2) Confirm sequencing in `MILESTONES.md` (or the more execution-oriented `QUEUE.md`).
3) Ensure there is a spec (either in `docs/SPECS/` or an architecture/product doc).
4) Pick a single task from `agents/tasks/` and implement it as a small diff.
5) Keep the harness green (`python scripts/harness.py lint/test/typecheck`).

## Backlog maintenance

If you add/remove task files, or update milestone sequencing, regenerate the derived docs:

```bash
make backlog-refresh
```

Or run individually:

```bash
make task-index
make queue
```

To sanity-check that the planning artifacts remain consistent and tasks are "codex-ready":

```bash
make backlog-audit
```

## Agent execution helpers

### Prompt packs for @codex

To generate a single markdown “prompt pack” that includes the task, referenced specs, and the repo non-negotiables:

```bash
make codex-prompt TASK=agents/tasks/TASK_UI_UX_POLISH.md
```

Output is written to `dist/codex_prompts/` (gitignored).

### Optional: export backlog to GitHub Issues

If you want to work the backlog in GitHub Issues/Projects (instead of markdown files), generate GitHub-issue-friendly
artifacts:

```bash
make backlog-export
```

Output is written to `dist/github_issues/` (gitignored).

## Safety constraints

- Public demo remains safe-by-default: read-only, extractive-only, demo corpus only.
- Private deployments can be richer, but must explicitly enable privileged features behind auth.
