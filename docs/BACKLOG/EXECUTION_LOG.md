# Backlog Execution Log

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-ui-ux-polish`
- Current task: `TASK_UI_UX_POLISH` (`agents/tasks/TASK_UI_UX_POLISH.md`)

## Task summary

Implemented Task #1 UI/UX polish slice with focus on:

- shared app shell usability on mobile + keyboard (dialog-based nav)
- explicit public demo guardrails in global navigation/status surfaces
- Ask flow streaming stability and citation utility actions (`Copy quote` + toast feedback)
- consistent page-level headers across docs/search/ingest/doc-detail views

## Decisions made

- Start from queue item #1 in `docs/BACKLOG/QUEUE.md`.
- Preserve ADR constraints for public demo safety defaults (read-only, extractive-only posture, no privileged actions).
- Keep private-only capabilities visible in nav when disabled, with explicit reason text.
- Apply minimal repository-wide lint/type fixes only where needed to make required validation gates pass.

## Files changed

- `web/src/portfolio-ui/components/AppShell.tsx`
- `web/src/router.tsx`
- `web/src/pages/Home.tsx`
- `web/src/pages/Docs.tsx`
- `web/src/pages/Search.tsx`
- `web/src/pages/Ingest.tsx`
- `web/src/pages/DocDetail.tsx`
- `app/connectors/gcs.py`
- `app/ingestion.py`
- `app/retrieval.py`
- `app/storage.py`
- `app/storage_repo/postgres_adapter.py`
- `scripts/backlog_audit.py`
- `scripts/export_github_issues.py`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Discovery/grounding:
   - `pwd; ls -la`
   - `ls -la docs/BACKLOG; ls -la docs/DECISIONS; ls -la agents/tasks`
   - `sed -n ... AGENTS.md`
   - `sed -n ... harness.toml`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... docs/PRODUCT/PRODUCT_BRIEF.md`
   - `sed -n ... docs/ARCHITECTURE/README.md`
   - `sed -n ... docs/DOMAIN.md`
   - `sed -n ... docs/DESIGN.md`
   - `sed -n ... docs/CONTRACTS.md`
   - `sed -n ... docs/WORKFLOW.md`
   - `sed -n ... agents/tasks/TASK_UI_UX_POLISH.md`
   - `sed -n ... docs/SPECS/UI_UX_PRODUCTION_POLISH.md`
2. Branching:
   - `git checkout -b codex/task-ui-ux-polish`
3. Validation/install:
   - `make web-typecheck` (failed initially: missing web deps)
   - `make web-install`
   - `make web-typecheck`
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`
   - `make web-typecheck`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`29 passed, 3 skipped`)
- `make backlog-audit`: PASS (`OK`)
- `make web-typecheck`: PASS

## Follow-up notes

- Initial validation failures were pre-existing lint/type issues outside UI scope; fixed minimally to unblock required harness checks.
- Remaining queue tasks proceed from `docs/BACKLOG/QUEUE.md` item #2 after this branch is committed and opened as PR.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-doc-viewer-citations`
- Current task: `TASK_DOC_VIEWER_CITATIONS` (`agents/tasks/TASK_DOC_VIEWER_CITATIONS.md`)

## Task summary

Implemented Task #2 citation UX polish:

- citation deep links from Ask view now carry doc context (`chunk_id`, quote, title/source, score)
- Doc Detail now detects citation navigation and renders a dedicated “Citations in this doc” section
- cited snippets are highlighted in chunk preview context when chunk view is enabled
- jump behavior now auto-scrolls/focuses cited content (or citation summary card when chunk view is gated)
- copy-citation UX standardized to include quote + title + `doc_id`
- added web UI test coverage for citation click navigation + scroll/focus highlight behavior

## Decisions made

- Keep public demo safe-by-default: only show citation snippets in URL/summary; no full chunk exposure unless chunk view is enabled.
- Use URL search params for citation jump state (no new backend surface area).
- Add a lightweight web test stack (`vitest` + `jsdom`) and wire it into harness `test` so citation UX checks run in CI.

## Files changed

- `web/src/lib/citations.ts`
- `web/src/lib/citations.test.ts`
- `web/src/pages/Home.tsx`
- `web/src/pages/DocDetail.tsx`
- `web/vitest.config.ts`
- `web/package.json`
- `web/pnpm-lock.yaml`
- `harness.toml`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Discovery/grounding:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... agents/tasks/TASK_DOC_VIEWER_CITATIONS.md`
   - `sed -n ... docs/SPECS/UI_UX_PRODUCTION_POLISH.md`
2. Implementation:
   - file edits for citation helper, Ask citations, Doc Detail citation jump/highlight, and web tests
   - `cd web && corepack pnpm install`
3. Validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`
   - `make web-typecheck`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`29 passed, 3 skipped` in Python; `1 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make web-typecheck`: PASS

## What’s next

- Commit `TASK_DOC_VIEWER_CITATIONS` on this branch and open PR.
- Move to queue item #3: `TASK_QUERY_EXPLAIN_DRAWER`.
