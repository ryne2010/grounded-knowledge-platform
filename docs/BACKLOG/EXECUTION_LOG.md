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

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-query-explain-drawer`
- Current task: `TASK_QUERY_EXPLAIN_DRAWER` (`agents/tasks/TASK_QUERY_EXPLAIN_DRAWER.md`)

## Task summary

Implemented Task #3 retrieval transparency via an “Explain this answer” drawer and stable API payloads:

- backend `/api/query` now returns an `explain` object for answered and refused responses
- backend `/api/query/stream` now includes the same `explain` payload in `done` events
- `explain` includes:
  - `evidence_used`
  - `how_retrieval_works`
  - `refusal` (categorized, human-readable reason)
- public demo mode keeps explanation safe-by-default (no chunk IDs/scores in explanation evidence)
- private mode with debug enabled includes richer evidence detail (chunk IDs + scores)
- Ask page now has an “Explain this answer” drawer with:
  - “Evidence used”
  - “How retrieval works”
  - “Why the system refused”

## Decisions made

- Chose **Option A** from task requirements: extend `/api/query` contract with stable `explain` payload.
- Mirrored `explain` into streaming `done` events so default streaming UX still supports explainability.
- Kept explanation evidence snippet-first in public demo; private-only numeric/internal detail remains gated.
- Replaced the old retrieval-debug modal in Ask flow with the dedicated explain drawer to avoid parallel UX paths.

## Files changed

- `app/main.py`
- `web/src/api.ts`
- `web/src/pages/Home.tsx`
- `tests/test_query_explain.py`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git checkout main && git pull --ff-only`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_QUERY_EXPLAIN_DRAWER.md`
   - `sed -n ... docs/SPECS/UI_UX_PRODUCTION_POLISH.md`
2. Branching:
   - `git checkout -b codex/task-query-explain-drawer`
3. Targeted validation during implementation:
   - `cd web && corepack pnpm run typecheck`
   - `uv run pytest -q tests/test_query_explain.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`32 passed, 3 skipped` in Python; `1 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## What’s next

- Commit `TASK_QUERY_EXPLAIN_DRAWER` on this branch and open PR.
- Move to queue item #4: `TASK_DEMO_GUIDED_TOUR`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-demo-guided-tour`
- Current task: `TASK_DEMO_GUIDED_TOUR` (`agents/tasks/TASK_DEMO_GUIDED_TOUR.md`)

## Task summary

Implemented Task #4 onboarding improvements for public demo mode:

- added curated **Suggested demo queries** panel (single config source, one-click run)
- clicking suggested queries now both populates the input and executes the query
- added user-triggered **guided tour** with 5 required steps:
  1. demo mode badge
  2. query input
  3. citations area
  4. doc/source viewer
  5. refusal behavior
- tour is keyboard accessible via dialog semantics and focus management:
  - focus trap + ESC close (Radix dialog)
  - reachable next/previous controls
  - step target scroll/focus + visual highlight
- added small docs note in product demo script about using the built-in tour

## Decisions made

- Stored curated queries and guided tour step copy in a single config module (`web/src/config/demoOnboarding.ts`) to make updates low-friction.
- Kept implementation dependency-light by using existing Radix dialog + existing UI primitives (no new tour library).
- Applied tour targeting via `data-tour-target` attributes and runtime focus/highlight behavior instead of adding a heavy overlay engine.
- Preserved demo safety constraints: onboarding copy explicitly explains read-only/demo-corpus limits and disabled privileged controls.

## Files changed

- `web/src/config/demoOnboarding.ts`
- `web/src/config/demoOnboarding.test.ts`
- `web/src/pages/Home.tsx`
- `web/src/router.tsx`
- `docs/PRODUCT/DEMO_SCRIPT.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git checkout main && git pull --ff-only`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_DEMO_GUIDED_TOUR.md`
   - `sed -n ... docs/SPECS/UI_UX_PRODUCTION_POLISH.md`
2. Branching:
   - `git checkout -b codex/task-demo-guided-tour`
3. Targeted validation:
   - `cd web && corepack pnpm run typecheck`
   - `cd web && corepack pnpm run test`
4. Full required validation:
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
- `python scripts/harness.py test`: PASS (`32 passed, 3 skipped` in Python; `3 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make web-typecheck`: PASS

## What’s next

- Commit `TASK_DEMO_GUIDED_TOUR` on this branch and open PR.
- Move to queue item #5: `TASK_ACCESSIBILITY_AUDIT`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-accessibility-audit`
- Current task: `TASK_ACCESSIBILITY_AUDIT` (`agents/tasks/TASK_ACCESSIBILITY_AUDIT.md`)

## Task summary

Completed the accessibility baseline audit/fix pass for core flows:

- Ask flow: improved keyboard and focus affordances for key links and error announcements
- Docs list + Doc detail: added missing explicit labels for filters and alert semantics for surfaced errors
- App shell/demo banners: added skip link, focus-visible link styles, and polite live-region status semantics
- Dialogs: added a keyboard-reachable close control in dialog content while preserving focus trap + ESC behavior
- Updated in-repo checklist with tested flows, fixes, and residual risks

## Decisions made

- Kept changes dependency-light (no new a11y lint plugin) and focused on high-impact keyboard/focus/labeling gaps.
- Implemented a shared dialog close affordance at the `DialogContent` primitive level to eliminate modal escape ambiguity.
- Prioritized explicit labels and announcement roles for user-visible form/error/status surfaces in scope.

## Files changed

- `web/src/portfolio-ui/ui/dialog.tsx`
- `web/src/portfolio-ui/components/AppShell.tsx`
- `web/src/pages/Home.tsx`
- `web/src/pages/Docs.tsx`
- `web/src/pages/DocDetail.tsx`
- `docs/QUALITY/A11Y_CHECKLIST.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git checkout main && git pull --ff-only`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_ACCESSIBILITY_AUDIT.md`
   - `sed -n ... docs/SPECS/UI_UX_PRODUCTION_POLISH.md`
2. Branching:
   - `git checkout -b codex/task-accessibility-audit`
3. Full required validation:
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
- `python scripts/harness.py test`: PASS (`32 passed, 3 skipped` in Python; `3 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make web-typecheck`: PASS

## What’s next

- Commit `TASK_ACCESSIBILITY_AUDIT` on this branch and open PR.
- Move to queue item #6: `TASK_AUTH`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-auth-queue`
- Current task: `TASK_AUTH` (`agents/tasks/TASK_AUTH.md`)

## Task summary

Completed Task #6 auth/authz hardening pass by closing remaining operational gaps in the existing implementation:

- added structured `auth.denied` logging events for authorization/authentication denials with stable fields (`event`, `reason`, `path`, `request_id`, `status`, `auth_mode`)
- ensured auth mode resolution stays correct across config reloads by reading `config.settings` dynamically in auth mode checks
- added/expanded auth tests to verify structured denial logging for both:
  - missing API key (`401`)
  - insufficient role (`403`)
- stabilized test isolation around environment variables so auth-mode test state does not leak between modules

## Decisions made

- Keep existing auth contract and endpoint role gates intact (already aligned with task acceptance criteria).
- Add structured denial telemetry as the smallest coherent enhancement to satisfy the spec observability guidance without changing API behavior.
- Fix test isolation at test-helper level (env restore fixtures + explicit auth defaults) to keep harness deterministic.

## Files changed

- `app/auth.py`
- `app/main.py`
- `tests/test_auth.py`
- `tests/test_demo_mode_invariants.py`
- `tests/test_doc_update_api.py`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_AUTH.md`
   - `sed -n ... docs/SPECS/AUTH_PRIVATE_DEPLOYMENTS.md`
2. Discovery:
   - `rg -n "AUTH_MODE|API_KEYS_JSON|..."`
   - `sed -n ... app/auth.py`
   - `sed -n ... app/main.py`
   - `sed -n ... tests/test_auth.py`
3. Targeted validation while implementing:
   - `uv run pytest -q tests/test_auth.py` (iterative runs)
   - `uv run pytest -q tests/test_auth.py tests/test_demo_mode_invariants.py tests/test_doc_update_api.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`34 passed, 3 skipped` in Python; `3 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## What’s next

- Commit `TASK_AUTH` on this branch and open PR.
- Move to queue item #7: `TASK_CONNECTORS_GCS_UI`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-connectors-gcs-ui`
- Current task: `TASK_CONNECTORS_GCS_UI` (`agents/tasks/TASK_CONNECTORS_GCS_UI.md`)

## Task summary

Implemented the private-deployment GCS connector UX in the Ingest workspace:

- added a dedicated **GCS connector sync** card with inputs for:
  - bucket (required)
  - prefix
  - max_objects (bounded 1-5000)
  - dry_run toggle
  - classification / retention / tags / notes
- added safe gating behavior:
  - explicit disabled explanation in `PUBLIC_DEMO_MODE`
  - explicit disabled explanation when `ALLOW_CONNECTORS=0`
  - action remains backend-admin-gated; UI notes admin requirement when auth is enabled
- integrated API call to `POST /api/connectors/gcs/sync`
- added result rendering:
  - run metadata (run_id, start/end, target)
  - summary badges (scanned, ingested, changed, unchanged, would_ingest, skipped)
  - actionable errors list (if returned)
  - per-object results table with doc deep links when available
- persisted latest run in UI state and added **Copy JSON** + **Export JSON** actions

## Decisions made

- Keep changes frontend-only (no backend contract changes) because the sync endpoint and auth gates already existed.
- Add a small pure helper module for connector availability + run summaries to keep Ingest page readable and testable.
- Treat backend as source of truth for admin enforcement; UI communicates requirement and surfaces 401/403 errors clearly.

## Files changed

- `web/src/api.ts`
- `web/src/pages/Ingest.tsx`
- `web/src/lib/gcsConnector.ts`
- `web/src/lib/gcsConnector.test.ts`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_CONNECTORS_GCS_UI.md`
   - `sed -n ... docs/SPECS/CONNECTOR_GCS_INGESTION.md`
2. Branching:
   - `git checkout main`
   - `git pull --ff-only`
   - `git checkout -b codex/task-connectors-gcs-ui`
3. Discovery:
   - `rg -n "connectors|gcs sync|/api/connectors/gcs/sync|..."`
   - `sed -n ... web/src/pages/Ingest.tsx`
   - `sed -n ... web/src/api.ts`
   - `sed -n ... app/connectors/gcs.py`
4. Targeted validation:
   - `cd web && corepack pnpm run test`
   - `cd web && corepack pnpm run typecheck`
5. Full required validation:
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
- `python scripts/harness.py test`: PASS (`34 passed, 3 skipped` in Python; `7 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make web-typecheck`: PASS

## What’s next

- Commit `TASK_CONNECTORS_GCS_UI` on this branch and open PR.
- Move to queue item #8: `TASK_INGESTION_RUNS`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-ingestion-runs`
- Current task: `TASK_INGESTION_RUNS` (`agents/tasks/TASK_INGESTION_RUNS.md`)

## Task summary

Implemented the backend ingestion-runs capability for connector operations:

- added persistent `ingestion_runs` storage with lifecycle/status + summaries
- added `run_id` linkage on `ingest_events` so a run can be tied to its emitted lineage events
- added API endpoints:
  - `GET /api/ingestion-runs`
  - `GET /api/ingestion-runs/{run_id}`
- wired GCS sync endpoint to:
  - create a run record as `running`
  - propagate `run_id` into ingested events
  - complete run as `succeeded` with summary counters
  - mark run `failed` with retained actionable errors on failures
- added tests covering:
  - successful sync creates run summary + detail/event linkage
  - failed sync persists failed run with error context
  - rerunning same sync remains idempotent at doc level (no duplicate docs)

## Decisions made

- Used the task-allowed simpler linkage strategy: add `run_id` to `ingest_events` instead of introducing a separate `ingestion_run_events` table.
- Kept run creation/update in the API layer for connector-triggered runs (explicitly satisfies acceptance without introducing wider ingestion orchestration changes).
- Added Postgres migration (`003_ingestion_runs.sql`) and SQLite additive migration path in `init_db` for parity.

## Files changed

- `app/storage.py`
- `app/ingestion.py`
- `app/connectors/gcs.py`
- `app/main.py`
- `app/migrations/postgres/003_ingestion_runs.sql`
- `tests/test_ingestion_runs.py`
- `tests/test_storage_migrations.py`
- `docs/CONTRACTS.md`
- `docs/ARCHITECTURE/DATA_MODEL.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_INGESTION_RUNS.md`
   - `sed -n ... docs/ARCHITECTURE/INGESTION_PIPELINE.md`
2. Branching:
   - `git checkout main`
   - `git pull --ff-only`
   - `git checkout -b codex/task-ingestion-runs`
3. Targeted validation during implementation:
   - `uv run pytest -q tests/test_ingestion_runs.py tests/test_storage_migrations.py`
   - `python scripts/harness.py typecheck`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`
   - `make test-postgres`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`37 passed, 3 skipped` in Python; `7 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make test-postgres`: PASS (`1 skipped` when Docker unavailable)

## What’s next

- Commit `TASK_INGESTION_RUNS` on this branch and open PR.
- Move to queue item #9: `TASK_INGESTION_RUNS_UI`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-ingestion-runs-ui`
- Current task: `TASK_INGESTION_RUNS_UI` (`agents/tasks/TASK_INGESTION_RUNS_UI.md`)

## Task summary

Implemented the ingestion-runs operator UI in the Ingest workspace:

- added run history list + detail panel on `/ingest`
- added list filters for status, trigger type, and started-on/after date
- added detail summary tiles (changed, unchanged, errors) and expandable error details
- added linked ingest-events table per selected run (metadata only; no raw content rendering)
- added a disabled `Rerun (coming soon)` affordance with explicit admin/safety labeling
- enforced demo-safe UX path: public demo now shows a clear empty-state message for ingestion runs and no run actions

## Decisions made

- Keep this task frontend-only and consume existing Task #8 APIs (`/api/ingestion-runs`, `/api/ingestion-runs/{run_id}`).
- Gate runs-query fetch + rendering in public demo mode to preserve safe-by-default posture.
- Introduce small pure helper utilities (`web/src/lib/ingestionRuns.ts`) for filtering, badge mapping, and bounded error summaries to keep page logic testable.

## Files changed

- `web/src/api.ts`
- `web/src/pages/Ingest.tsx`
- `web/src/lib/ingestionRuns.ts`
- `web/src/lib/ingestionRuns.test.ts`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_INGESTION_RUNS_UI.md`
2. Branch/context checks:
   - `git status --short`
   - `git branch --show-current`
3. Discovery:
   - `sed -n ... web/src/pages/Ingest.tsx`
   - `sed -n ... web/src/api.ts`
   - `sed -n ... app/main.py`
   - `rg -n ... app tests`
4. Targeted validation:
   - `cd web && corepack pnpm run test -- --run src/lib/ingestionRuns.test.ts`
   - `cd web && corepack pnpm run typecheck`
5. Full required validation:
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
- `python scripts/harness.py test`: PASS (`37 passed, 3 skipped` in Python; `12 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make web-typecheck`: PASS

## What’s next

- Commit `TASK_INGESTION_RUNS_UI` on this branch and open PR.
- Move to queue item #10: `TASK_REPLAY_BACKFILL`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-replay-backfill`
- Current task: `TASK_REPLAY_BACKFILL` (`agents/tasks/TASK_REPLAY_BACKFILL.md`)

## Task summary

Implemented safe replay/backfill tooling for private deployments:

- added CLI commands:
  - `uv run python -m app.cli replay-doc --doc-id <id> [--force]`
  - `uv run python -m app.cli replay-run --run-id <id> [--force]`
- added replay behavior:
  - default skip-if-unchanged when a content hash exists
  - `--force` path re-chunks/re-embeds even when unchanged
- added ingestion-run tracking for CLI replay operations (`trigger_type=cli`)
- added a storage helper to enumerate run-linked doc ids for run replay
- added runbook: `docs/RUNBOOKS/REPLAY_BACKFILL.md`
- added tests covering:
  - replay-run idempotency (no duplicate docs/chunks when not forced)
  - replay-doc `--force` reprocessing behavior on unchanged content
  - replay command blocking in public demo mode + no replay API exposure

## Decisions made

- Keep replay/backfill implementation CLI-only for this task; do not add replay API endpoints.
- Preserve public demo safety posture by hard-blocking replay commands in `PUBLIC_DEMO_MODE`.
- Reuse existing ingestion pipeline for forced replay (`ingest_text`) and keep skip logic explicit in replay path.

## Files changed

- `app/cli.py`
- `app/ingestion.py`
- `app/storage.py`
- `tests/test_replay_backfill.py`
- `docs/RUNBOOKS/REPLAY_BACKFILL.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_REPLAY_BACKFILL.md`
   - `sed -n ... docs/ARCHITECTURE/INGESTION_PIPELINE.md`
   - `sed -n ... docs/ARCHITECTURE/DATA_MODEL.md`
2. Branching:
   - `git checkout main`
   - `git pull --ff-only`
   - `git checkout -b codex/task-replay-backfill`
3. Targeted checks while implementing:
   - `uv run ruff check app/cli.py app/ingestion.py app/storage.py tests/test_replay_backfill.py`
   - `uv run mypy app`
   - `uv run pytest -q tests/test_replay_backfill.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`
   - `make test-postgres`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`40 passed, 3 skipped` in Python; `12 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make test-postgres`: PASS (`1 skipped` when Docker/Postgres unavailable)

## What’s next

- Commit `TASK_REPLAY_BACKFILL` on this branch and open PR.
- Move to queue item #11: `TASK_DATA_CONTRACTS`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-data-contracts`
- Current task: `TASK_DATA_CONTRACTS` (`agents/tasks/TASK_DATA_CONTRACTS.md`)

## Task summary

Completed Task #11 acceptance closure for data contracts + schema drift by adding explicit invalid-type validation coverage and re-validating the full contract/drift implementation already present on `main`:

- verified existing implementation includes:
  - optional contract parsing for tabular ingests (`contract_file` / `--contract`)
  - safe YAML parsing + max size cap + Pydantic validation
  - lineage fields (`schema_fingerprint`, `contract_sha256`, `validation_status`, `validation_errors`, `schema_drifted`)
  - UI rendering for validation status and drift indicators
- added missing acceptance-focused test for clear invalid-type error messaging on contract mismatch

## Decisions made

- Keep this task slice minimal and reviewable because core task functionality is already in `main`.
- Add explicit test coverage for “invalid type” error clarity, which was the remaining acceptance criterion not directly asserted.
- Avoid broad refactors or behavior changes to already-validated ingestion contract paths.

## Files changed

- `tests/test_data_contracts.py`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_DATA_CONTRACTS.md`
   - `sed -n ... docs/DATA_CONTRACTS.md`
2. Discovery:
   - `sed -n ... app/contracts/tabular_contract.py`
   - `sed -n ... tests/test_data_contracts.py`
   - `rg -n ... web/src app/main.py tests`
3. Targeted validation:
   - `uv run pytest -q tests/test_data_contracts.py`
   - `uv run ruff check tests/test_data_contracts.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`
   - `make test-postgres`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`41 passed, 3 skipped` in Python; `12 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make test-postgres`: PASS (`1 skipped` when Docker/Postgres unavailable)

## What’s next

- Commit `TASK_DATA_CONTRACTS` on this branch and open PR.
- Move to queue item #12: `TASK_PUBSUB_PUSH_INGEST`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-pubsub-push-ingest`
- Current task: `TASK_PUBSUB_PUSH_INGEST` (`agents/tasks/TASK_PUBSUB_PUSH_INGEST.md`)

## Task summary

Implemented event-driven GCS ingestion via Pub/Sub push for private deployments:

- added backend endpoint: `POST /api/connectors/gcs/notify`
- added private connectors gating dependency for notify endpoint:
  - returns `404` when `PUBLIC_DEMO_MODE=1`
  - returns `404` when `ALLOW_CONNECTORS!=1`
  - requires admin role when enabled
- added Pub/Sub payload parsing:
  - attributes-first (`bucketId`, `objectId`, `eventType`)
  - fallback to base64-decoded `message.data` JSON (`bucket`/`bucketId`, `name`/`objectId`)
- added single-object GCS ingest helper in connector module to reuse existing ingest pipeline
- wired ingestion run lifecycle + structured logs for notify path
- added Terraform optional resources for private Pub/Sub push ingestion:
  - topic + DLQ topic
  - push subscription (OIDC push identity)
  - Cloud Run invoker IAM binding for push service account
  - bucket notification config (`OBJECT_FINALIZE`)
  - required Pub/Sub publisher IAM bindings
- updated runbook and contracts docs with setup/testing details

## Decisions made

- Keep notify processing synchronous and idempotent for this slice (returns `202` for accepted/duplicate events).
- Restrict processing to finalize events; non-finalize events return `202` with `ignored_event` result.
- Keep public demo safe-by-default by hiding endpoint availability (`404`) when connectors are disabled.

## Files changed

- `app/main.py`
- `app/connectors/gcs.py`
- `tests/test_pubsub_push_ingest.py`
- `infra/gcp/cloud_run_demo/pubsub_ingest.tf`
- `infra/gcp/cloud_run_demo/variables.tf`
- `infra/gcp/cloud_run_demo/outputs.tf`
- `infra/gcp/cloud_run_demo/README.md`
- `infra/gcp/cloud_run_demo/terraform.tfvars.example`
- `docs/RUNBOOKS/CONNECTORS_GCS.md`
- `docs/CONTRACTS.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_PUBSUB_PUSH_INGEST.md`
   - `sed -n ... docs/SPECS/PUBSUB_EVENT_INGESTION.md`
2. Branching:
   - `git checkout main`
   - `git pull --ff-only`
   - `git checkout -B codex/task-pubsub-push-ingest main`
3. Targeted validation during implementation:
   - `uv run ruff check app/main.py app/connectors/gcs.py tests/test_pubsub_push_ingest.py`
   - `uv run mypy app`
   - `uv run pytest -q tests/test_pubsub_push_ingest.py tests/test_ingestion_runs.py`
   - `terraform -chdir=infra/gcp/cloud_run_demo fmt -recursive`
   - `terraform -chdir=infra/gcp/cloud_run_demo init -backend=false -input=false`
   - `terraform -chdir=infra/gcp/cloud_run_demo validate`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`
   - `terraform -chdir=infra/gcp/cloud_run_demo fmt -check -recursive`
   - `terraform -chdir=infra/gcp/cloud_run_demo validate`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`46 passed, 3 skipped` in Python; `12 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `terraform -chdir=infra/gcp/cloud_run_demo fmt -check -recursive`: PASS
- `terraform -chdir=infra/gcp/cloud_run_demo validate`: PASS

## What’s next

- Commit `TASK_PUBSUB_PUSH_INGEST` on this branch and open PR.
- Move to queue item #13: `TASK_SCHEDULER_PERIODIC_SYNC`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-scheduler-periodic-sync`
- Current task: `TASK_SCHEDULER_PERIODIC_SYNC` (`agents/tasks/TASK_SCHEDULER_PERIODIC_SYNC.md`)

## Task summary

Implemented Task #13 periodic private sync via Cloud Scheduler:

- added optional Terraform scheduler stack:
  - dedicated scheduler service account
  - Cloud Run `roles/run.invoker` IAM binding
  - Cloud Scheduler HTTP job posting to `POST /api/connectors/gcs/sync`
- added configurable scheduler controls (schedule/timezone/pause and sync payload inputs including bucket/prefix)
- added optional API-key header injection for `AUTH_MODE=api_key` private deployments
- added backend structured logging for scheduled sync triggers with:
  - `event=connector.gcs.sync.scheduled`
  - `job_name`, `bucket`, `prefix`, `run_id`
- updated connector runbook and Terraform docs for configure/force-run/pause/disable workflows

## Decisions made

- Used Cloud Scheduler OIDC identity + Cloud Run invoker IAM as the baseline invocation model for private services.
- Kept app auth behavior unchanged (OIDC mode remains unimplemented); added optional `scheduler_sync_api_key` for current `AUTH_MODE=api_key` operator workflows.
- Kept periodic sync private-only by validating `allow_unauthenticated=false` and requiring private-mode connector overrides (`PUBLIC_DEMO_MODE=0`, `ALLOW_CONNECTORS=1`) when enabled.
- Implemented scheduled-trigger observability in the existing sync endpoint rather than adding a new endpoint surface.

## Files changed

- `infra/gcp/cloud_run_demo/scheduler_sync.tf`
- `infra/gcp/cloud_run_demo/variables.tf`
- `infra/gcp/cloud_run_demo/outputs.tf`
- `infra/gcp/cloud_run_demo/terraform.tfvars.example`
- `infra/gcp/cloud_run_demo/README.md`
- `app/main.py`
- `tests/test_ingestion_runs.py`
- `docs/RUNBOOKS/CONNECTORS_GCS.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_SCHEDULER_PERIODIC_SYNC.md`
   - `sed -n ... docs/SPECS/SCHEDULER_PERIODIC_SYNC.md`
2. Branching:
   - `git checkout main`
   - `git pull --ff-only`
   - `git checkout -b codex/task-scheduler-periodic-sync`
3. Targeted validation during implementation:
   - `uv run pytest -q tests/test_ingestion_runs.py`
   - `terraform -chdir=infra/gcp/cloud_run_demo fmt -check -recursive`
   - `terraform -chdir=infra/gcp/cloud_run_demo init -reconfigure -backend=false`
   - `terraform -chdir=infra/gcp/cloud_run_demo validate`
   - `docker run ... tflint`
   - `docker run ... tfsec`
   - `docker run ... checkov --skip-check "CKV_GCP_84,CKV_GCP_26,CKV2_GCP_18,CKV_GCP_79,CKV_GCP_6,CKV_GCP_83,CKV_SECRET_4"`
   - `docker run ... conftest`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`47 passed, 3 skipped` in Python; `12 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- Terraform checks:
  - `fmt -check -recursive`: PASS
  - `validate`: PASS
  - `tflint`: PASS
  - `tfsec`: PASS
  - `checkov` (workflow-aligned skip list): PASS
  - `conftest`: PASS

## What’s next

- Commit `TASK_SCHEDULER_PERIODIC_SYNC` on this branch and open PR.
- Move to queue item #14: `TASK_GOVERNANCE_METADATA_UI`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-governance-metadata-ui`
- Current task: `TASK_GOVERNANCE_METADATA_UI` (`agents/tasks/TASK_GOVERNANCE_METADATA_UI.md`)

## Task summary

Completed Task #14 governance metadata UX hardening by closing the remaining acceptance gaps:

- added role-aware metadata edit gating in `/api/meta` via `metadata_edit_enabled`
- updated Doc Detail metadata editor UX to include:
  - explicit read-only reason when editing is unavailable
  - canonical client-side validation for classification/retention
  - deterministic tag normalization (lowercase/trim/slugify/de-dupe)
  - actionable error messaging (client + server detail extraction)
  - save success toast feedback
- added unit tests for new metadata normalization/validation helpers
- added auth test coverage verifying edit capability is exposed by role in meta response

## Decisions made

- Preserved existing retention-clock invariant (`updated_at` unchanged for metadata-only edits), consistent with storage contract/tests and runbook messaging.
- Used `metadata_edit_enabled` as the UI gating signal so front-end can honor editor/admin-only edit mode without introducing new auth UI.
- Kept backend metadata validation as source of truth while adding client-side canonical checks for faster, actionable operator feedback.

## Files changed

- `app/main.py`
- `tests/test_auth.py`
- `web/src/api.ts`
- `web/src/pages/DocDetail.tsx`
- `web/src/lib/governanceMetadata.ts`
- `web/src/lib/governanceMetadata.test.ts`
- `docs/CONTRACTS.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... agents/tasks/TASK_GOVERNANCE_METADATA_UI.md`
   - `sed -n ... docs/SPECS/GOVERNANCE_METADATA.md`
2. Branching:
   - `git checkout main`
   - `git pull --ff-only`
   - `git checkout -b codex/task-governance-metadata-ui`
3. Discovery:
   - `rg -n "classification|retention|tags|governance|metadata" web app docs tests -S`
   - `sed -n ... web/src/pages/DocDetail.tsx`
   - `sed -n ... tests/test_doc_update_api.py`
   - `sed -n ... tests/test_auth.py`
   - `sed -n ... app/metadata.py`
4. Targeted validation:
   - `uv run pytest -q tests/test_auth.py tests/test_doc_update_api.py`
   - `cd web && corepack pnpm run test -- --run src/lib/governanceMetadata.test.ts`
   - `cd web && corepack pnpm run typecheck`
5. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`48 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## What’s next

- Commit `TASK_GOVERNANCE_METADATA_UI` on this branch and open PR.
- Move to queue item #15: `TASK_RETENTION_ENFORCEMENT`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-retention-enforcement`
- Current task: `TASK_RETENTION_ENFORCEMENT` (`agents/tasks/TASK_RETENTION_ENFORCEMENT.md`)

## Task summary

Implemented Task #15 retention enforcement with retrieval filtering and operator sweep tooling:

- retrieval now excludes retention-expired docs/chunks in both SQLite and Postgres retrieval paths
- added reusable retention helpers (`retention_expires_at`, `retention_is_expired`) for deterministic expiry checks
- added new CLI command `retention-sweep` (dry-run default, `--apply` for deletes)
- retention sweep is blocked in `PUBLIC_DEMO_MODE` to preserve safe public posture
- kept `purge-expired` as a backwards-compatible alias to avoid breaking existing automation/docs
- updated maintenance docs and Make targets to use `retention-sweep`
- added tests covering retrieval enforcement and CLI sweep behavior

## Decisions made

- Kept retention clock tied to `updated_at` (content-ingest timestamp) to preserve existing contract/invariant that metadata-only edits do not reset retention age.
- Enforced retention at retrieval-time (not API-layer mutation) so expired content is non-retrievable even before delete sweeps run.
- Preserved API safety boundary: maintenance API remains read-only; destructive sweep/delete stays CLI-only.
- Introduced `retention-sweep` as canonical command and retained `purge-expired` as alias for compatibility.

## Files changed

- `app/maintenance.py`
- `app/retrieval.py`
- `app/cli.py`
- `Makefile`
- `tests/test_retention_enforcement.py`
- `docs/CONTRACTS.md`
- `docs/DOMAIN.md`
- `docs/RUNBOOKS/MAINTENANCE.md`
- `docs/TUTORIAL.md`
- `docs/DEV_SETUP_MACOS.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... docs/PRODUCT/PRODUCT_BRIEF.md`
   - `sed -n ... docs/ARCHITECTURE/README.md`
   - `sed -n ... docs/DOMAIN.md`
   - `sed -n ... docs/DESIGN.md`
   - `sed -n ... docs/CONTRACTS.md`
   - `sed -n ... docs/WORKFLOW.md`
   - `sed -n ... agents/tasks/TASK_RETENTION_ENFORCEMENT.md`
   - `sed -n ... docs/SPECS/GOVERNANCE_METADATA.md`
   - `sed -n ... docs/ARCHITECTURE/SECURITY_MODEL.md`
   - `sed -n ... docs/PRODUCT/FEATURE_MATRIX.md`
   - `rg -n "retention|purge-expired|maintenance|retrieve" app tests docs -S`
2. Branching:
   - `git checkout main`
   - `git pull --ff-only`
   - `git checkout -b codex/task-retention-enforcement`
3. Targeted validation during implementation:
   - `uv run ruff check app/maintenance.py app/retrieval.py app/cli.py tests/test_retention_enforcement.py`
   - `uv run pytest -q tests/test_retention_purge.py tests/test_retention_enforcement.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`
   - `make test-postgres`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`51 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make test-postgres`: PASS (`1 skipped` when Docker/Postgres unavailable)

## What’s next

- Commit `TASK_RETENTION_ENFORCEMENT` on this branch and open PR.
- Move to queue item #16: `TASK_AUDIT_EVENTS`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-audit-events`
- Current task: `TASK_AUDIT_EVENTS` (`agents/tasks/TASK_AUDIT_EVENTS.md`)

## Task summary

Implemented Task #16 audit events for security-sensitive admin actions:

- added append-only `audit_events` storage model for SQLite + Postgres
- added Postgres migration `004_audit_events.sql`
- added storage helpers to insert/list audit events with filters (`action`, `since`, `until`, `limit`)
- added admin-only API endpoint:
  - `GET /api/audit-events`
- added shared audit write helper in API layer with metadata sanitization/redaction guardrails
- wired audit writes at required action points:
  - metadata update (`doc.metadata.updated`)
  - doc delete (`doc.deleted`)
  - connector sync trigger (`connector.gcs.sync.triggered`)
  - eval run trigger (`eval.run.created`)
- added tests for endpoint access/filtering, write-point coverage, request-id correlation, and migration/table creation

## Decisions made

- Kept audit logging API read-only; write actions remain endpoint-internal/CLI-internal (no new public write surface).
- Used explicit per-action metadata payloads plus a sanitizer/redactor to avoid storing document content or secrets.
- Scoped endpoint access to `admin` role only, consistent with security model and task requirement.
- Used correlation via existing `request_id` middleware state so audit events align with structured request logs.

## Files changed

- `app/storage.py`
- `app/main.py`
- `app/migrations/postgres/004_audit_events.sql`
- `tests/test_audit_events.py`
- `tests/test_storage_migrations.py`
- `docs/CONTRACTS.md`
- `docs/DOMAIN.md`
- `docs/ARCHITECTURE/DATA_MODEL.md`
- `docs/ARCHITECTURE/SECURITY_MODEL.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... harness.toml`
   - `sed -n ... docs/PRODUCT/PRODUCT_BRIEF.md`
   - `sed -n ... docs/PRODUCT/FEATURE_MATRIX.md`
   - `sed -n ... docs/ARCHITECTURE/README.md`
   - `sed -n ... docs/DOMAIN.md`
   - `sed -n ... docs/DESIGN.md`
   - `sed -n ... docs/CONTRACTS.md`
   - `sed -n ... agents/tasks/TASK_AUDIT_EVENTS.md`
   - `sed -n ... docs/SPECS/GOVERNANCE_METADATA.md`
   - `rg -n "audit|request_id|principal|doc_update|delete_doc|eval|connectors/gcs/sync" app tests docs -S`
2. Branching:
   - `git checkout main`
   - `git pull --ff-only`
   - `git checkout -b codex/task-audit-events`
3. Targeted validation during implementation:
   - `uv run ruff check app/main.py app/storage.py tests/test_audit_events.py tests/test_storage_migrations.py`
   - `uv run mypy app`
   - `uv run pytest -q tests/test_audit_events.py tests/test_storage_migrations.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`
   - `make test-postgres`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`54 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make test-postgres`: PASS (`1 skipped` when Docker/Postgres unavailable)

## What’s next

- Commit `TASK_AUDIT_EVENTS` on this branch and open PR.
- Move to queue item #17: `TASK_SAFETY_HARDENING`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-safety-hardening`
- Current task: `TASK_SAFETY_HARDENING` (`agents/tasks/TASK_SAFETY_HARDENING.md`)

## Task summary

Implemented Task #17 safety hardening across API, streaming, UI refusal messaging, and safety eval coverage:

- expanded prompt-injection detection coverage for subtle instruction-hijack/system-reveal attempts
- standardized refusal reasons to canonical categories:
  - `safety_block`
  - `insufficient_evidence`
  - `internal_error`
- hardened refusal behavior for weak/unrelated citation support (query + stream paths)
- added explicit internal-error refusal handling when answer generation throws
- updated UI fallback refusal mapping to align with canonical refusal codes
- extended prompt-injection eval dataset and added dedicated backend tests for safety detection/hardening

## Decisions made

- Kept public demo safe-by-default and extractive-only posture unchanged; no new privileged data exposure paths were introduced.
- Used a citation relevance heuristic based on question-term overlap against citation quotes (rather than quote length alone) to avoid false refusals on valid short evidence.
- Mapped provider/model refusals to `insufficient_evidence` so refusal semantics remain user-safe and contract-stable.
- Preserved debug/contract behavior while documenting canonical refusal codes in architecture/contracts docs.

## Files changed

- `app/main.py`
- `app/safety.py`
- `tests/test_safety_detection.py`
- `tests/test_safety_hardening.py`
- `data/eval/prompt_injection.jsonl`
- `web/src/pages/Home.tsx`
- `docs/CONTRACTS.md`
- `docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... harness.toml`
   - `sed -n ... docs/PRODUCT/PRODUCT_BRIEF.md`
   - `sed -n ... docs/ARCHITECTURE/README.md`
   - `sed -n ... docs/DOMAIN.md`
   - `sed -n ... docs/DESIGN.md`
   - `sed -n ... docs/CONTRACTS.md`
   - `sed -n ... docs/WORKFLOW.md`
   - `sed -n ... agents/tasks/TASK_SAFETY_HARDENING.md`
   - `sed -n ... docs/ARCHITECTURE/SECURITY_MODEL.md`
   - `sed -n ... docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md`
2. Branching:
   - `git switch -c codex/task-safety-hardening`
3. Targeted validation during implementation:
   - `uv run ruff check app/main.py app/safety.py tests/test_safety_detection.py tests/test_safety_hardening.py`
   - `uv run mypy app`
   - `uv run pytest -q tests/test_safety_detection.py tests/test_safety_hardening.py`
   - `uv run pytest -q tests/test_streaming.py tests/test_safety_detection.py tests/test_safety_hardening.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`66 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## What’s next

- Commit `TASK_SAFETY_HARDENING` on this branch and open PR.
- Move to queue item #18: `TASK_EVAL_PRODUCTIZATION`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-eval-productization`
- Current task: `TASK_EVAL_PRODUCTIZATION` (`agents/tasks/TASK_EVAL_PRODUCTIZATION.md`)

## Task summary

Implemented Task #18 evaluation productization with persisted runs, run history APIs, and UI run history/detail experience:

- added persisted `eval_runs` data model for SQLite + Postgres migrations
- expanded eval run payload to include aggregate pass/fail metrics and stable per-case detail records
- implemented eval run persistence with required metadata snapshots:
  - app version
  - embeddings backend/model
  - retrieval config (`k` + hybrid weights)
  - provider config
- added API endpoints for run history and run detail:
  - `GET /api/eval/runs`
  - `GET /api/eval/runs/{run_id}`
- enhanced `POST /api/eval/run` to persist runs and return `run_id` + metadata/diff summary
- added run-to-run diff calculation (delta metrics + regressions/improvements)
- updated Eval UI to show:
  - aggregate metrics
  - per-case pass/fail
  - run history list
  - simple pass-rate sparkline trend
  - dedicated run detail page with case-level diff signals

## Decisions made

- Kept eval endpoints private/admin-only and disabled in `PUBLIC_DEMO_MODE`, preserving ADR non-negotiables for public demo safety.
- Used a single persisted `eval_runs` table with JSON columns (`summary_json`, `details_json`, `diff_from_prev_json`) for small, reviewable implementation scope while still enabling history/detail/diff UX.
- Always materialized per-case details during run execution for reliable persistence/diffing; `include_details` now controls response verbosity rather than storage completeness.
- Modeled hybrid retrieval weights in metadata from actual runtime behavior (`0.5/0.5` with vector enabled, `1.0/0.0` lexical-only).

## Files changed

- `app/eval.py`
- `app/main.py`
- `app/storage.py`
- `app/migrations/postgres/005_eval_runs.sql`
- `tests/test_eval_runs.py`
- `tests/test_storage_migrations.py`
- `web/src/api.ts`
- `web/src/pages/Eval.tsx`
- `web/src/pages/EvalRunDetail.tsx`
- `web/src/router.tsx`
- `docs/CONTRACTS.md`
- `docs/ARCHITECTURE/DATA_MODEL.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `git fetch --all --prune && git log --oneline --decorate -n 8 --all --simplify-by-decoration`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... agents/tasks/TASK_EVAL_PRODUCTIZATION.md`
   - `sed -n ... docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`
2. Branching:
   - `git checkout main && git pull --ff-only && git checkout -b codex/task-eval-productization`
3. Targeted validation during implementation:
   - `uv run ruff check app/eval.py app/main.py app/storage.py tests/test_eval_runs.py tests/test_storage_migrations.py`
   - `uv run mypy app`
   - `uv run pytest -q tests/test_eval_runs.py tests/test_storage_migrations.py`
   - `cd web && corepack pnpm run typecheck`
   - `cd web && corepack pnpm run test -- --run ...`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`69 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## What’s next

- Commit `TASK_EVAL_PRODUCTIZATION` on this branch and open PR.
- Move to queue item #19: `TASK_EVAL_CI_SMOKE`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-eval-ci-smoke`
- Current task: `TASK_EVAL_CI_SMOKE` (`agents/tasks/TASK_EVAL_CI_SMOKE.md`)

## Task summary

Implemented Task #19 CI smoke eval gate to catch retrieval/safety regressions quickly:

- added `data/eval/smoke.jsonl` as a small, fast retrieval smoke suite
- added `scripts/eval_smoke_gate.py` to run CI-style smoke checks end-to-end in-process:
  - retrieval smoke quality threshold gate (minimum pass rate)
  - refusal behavior smoke checks (expected refuse + expected non-refuse)
  - prompt-injection regression suite checks (hard failure on safety regressions)
- added explicit GitHub Actions step `Run eval smoke gate` in `.github/workflows/ci.yml`
- added local Make shortcut `make eval-smoke` and help text in `Makefile`

## Decisions made

- Used an in-process FastAPI `TestClient` smoke harness instead of external HTTP server startup to keep runtime deterministic and well under the 2-minute budget.
- Kept smoke gate aligned with public demo safety posture by forcing demo-safe runtime settings in the smoke script (`PUBLIC_DEMO_MODE=1`, `CITATIONS_REQUIRED=1`, uploads/eval/connectors disabled).
- Evaluated prompt-injection suite with a safety-focused assertion model:
  - injection cases must refuse with `safety_block`
  - non-injection cases must not be classified as `safety_block` (they may still refuse for evidence reasons)
- Selected a retrieval threshold of `0.80` for smoke gating to catch obvious regressions while avoiding overfitting to exact rank order.

## Files changed

- `.github/workflows/ci.yml`
- `Makefile`
- `data/eval/smoke.jsonl`
- `scripts/eval_smoke_gate.py`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `git fetch --all --prune && git log --oneline --decorate ...`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... agents/tasks/TASK_EVAL_CI_SMOKE.md`
   - `sed -n ... docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`
   - `sed -n ... harness.toml`
2. Branching:
   - `git checkout main && git pull --ff-only && git checkout -b codex/task-eval-ci-smoke`
3. Targeted validation during implementation:
   - `uv run ruff check scripts/eval_smoke_gate.py`
   - `uv run python scripts/eval_smoke_gate.py --dataset ... --prompt-suite ... --k 5 --min-pass-rate 0.80`
   - `make eval-smoke`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`69 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `make eval-smoke`: PASS

## What’s next

- Commit `TASK_EVAL_CI_SMOKE` on this branch and open PR.
- Move to queue item #20: `TASK_EVAL_DATASET_AUTHORING`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-eval-dataset-authoring`
- Current task: `TASK_EVAL_DATASET_AUTHORING` (`agents/tasks/TASK_EVAL_DATASET_AUTHORING.md`)

## Task summary

Implemented Task #20 eval dataset authoring docs + validator tooling:

- added `docs/EVAL_DATASETS.md` with canonical JSONL schema, answerable/refusal examples, safe update workflow, and anti-flake guidance
- added dataset validator logic in `app/eval.py` with strict line-level checks for:
  - malformed JSON
  - missing/invalid required fields
  - duplicate IDs
  - invalid expectation shape/type
- added CLI helper command:
  - `python -m app.cli validate-eval-dataset <path>.jsonl`
- wired retrieval eval to run dataset validation before execution and to evaluate only citation-targeted cases
- added automated tests covering valid datasets, malformed/missing fields, and CLI success/failure behavior

## Decisions made

- Kept backward compatibility with existing repo datasets while introducing canonical `expect` format:
  - supports legacy retrieval rows (`expected_doc_ids` / `expected_chunk_ids`)
  - supports legacy safety rows (`expect_refusal: true|false`)
- Enforced strict validation errors (non-zero exit) so malformed dataset edits fail early in local workflows and CI.
- Preserved deterministic eval behavior by skipping non-citation cases in `run_eval` instead of forcing ambiguous pass/fail semantics.

## Files changed

- `app/eval.py`
- `app/cli.py`
- `tests/test_eval_dataset_validation.py`
- `docs/EVAL_DATASETS.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... harness.toml`
   - `sed -n ... docs/PRODUCT/PRODUCT_BRIEF.md`
   - `sed -n ... docs/ARCHITECTURE/README.md`
   - `sed -n ... docs/DOMAIN.md`
   - `sed -n ... docs/DESIGN.md`
   - `sed -n ... docs/CONTRACTS.md`
   - `sed -n ... docs/WORKFLOW.md`
   - `sed -n ... agents/tasks/TASK_EVAL_DATASET_AUTHORING.md`
   - `sed -n ... docs/SPECS/EVAL_HARNESS_PRODUCTIZATION.md`
2. Branching:
   - `git checkout main && git pull --ff-only && git checkout -b codex/task-eval-dataset-authoring`
3. Targeted validation during implementation:
   - `uv run ruff check app/eval.py app/cli.py tests/test_eval_dataset_validation.py`
   - `uv run pytest -q tests/test_eval_dataset_validation.py`
   - `uv run python -m app.cli validate-eval-dataset data/eval/golden.jsonl`
   - `uv run python -m app.cli validate-eval-dataset data/eval/smoke.jsonl`
   - `uv run python -m app.cli validate-eval-dataset data/eval/prompt_injection.jsonl`
   - `make eval-smoke`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`73 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `validate-eval-dataset` smoke checks on repo datasets: PASS
- `make eval-smoke`: PASS

## What’s next

- Commit `TASK_EVAL_DATASET_AUTHORING` on this branch and open PR.
- Move to queue item #21: `TASK_OTEL`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-otel-observability`
- Current task: `TASK_OTEL` (`agents/tasks/TASK_OTEL.md`)

## Task summary

Completed Task #21 OpenTelemetry observability hardening slice focused on trace/log correlation and regression coverage:

- added active OTEL context extraction helper in `app/observability.py` (`current_trace_context`)
- updated request middleware logging in `app/main.py` to resolve `trace_id`/`span_id` from active OTEL span context when `X-Cloud-Trace-Context` is absent
- preserved existing request-ID propagation behavior while strengthening trace correlation in structured logs
- added OTEL regression test to ensure `/api/query` logs include `trace_id` + `span_id` under `OTEL_ENABLED=1` without requiring incoming Cloud Trace headers
- updated observability docs to describe trace correlation behavior (header-first fallback to active span context)

## Decisions made

- Existing OTEL tracing/metrics instrumentation already satisfied most task requirements; implementation focused on the remaining reliability gap for log correlation when upstream trace headers are missing.
- Kept privacy posture unchanged (no prompt/document content in span attributes by default).
- Branch naming note: `codex/task-otel` already existed from earlier work, so this task used `codex/task-otel-observability` to keep a clean, reviewable diff.

## Files changed

- `app/observability.py`
- `app/main.py`
- `tests/test_otel.py`
- `docs/OBSERVABILITY.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_OTEL.md`
   - `sed -n ... docs/SPECS/OBSERVABILITY_OPS.md`
   - `sed -n ... docs/OBSERVABILITY.md`
   - `sed -n ... app/otel.py`
   - `sed -n ... tests/test_otel.py`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git checkout -b codex/task-otel-observability`
3. Targeted validation during implementation:
   - `uv run ruff check app/main.py app/observability.py tests/test_otel.py`
   - `uv run pytest -q tests/test_otel.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`73 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)
- `uv run pytest -q tests/test_otel.py`: SKIP in local env when OTEL packages are unavailable (expected optional dependency behavior)

## What’s next

- Commit `TASK_OTEL` on this branch and open PR.
- Move to queue item #22: `TASK_DASHBOARDS_TERRAFORM`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-dashboards-terraform`
- Current task: `TASK_DASHBOARDS_TERRAFORM` (`agents/tasks/TASK_DASHBOARDS_TERRAFORM.md`)

## Task summary

Implemented Task #22 Terraform-managed observability dashboards with expanded operator coverage and docs:

- upgraded `infra/gcp/cloud_run_demo/observability.tf` dashboard model to include:
  - Cloud Run request count, 5xx, p95 latency
  - query latency breakdown (retrieval vs answer generation OTEL metrics)
  - ingestion failures widget for private deployments
  - Cloud SQL health widgets (CPU utilization + active backends) when Cloud SQL is enabled
  - existing recent error logs panel
- added Terraform-managed log-based metric for ingestion failures in private deployments:
  - `google_logging_metric.ingestion_failures`
- added output for the ingestion failure metric name:
  - `ingestion_failure_metric_name`
- updated observability docs/runbook references explaining dashboard contents and how to fetch dashboard outputs
- aligned local `make tf-check` behavior with CI by syncing checkov skip IDs and conftest file selection in `Makefile`

## Decisions made

- Kept ingestion failure metric/dashboard coverage private-only (`allow_unauthenticated=false`) to align with “private deployment operator workflows” and avoid irrelevant public-demo noise.
- Used existing OTEL metric names (`workload.googleapis.com/gkp.query.*`) for query stage latency instead of adding new custom app instrumentation.
- Included Cloud SQL widgets conditionally (`enable_cloudsql=true`) to preserve the one-project-per-client Cloud SQL baseline while keeping non-CloudSQL experiments valid.
- Updated local Terraform hygiene commands to mirror CI skip logic and conftest invocation so local validation matches pipeline behavior.

## Files changed

- `infra/gcp/cloud_run_demo/observability.tf`
- `infra/gcp/cloud_run_demo/outputs.tf`
- `infra/gcp/cloud_run_demo/README.md`
- `docs/OBSERVABILITY.md`
- `Makefile`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_DASHBOARDS_TERRAFORM.md`
   - `sed -n ... docs/SPECS/OBSERVABILITY_OPS.md`
   - `sed -n ... infra/gcp/cloud_run_demo/*.tf`
2. Branching:
   - `git checkout main && git pull --ff-only && git checkout -b codex/task-dashboards-terraform`
3. Targeted Terraform validation:
   - `terraform -chdir=infra/gcp/cloud_run_demo fmt -recursive`
   - `terraform -chdir=infra/gcp/cloud_run_demo init -backend=false -upgrade`
   - `terraform -chdir=infra/gcp/cloud_run_demo validate`
   - `make tf-check`
   - `terraform plan` proof run in backendless temp copy (to avoid remote backend dependency) with active project vars; confirmed planned resources:
     - `google_logging_metric.ingestion_failures[0]`
     - `google_monitoring_alert_policy.cloudrun_5xx[0]`
     - `google_monitoring_alert_policy.cloudrun_latency_p95[0]`
     - `google_monitoring_dashboard.cloudrun[0]`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make tf-check`: PASS
- `terraform plan` resource check: PASS (dashboard + alert + ingestion metric resources in plan output)
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`73 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## What’s next

- Commit `TASK_DASHBOARDS_TERRAFORM` on this branch and open PR.
- Move to queue item #23: `TASK_SLOS_BURN_RATE`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-slos-burn-rate`
- Current task: `TASK_SLOS_BURN_RATE` (`agents/tasks/TASK_SLOS_BURN_RATE.md`)

## Task summary

Implemented Task #23 SLO + burn-rate alert baseline for Cloud Run in Terraform:

- added latency SLO alongside existing availability SLO
- added separate burn-rate alert policies for availability and latency SLOs
- aligned burn-rate windows to spec style (`1h` fast, `6h` slow)
- parameterized SLO/burn-rate tuning inputs in Terraform variables
- added dedicated operator runbook for SLO alert triage (`docs/RUNBOOKS/SLOS.md`)
- updated observability and infra docs with new outputs and runbook links

## Decisions made

- Kept existing `slo_full_name` output as a backward-compatible alias for availability while adding explicit latency/alert outputs.
- Used configurable defaults tuned for demo + small private deployments:
  - availability goal `99.5%`
  - latency goal `95%` under `1200ms`
  - burn-rate thresholds `6` (fast) and `3` (slow)
- Used dual SLO burn-rate policies (availability and latency) so alerts are actionable by failure mode.

## Files changed

- `infra/gcp/cloud_run_demo/slo.tf`
- `infra/gcp/cloud_run_demo/variables.tf`
- `infra/gcp/cloud_run_demo/terraform.tfvars.example`
- `infra/gcp/cloud_run_demo/README.md`
- `docs/OBSERVABILITY.md`
- `docs/RUNBOOKS/SLOS.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... harness.toml`
   - `sed -n ... agents/tasks/TASK_SLOS_BURN_RATE.md`
   - `sed -n ... docs/SPECS/OBSERVABILITY_OPS.md`
2. Terraform/doc implementation:
   - edits in `slo.tf`, `variables.tf`, docs, and new runbook
3. Task validation:
   - `make tf-check`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make tf-check`: PASS
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`73 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## What’s next

- Commit `TASK_SLOS_BURN_RATE` on this branch and open PR.
- Move to queue item #24: `TASK_COST_GUARDRAILS`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-cost-guardrails`
- Current task: `TASK_COST_GUARDRAILS` (`agents/tasks/TASK_COST_GUARDRAILS.md`)

## Task summary

Implemented Task #24 cost guardrails across infra, app, tests, and runbooks:

- added Cloud Run request guardrail knobs in Terraform:
  - `max_request_concurrency` (default `40`)
  - `request_timeout_seconds` (default `30`)
- added optional Terraform-managed project budget alerts:
  - `google_billing_budget` resource (`cost_guardrails.tf`)
  - budget amount + threshold configuration variables
  - optional Monitoring notification channels
  - output `billing_budget_name`
- added app payload size guardrail for query endpoints:
  - `MAX_QUERY_PAYLOAD_BYTES` (default `32768`)
  - enforced on `POST /api/query` and `POST /api/query/stream`
  - returns `413` for oversized payloads
- added test coverage for payload limit behavior and `/api/meta` surface
- added cost incident runbook and updated cost/safety docs with concrete knobs

## Decisions made

- Kept billing budgets optional by default (`enable_billing_budget=false`) to avoid forcing Billing Account configuration in every demo deploy.
- Enforced a required `billing_account_id` when budgets are enabled to prevent silent no-op config.
- Scoped payload-size guardrail to query endpoints only (the highest-risk abuse path) and preserved existing upload-specific size enforcement.
- Preserved ADR posture: no edge WAF dependency; controls stay in-app + Cloud Run + Terraform budgeting.

## Files changed

- `infra/gcp/modules/cloud_run_service/main.tf`
- `infra/gcp/modules/cloud_run_service/variables.tf`
- `infra/gcp/modules/cloud_run_service/README.md`
- `infra/gcp/cloud_run_demo/main.tf`
- `infra/gcp/cloud_run_demo/variables.tf`
- `infra/gcp/cloud_run_demo/cost_guardrails.tf`
- `infra/gcp/cloud_run_demo/outputs.tf`
- `infra/gcp/cloud_run_demo/terraform.tfvars.example`
- `infra/gcp/cloud_run_demo/README.md`
- `app/config.py`
- `app/main.py`
- `tests/test_cost_guardrails.py`
- `docs/COST_HYGIENE.md`
- `docs/public-demo-checklist.md`
- `docs/RUNBOOKS/COST_INCIDENT.md`
- `docs/RUNBOOKS/INCIDENT.md`
- `docs/CONTRACTS.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... harness.toml`
   - `sed -n ... agents/tasks/TASK_COST_GUARDRAILS.md`
   - `sed -n ... docs/SPECS/OBSERVABILITY_OPS.md`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git checkout -b codex/task-cost-guardrails`
3. Targeted discovery/implementation checks:
   - `rg -n ...` across infra/app/docs for existing guardrails
   - `sed -n ...` across Terraform module/root/docs/app/test files
   - `terraform ... providers schema -json ...` (temporary backendless copies) to confirm `google_billing_budget` and Cloud Run v2 timeout/concurrency schema fields
4. Validation:
   - `terraform -chdir=infra/gcp/cloud_run_demo fmt -recursive`
   - `make tf-check`
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make tf-check`: PASS
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`76 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- Local `terraform validate`/`tf-check` initially hit a provider startup timeout on this workstation; rerunning after clearing local `.terraform` directory resolved it.

## What’s next

- Commit `TASK_COST_GUARDRAILS` on this branch and open PR.
- Move to queue item #25: `TASK_SMOKE_TESTS_DEPLOY`.

---

## Session

- Date: 2026-02-21
- Agent: Codex
- Branch: `codex/task-smoke-tests-deploy`
- Current task: `TASK_SMOKE_TESTS_DEPLOY` (`agents/tasks/TASK_SMOKE_TESTS_DEPLOY.md`)

## Task summary

Implemented Task #25 post-deploy smoke workflow with Makefile shortcuts and actionable output:

- added `scripts/deploy_smoke.py` smoke runner for:
  - `GET /health`
  - `GET /ready`
  - `GET /api/meta`
  - `POST /api/query` with demo-safe known-answer question
- added Make targets:
  - `make smoke` (uses `SMOKE_URL` or Terraform `service_url` output)
  - `make smoke-local` (uses `GKP_API_URL`, intended for local `make dev`)
- updated `make deploy` to run smoke checks after apply (`deploy: build apply smoke`)
- added configurable smoke knobs:
  - `SMOKE_URL`, `SMOKE_QUERY`, `SMOKE_TIMEOUT_S`, `SMOKE_RETRIES`, `SMOKE_RETRY_DELAY_S`, `SMOKE_API_KEY`
- added unit tests for smoke runner behavior (`tests/test_deploy_smoke.py`)
- updated deploy/release docs to use the new smoke workflow

## Decisions made

- Kept existing `make verify` unchanged for quick endpoint checks and introduced `make smoke` as the richer post-deploy gate.
- Smoke runner enforces stricter assertions when deployment reports `public_demo_mode=true`:
  - extractive-only provider
  - uploads/connectors/eval disabled
  - query returns non-refusal with citations
- Added optional `SMOKE_API_KEY` support so smoke checks can also run against private deployments.
- Added lightweight retry support to reduce false negatives from fresh revision warm-up.

## Files changed

- `Makefile`
- `scripts/deploy_smoke.py`
- `tests/test_deploy_smoke.py`
- `docs/RUNBOOKS/RELEASE.md`
- `docs/DEPLOY_GCP.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_SMOKE_TESTS_DEPLOY.md`
   - `sed -n ... docs/SPECS/OBSERVABILITY_OPS.md`
   - `sed -n ... Makefile`
   - `rg -n ...` across workflows/docs/scripts for existing smoke/verify behavior
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git checkout -b codex/task-smoke-tests-deploy`
3. Task-specific validation:
   - `uv run pytest -q tests/test_deploy_smoke.py`
   - `uv run uvicorn app.main:app --port 8081` (temporary background)
   - `make smoke-local GKP_API_URL=http://127.0.0.1:8081`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `uv run pytest -q tests/test_deploy_smoke.py`: PASS (`2 passed`)
- `make smoke-local GKP_API_URL=http://127.0.0.1:8081`: PASS (`6/6` checks passed)
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`78 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## What’s next

- Commit `TASK_SMOKE_TESTS_DEPLOY` on this branch and open PR.
- Move to queue item #26: `TASK_BACKUP_RESTORE`.

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-backup-restore`
- Current task: `TASK_BACKUP_RESTORE` (`agents/tasks/TASK_BACKUP_RESTORE.md`)

## Task summary

Implemented Task #26 Cloud SQL backup/restore ops slice:

- hardened Cloud SQL Terraform backup configuration with explicit retention + PITR controls
- added operator-facing backup/restore drill runbook with RTO/RPO assumptions and step-by-step restore flow
- documented post-restore service smoke verification path and cleanup guidance
- updated deployment/Cloud SQL docs to point to the new runbook and backup knobs

## Decisions made

- Kept Cloud SQL backup automation enabled by default and made key backup controls explicit Terraform variables (`cloudsql_retained_backups`, backup start time, PITR toggle, transaction-log retention).
- Set PITR default to enabled for private deployment resilience; retained values remain configurable in tfvars.
- Chose documentation-first restore drill (task optional script not required) to keep this diff small and reviewable.
- Recommended PITR clone path in the runbook for staging restores, with backup-ID restore documented as an alternate operator path.

## Files changed

- `infra/gcp/cloud_run_demo/cloudsql.tf`
- `infra/gcp/cloud_run_demo/variables.tf`
- `infra/gcp/cloud_run_demo/terraform.tfvars.example`
- `infra/gcp/cloud_run_demo/README.md`
- `docs/DEPLOY_GCP.md`
- `docs/RUNBOOKS/CLOUDSQL.md`
- `docs/RUNBOOKS/BACKUP_RESTORE.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... harness.toml`
   - `sed -n ... docs/PRODUCT/PRODUCT_BRIEF.md docs/DOMAIN.md docs/ARCHITECTURE/README.md docs/DESIGN.md docs/CONTRACTS.md docs/WORKFLOW.md`
   - `sed -n ... agents/tasks/TASK_BACKUP_RESTORE.md`
   - `sed -n ... docs/SPECS/OBSERVABILITY_OPS.md`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git checkout -b codex/task-backup-restore`
3. Implementation/discovery support:
   - `rg -n ...` across Terraform/docs/runbooks
   - `gcloud sql backups restore --help`
   - `gcloud sql instances clone --help`
   - `terraform -chdir=infra/gcp/cloud_run_demo fmt -recursive`
4. Validation:
   - `make tf-check` (validated successfully via temporary Docker-backed `terraform` PATH wrapper due local host Terraform provider startup timeouts)
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make tf-check`: PASS
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`78 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- This workstation intermittently times out launching the local `hashicorp/google` Terraform provider for `terraform validate`; Docker-backed Terraform validation passed and produced a clean `make tf-check` run for this task.

## What’s next

- Commit `TASK_BACKUP_RESTORE` on this branch and open PR.
- Move to queue item #27: `TASK_RELEASE_PROCESS`.

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-release-process`
- Current task: `TASK_RELEASE_PROCESS` (`agents/tasks/TASK_RELEASE_PROCESS.md`)

## Task summary

Implemented Task #27 release-process baseline with consistent versioning + changelog workflow:

- added release tooling script (`scripts/release_tools.py`) with:
  - `bump`: updates `pyproject.toml` version and rolls `CHANGELOG.md` `Unreleased` into a dated release section
  - `notes`: extracts release notes for a specific version from `CHANGELOG.md`
- added Make targets:
  - `make release-bump VERSION=x.y.z [RELEASE_DATE=YYYY-MM-DD]`
  - `make release-notes VERSION=x.y.z [RELEASE_NOTES_OUT=...]`
- added new release process guide: `docs/RELEASES.md`
- updated release runbook and README docs map to link release process
- added automated tests for release tooling (`tests/test_release_tools.py`)
- updated `CHANGELOG.md` Unreleased entries to document release tooling/docs changes

## Decisions made

- Chose semantic versioning with `pyproject.toml` as the single source of truth for release version.
- Explicitly documented that `app/version.py` is not manually edited per release; it resolves version from installed metadata / pyproject fallback.
- Kept release tooling intentionally lightweight and repo-local (no new external release service dependency).
- Kept GitHub release workflow optional; task acceptance is met by documented sequence + repeatable local commands.

## Files changed

- `scripts/release_tools.py`
- `tests/test_release_tools.py`
- `Makefile`
- `docs/RELEASES.md`
- `docs/RUNBOOKS/RELEASE.md`
- `README.md`
- `CHANGELOG.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `tail -n ... docs/BACKLOG/EXECUTION_LOG.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_RELEASE_PROCESS.md`
   - `sed -n ... docs/SPECS/OBSERVABILITY_OPS.md`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git checkout -b codex/task-release-process`
3. Discovery/implementation support:
   - `rg -n ...` across Makefile/docs/scripts for version/changelog/release behavior
   - `sed -n ... CHANGELOG.md docs/RUNBOOKS/RELEASE.md README.md Makefile pyproject.toml app/version.py`
4. Task-specific checks:
   - `uv run pytest -q tests/test_release_tools.py`
   - `make release-notes VERSION=0.10.0`
5. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-refresh`
   - `make backlog-audit`

## Validation results (summarized)

- `uv run pytest -q tests/test_release_tools.py`: PASS (`3 passed`)
- `make release-notes VERSION=0.10.0`: PASS (`dist/release_notes_0.10.0.md` generated locally)
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`81 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-refresh`: PASS
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- `make release-notes` output in `dist/` is intentionally local artifact and not committed.

## What’s next

- Commit `TASK_RELEASE_PROCESS` on this branch and open PR.
- Move to queue item #28: `TASK_DEPENDABOT_CODE_SCANNING`.

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-dependabot-code-scanning`
- Current task: `TASK_DEPENDABOT_CODE_SCANNING` (`agents/tasks/TASK_DEPENDABOT_CODE_SCANNING.md`)

## Task summary

Implemented Task #28 DevSecOps dependency and code-scanning baseline:

- added Dependabot config (`.github/dependabot.yml`) for weekly updates:
  - Python dependencies (`pip` ecosystem, repo root)
  - web dependencies (`npm` ecosystem, `web/`)
  - grouped minor/patch updates and PR limits to reduce noise
- added CodeQL workflow (`.github/workflows/codeql.yml`) for:
  - `push` to `main`
  - `pull_request` targeting `main`
  - weekly scheduled scan + manual dispatch
  - matrix languages: `python` and `javascript-typescript`
- updated `SECURITY.md` with CI security posture and noise-control guidance
- updated `CHANGELOG.md` Unreleased section for discoverability

## Decisions made

- Chose weekly cadence for both ecosystems with small open PR caps to keep update flow manageable.
- Grouped minor/patch updates for Dependabot to reduce review overhead while still surfacing actionable update PRs.
- Used CodeQL default analysis profile for visibility without introducing severity-based merge blocking.
- Documented that CodeQL findings are visible in GitHub Security alerts while CI fails only for scanning execution failures.

## Files changed

- `.github/dependabot.yml`
- `.github/workflows/codeql.yml`
- `SECURITY.md`
- `CHANGELOG.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_DEPENDABOT_CODE_SCANNING.md`
   - `sed -n ... docs/SPECS/OBSERVABILITY_OPS.md`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git checkout -b codex/task-dependabot-code-scanning`
3. Discovery/implementation support:
   - `ls -la .github .github/workflows`
   - `sed -n ... SECURITY.md .github/workflows/ci.yml`
4. Task-specific checks:
   - `ruby -e 'require "yaml"; YAML.load_file(".github/dependabot.yml"); YAML.load_file(".github/workflows/codeql.yml"); puts "YAML_OK"'`
5. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- YAML parse/lint check: PASS (`YAML_OK`)
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`81 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- CodeQL alert triage remains in GitHub Security (no severity-based hard fail gate configured by default).

## What’s next

- Commit `TASK_DEPENDABOT_CODE_SCANNING` on this branch and open PR.
- Move to queue item #29: `TASK_CONTAINER_IMAGE_SCANNING`.

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-container-image-scanning`
- Current task: `TASK_CONTAINER_IMAGE_SCANNING` (`agents/tasks/TASK_CONTAINER_IMAGE_SCANNING.md`)

## Task summary

Implemented Task #29 container image vulnerability scanning baseline:

- added a new GitHub Actions workflow (`.github/workflows/container-image-scan.yml`) that:
  - builds the app image from `docker/Dockerfile`
  - runs Trivy image scan to produce SARIF and JSON reports
  - uploads SARIF to GitHub Security (code scanning)
  - uploads SARIF + JSON as workflow artifacts
- added optional strict CI fail gate controlled by repository variable `IMAGE_SCAN_FAIL_ON_SEVERITY`
  - default behavior remains report-only (non-blocking)
- updated `SECURITY.md` to document container scan posture and gate configuration
- updated `CHANGELOG.md` Unreleased entries

## Decisions made

- Used Trivy for pragmatic image scanning with broad ecosystem coverage and SARIF support.
- Chose report-first posture by default (`exit-code: 0`) to keep findings visible without adding brittle severity gate noise.
- Added optional fail gate so teams can enforce blocking on `CRITICAL,HIGH` (or other severities) without modifying workflow code.
- Published results in both Security tab (SARIF) and artifacts (JSON/SARIF) for easy triage and auditability.

## Files changed

- `.github/workflows/container-image-scan.yml`
- `SECURITY.md`
- `CHANGELOG.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_CONTAINER_IMAGE_SCANNING.md`
   - `sed -n ... docs/SPECS/OBSERVABILITY_OPS.md`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git checkout -b codex/task-container-image-scanning`
3. Discovery/implementation support:
   - `rg -n ...` across workflows/docs for existing scanner setup
   - `sed -n ... docker/Dockerfile cloudbuild.yaml SECURITY.md`
4. Task-specific checks:
   - `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/container-image-scan.yml"); puts "YAML_OK"'`
5. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- YAML parse/lint check: PASS (`YAML_OK`)
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`81 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- Strict vulnerability enforcement is opt-in via repository variable `IMAGE_SCAN_FAIL_ON_SEVERITY`; no blocking severity gate is enabled by default.

## What’s next

- Commit `TASK_CONTAINER_IMAGE_SCANNING` on this branch and open PR.
- Move to queue item #30: `TASK_BIGQUERY_EXPORT`.

### Follow-up (2026-02-22): CI fix for container-image-scan build instability

Applied a targeted fix after CI failure in the `container-image-scan` workflow when Docker build used lockfile URLs pointing at an internal mirror.

Changes:
- Added `actions/setup-python` + `astral-sh/setup-uv` in `.github/workflows/container-image-scan.yml`.
- Added a pre-build step to normalize `uv.lock` URLs via `uv lock --refresh` when mirror-host URLs are detected.
- Added retry loop for `docker build` to reduce transient network failure flakiness.

Validation rerun (all PASS):
- `make dev-doctor`
- `python scripts/harness.py lint`
- `python scripts/harness.py typecheck`
- `python scripts/harness.py test`
- `make backlog-audit`

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-bigquery-export`
- Current task: `TASK_BIGQUERY_EXPORT` (`agents/tasks/TASK_BIGQUERY_EXPORT.md`)

## Task summary

Implemented Task #30 BigQuery export baseline for private deployments:

- added a new export module (`app/bigquery_export.py`) with:
  - stable export schemas and row mappers for `docs`, `ingest_events`, and `eval_runs`
  - deterministic row iteration + chunking helpers
  - idempotent JSONL snapshot export (`docs.jsonl`, `ingest_events.jsonl`, `eval_runs.jsonl`, `manifest.json`)
  - optional direct BigQuery loading with truncate+append chunk strategy (idempotent reruns)
- added CLI command `export-bigquery` in `app/cli.py`:
  - blocked in `PUBLIC_DEMO_MODE`
  - supports JSONL-only mode (default workflow) and optional BigQuery load (`--project`, `--dataset`)
- added Makefile operator shortcut `make bigquery-export` with `BQ_*` overrides
- added dedicated runbook `docs/RUNBOOKS/BIGQUERY_EXPORT.md`
- updated docs discoverability (`README.md`, `docs/PRODUCT/FEATURE_MATRIX.md`) and changelog
- added unit tests `tests/test_bigquery_export.py` for:
  - schema mapping (lineage + governance fields)
  - export chunking behavior
  - idempotent JSONL snapshot output

## Decisions made

- Kept export path private-only and explicitly blocked in `PUBLIC_DEMO_MODE` to preserve ADR demo safety posture.
- Implemented JSONL snapshots as the default repeatable warehouse-compatible format, with optional BigQuery load layered on top.
- Chose full-snapshot idempotency semantics (rewrite JSONL + BigQuery truncate/append) to avoid duplicate rows on rerun.
- Included governance fields (`classification`, `retention`, `tags`) in `ingest_events` export via join with `docs` metadata.
- Kept BigQuery dependency optional at runtime (`google-cloud-bigquery` imported lazily), avoiding baseline dependency changes for demo/private non-BQ installs.

## Files changed

- `app/bigquery_export.py`
- `app/cli.py`
- `tests/test_bigquery_export.py`
- `Makefile`
- `docs/RUNBOOKS/BIGQUERY_EXPORT.md`
- `README.md`
- `docs/PRODUCT/FEATURE_MATRIX.md`
- `CHANGELOG.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_BIGQUERY_EXPORT.md`
   - `sed -n ... docs/SPECS/BIGQUERY_EXPORT.md`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git checkout -b codex/task-bigquery-export`
3. Discovery/implementation support:
   - `rg -n "bigquery|export|..." app scripts docs tests Makefile pyproject.toml`
   - `sed -n ... app/cli.py`
   - `sed -n ... app/storage.py`
   - `sed -n ... README.md docs/PRODUCT/FEATURE_MATRIX.md Makefile CHANGELOG.md`
4. Targeted validation:
   - `uv run ruff check app/bigquery_export.py app/cli.py tests/test_bigquery_export.py`
   - `uv run mypy app/bigquery_export.py app/cli.py`
   - `uv run pytest -q tests/test_bigquery_export.py`
5. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- Targeted checks:
  - `uv run ruff check app/bigquery_export.py app/cli.py tests/test_bigquery_export.py`: PASS
  - `uv run mypy app/bigquery_export.py app/cli.py`: PASS
  - `uv run pytest -q tests/test_bigquery_export.py`: PASS (`3 passed`)
- Required gates:
  - `make dev-doctor`: PASS
  - `python scripts/harness.py lint`: PASS
  - `python scripts/harness.py typecheck`: PASS
  - `python scripts/harness.py test`: PASS (`84 passed, 3 skipped` in Python; `16 passed` in web Vitest)
  - `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- Direct BigQuery load requires `google-cloud-bigquery` to be installed in the runtime environment.
- Task #31 (`TASK_BIGQUERY_MODELS`) remains next in queue for raw→curated→marts docs and SQL examples.

## What’s next

- Commit `TASK_BIGQUERY_EXPORT` on this branch and open PR.
- Move to queue item #31: `TASK_BIGQUERY_MODELS`.

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-bigquery-models`
- Current task: `TASK_BIGQUERY_MODELS` (`agents/tasks/TASK_BIGQUERY_MODELS.md`)

## Task summary

Implemented Task #31 BigQuery modeling documentation + SQL examples:

- added new modeling guide `docs/BIGQUERY_MODELING.md` covering:
  - raw -> curated -> marts conventions
  - dataset naming and placeholder tokens
  - partitioning/clustering recommendations
  - operational execution order + lightweight data-quality checks
- added example SQL model set under `infra/bigquery_models/`:
  - `raw/` models for exported datasets (`docs`, `ingest_events`, `eval_runs`) plus optional query request logs source
  - `curated/` models for:
    - ingestion freshness
    - retrieval/query latency trends
    - eval pass rates over time
  - `marts/` models for:
    - weekly ops KPIs
    - governance inventory rollups
- added `infra/bigquery_models/README.md` for structure/context
- linked modeling docs from existing runbook/docs surfaces:
  - `docs/RUNBOOKS/BIGQUERY_EXPORT.md`
  - `README.md`
  - `docs/PRODUCT/PORTFOLIO_ALIGNMENT.md`
  - `CHANGELOG.md`

## Decisions made

- Kept this task doc-and-model only (no runtime/API changes) to preserve small, reviewable scope.
- Included a retrieval-latency curated model using request-log sink data as a practical latency proxy (`/api/query` and `/api/query/stream`).
- Used placeholder-based SQL templates (`{{PROJECT_ID}}`, datasets, table prefix) to stay warehouse-agnostic within BigQuery and avoid hard-coded env names.
- Maintained ADR guardrails by keeping all BigQuery modeling guidance private-deployment focused; no public-demo behavior changed.

## Files changed

- `docs/BIGQUERY_MODELING.md`
- `infra/bigquery_models/README.md`
- `infra/bigquery_models/raw/01_docs.sql`
- `infra/bigquery_models/raw/02_ingest_events.sql`
- `infra/bigquery_models/raw/03_eval_runs.sql`
- `infra/bigquery_models/raw/04_query_requests.sql`
- `infra/bigquery_models/curated/01_ingestion_freshness.sql`
- `infra/bigquery_models/curated/02_retrieval_latency.sql`
- `infra/bigquery_models/curated/03_eval_pass_rates.sql`
- `infra/bigquery_models/marts/01_ops_weekly_kpis.sql`
- `infra/bigquery_models/marts/02_governance_inventory.sql`
- `docs/RUNBOOKS/BIGQUERY_EXPORT.md`
- `README.md`
- `docs/PRODUCT/PORTFOLIO_ALIGNMENT.md`
- `CHANGELOG.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_BIGQUERY_MODELS.md`
   - `sed -n ... docs/SPECS/BIGQUERY_EXPORT.md`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git checkout -b codex/task-bigquery-models`
3. Discovery/implementation support:
   - `ls -la docs ...`
   - `find infra -maxdepth 3 -type d`
   - `sed -n ... docs/RUNBOOKS/BIGQUERY_EXPORT.md`
   - `sed -n ... docs/PRODUCT/PORTFOLIO_ALIGNMENT.md`
   - `rg -n ... app/main.py app/observability.py app/otel.py tests/test_otel.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`84 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- SQL files are intentionally templates with placeholders and no orchestration binding; client deployments should substitute tokens and schedule execution in their preferred tool.
- Retrieval latency model depends on Cloud Logging sink availability and request-log table mapping (`{{LOGS_DATASET}}.{{REQUEST_LOG_TABLE}}`).

## What’s next

- Commit `TASK_BIGQUERY_MODELS` on this branch and open PR.
- Move to queue item #32: `TASK_PWA`.

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-pwa`
- Current task: `TASK_PWA` (`agents/tasks/TASK_PWA.md`)

## Task summary

Completed Task #32 PWA hardening slice for offline-first UX, focusing on safe caching posture and operator/dev ergonomics:

- audited existing PWA implementation already present in `main` (manifest, icons, service worker registration, offline banners, offline page states, browser-local conversation persistence)
- hardened service worker API caching policy (`web/public/sw.js`):
  - bumped SW cache version to rotate prior broad API cache
  - restricted API cache to low-risk read endpoints only: `/api/meta`, `/api/docs`, `/api/stats`
  - kept `/api/query*` explicitly uncached
  - prevented silent undefined cache fallbacks by returning explicit rejected promises when offline and uncached
- added `make web-dev` alias (maps to Vite dev server) to align task/local-dev workflow wording
- updated tutorial offline section with explicit manual verification sequence and clarified cached API surface

## Decisions made

- Treated existing PWA base as already implemented and applied a minimal hardening diff rather than broad UI rewrites.
- Prioritized safety invariant from ADR/public-demo posture by avoiding persistence of sensitive/private API responses in service-worker cache.
- Kept network-first behavior only for allowlisted read endpoints; all other API routes now go direct-network only.
- Added `web-dev` alias instead of renaming existing `run-ui` target to preserve backward compatibility.

## Files changed

- `web/public/sw.js`
- `Makefile`
- `docs/TUTORIAL.md`
- `CHANGELOG.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... agents/tasks/TASK_PWA.md`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git branch -f codex/task-pwa main && git checkout codex/task-pwa`
3. Discovery/verification of existing implementation:
   - `rg -n "manifest|service worker|offline|navigator.onLine|..." web docs/TUTORIAL.md`
   - `sed -n ... web/public/manifest.webmanifest`
   - `sed -n ... web/public/sw.js`
   - `sed -n ... web/src/main.tsx`
   - `sed -n ... web/src/lib/offline.ts`
   - `sed -n ... web/src/pages/Home.tsx Docs.tsx Search.tsx`
4. Task-specific validation:
   - `make web-build`
5. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `make web-build`: PASS
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`84 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- Manual browser offline walkthrough was documented in `docs/TUTORIAL.md`; not executed inside this terminal-only environment.
- Existing PWA installability and offline banners were already present before this slice; this task primarily tightened caching safety and developer workflow clarity.

## What’s next

- Commit `TASK_PWA` on this branch and open PR.
- Move to queue item #33: `TASK_STREAMING`.

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-streaming`
- Current task: `TASK_STREAMING` (`agents/tasks/TASK_STREAMING.md`)

## Task summary

Completed Task #33 streaming closure pass with a minimal, reviewable delta focused on contract accuracy and SSE regression depth:

- updated streaming contract docs in `docs/CONTRACTS.md` to:
  - document optional `done.explain` parity with `POST /api/query`
  - explicitly state `done` is the terminal stream event (including refusal/internal-error paths)
- added tutorial guidance in `docs/TUTORIAL.md` for canceling active streams from the Ask UI
- strengthened streaming regression coverage in `tests/test_streaming.py`:
  - explicit event-order/terminal assertions for SSE response bodies
  - direct helper-level SSE frame test for `_sse_event(...)`
  - explicit `done.explain` assertions in success/refusal flows
- updated `CHANGELOG.md` entries for the contract clarification and streaming test hardening

## Decisions made

- Treated backend/API/UI streaming implementation already in `main` as baseline-complete and avoided broad refactors.
- Chose a focused docs+tests slice to satisfy task acceptance criteria while preserving existing behavior.
- Kept all public-demo invariants intact (no connector/upload changes; extractive-safe posture unchanged).

## Files changed

- `docs/CONTRACTS.md`
- `docs/TUTORIAL.md`
- `tests/test_streaming.py`
- `CHANGELOG.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status -sb`
   - `git branch -vv`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... harness.toml`
   - `sed -n ... agents/tasks/TASK_STREAMING.md`
   - `rg -n ... app web tests docs/CONTRACTS.md docs/TUTORIAL.md`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git branch -f codex/task-streaming main && git checkout codex/task-streaming`
3. Implementation + focused verification:
   - `uv run pytest -q tests/test_streaming.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `uv run pytest -q tests/test_streaming.py`: PASS (`4 passed`)
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`85 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- Numbered queue task #33 is now completed; all numbered items in `docs/BACKLOG/QUEUE.md` are addressed.
- Remaining task files are the unsequenced backlog set (not part of the numbered queue).

## What’s next

- Commit `TASK_STREAMING` on this branch and open PR.
- After merge, either stop at queue completion or start unsequenced tasks based on maintainer priority.

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-cloudsql`
- Current task: `TASK_CLOUDSQL` (`agents/tasks/TASK_CLOUDSQL.md`)

## Task summary

Completed a focused Cloud SQL hardening slice for deterministic migrations, retrieval-index verification, and pgvector contract clarity:

- added a CI-friendly migration runner unit test (`tests/test_postgres_migrations.py`) that verifies:
  - migration files are applied in filename order
  - `schema_migrations` tracking prevents re-applying already recorded files
- strengthened Docker Postgres integration test (`tests/test_cloudsql_postgres.py`) to assert:
  - all migration filenames are recorded in `schema_migrations`
  - required retrieval indexes exist: `idx_chunks_fts` (`GIN`) and `idx_embeddings_vec_hnsw` (`HNSW`, `vector_cosine_ops`)
- updated storage contract docs (`docs/CONTRACTS.md`) to explicitly document:
  - `DATABASE_URL` Postgres mode
  - pgvector requirement
  - startup migration tracking behavior
- updated Cloud SQL runbook (`docs/RUNBOOKS/CLOUDSQL.md`) with pgvector baseline and `schema_migrations` details
- updated changelog entries (`CHANGELOG.md`) for Cloud SQL task closure

## Decisions made

- Kept scope tightly focused on acceptance criteria instead of broad infra refactors (Cloud SQL Terraform path already hardened in prior tasks).
- Added one non-Docker unit test to guarantee migration determinism checks run in standard harness/CI lanes.
- Preserved ADR constraints: no public-demo safety regressions, no change to extractive-only demo defaults.

## Files changed

- `tests/test_postgres_migrations.py`
- `tests/test_cloudsql_postgres.py`
- `docs/CONTRACTS.md`
- `docs/RUNBOOKS/CLOUDSQL.md`
- `CHANGELOG.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status -sb`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... docs/PRODUCT/PRODUCT_BRIEF.md`
   - `sed -n ... docs/ARCHITECTURE/README.md`
   - `sed -n ... docs/DESIGN.md`
   - `sed -n ... docs/CONTRACTS.md`
   - `sed -n ... agents/tasks/TASK_CLOUDSQL.md`
   - `sed -n ... docs/SPECS/CLOUDSQL_HARDENING.md`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git branch -f codex/task-cloudsql main && git checkout codex/task-cloudsql`
3. Focused validation:
   - `uv run pytest -q tests/test_postgres_migrations.py tests/test_cloudsql_postgres.py`
   - `make test-postgres`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `uv run pytest -q tests/test_postgres_migrations.py tests/test_cloudsql_postgres.py`: PASS (`1 passed, 1 skipped`)
- `make test-postgres`: PASS (`1 skipped` in this environment; docker/psycopg-dependent integration lane)
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`86 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- Cloud SQL integration tests are still docker/psycopg-gated and may skip in environments lacking those dependencies.
- Migration determinism/tracking now has direct coverage in standard CI-compatible unit tests.

## What’s next

- Commit `TASK_CLOUDSQL` on this branch and open PR.
- Continue unsequenced backlog with `TASK_CONNECTORS_GCS` or another maintainer-selected task.

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-connectors-gcs`
- Current task: `TASK_CONNECTORS_GCS` (`agents/tasks/TASK_CONNECTORS_GCS.md`)

## Task summary

Completed a focused closure pass for GCS connector acceptance criteria by adding explicit safety/idempotency regression coverage and tightening contract docs:

- added connector sync API safety tests in `tests/test_connectors_gcs_sync_api.py` for:
  - public demo hard-disable behavior (`PUBLIC_DEMO_MODE=1` keeps connectors unreachable even if flag is set)
  - admin-only authorization requirement on `POST /api/connectors/gcs/sync`
  - `max_objects` validation bounds (`1..5000`) including acceptance of min/max limits
- strengthened idempotency verification in `tests/test_ingestion_runs.py`:
  - second rerun now asserts per-result `changed=false` and summary `changed=0`
- updated contracts documentation (`docs/CONTRACTS.md`) to explicitly codify:
  - `max_objects` allowed range
  - add/update-only connector behavior (no automatic deletes/tombstones)
- updated changelog (`CHANGELOG.md`) for task closure visibility

## Decisions made

- Kept implementation scope narrow because connector runtime logic and UI path were already implemented in prior tasks.
- Prioritized acceptance-criteria proof via tests instead of broad connector refactors.
- Preserved ADR safety posture: public-demo connectors remain disabled and sync semantics remain add/update only.

## Files changed

- `tests/test_connectors_gcs_sync_api.py`
- `tests/test_ingestion_runs.py`
- `docs/CONTRACTS.md`
- `CHANGELOG.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status -sb`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/*.md`
   - `sed -n ... agents/tasks/TASK_CONNECTORS_GCS.md`
   - `sed -n ... docs/SPECS/CONNECTOR_GCS_INGESTION.md`
   - `rg -n ... app tests web docs infra`
2. Branching:
   - `git checkout main && git pull --ff-only`
   - `git branch -f codex/task-connectors-gcs main && git checkout codex/task-connectors-gcs`
3. Focused validation:
   - `uv run pytest -q tests/test_connectors_gcs_sync_api.py tests/test_ingestion_runs.py`
4. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make backlog-audit`

## Validation results (summarized)

- `uv run pytest -q tests/test_connectors_gcs_sync_api.py tests/test_ingestion_runs.py`: PASS (`7 passed`)
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`89 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- Task validation step `make gcs-sync ...` was not executed in this local run because it requires a live private deployment API + GCS credentials/bucket; coverage is instead provided by deterministic API tests.

## What’s next

- Commit `TASK_CONNECTORS_GCS` on this branch and open PR.
- Continue with next unsequenced backlog task (`TASK_HYBRID_RETRIEVAL_TUNING` or maintainer-prioritized item).

---

## Session

- Date: 2026-02-22
- Agent: Codex
- Branch: `codex/task-hybrid-retrieval-tuning`
- Current task: `TASK_HYBRID_RETRIEVAL_TUNING` (`agents/tasks/TASK_HYBRID_RETRIEVAL_TUNING.md`)

## Task summary

Completed hybrid retrieval tuning hardening with deterministic ranking, runtime knobs, and diagnostics:

- added runtime retrieval knobs in `Settings`/env parsing:
  - `RETRIEVAL_LEXICAL_LIMIT`
  - `RETRIEVAL_VECTOR_LIMIT`
  - `RETRIEVAL_LEXICAL_WEIGHT`
  - `RETRIEVAL_VECTOR_WEIGHT`
  - `RETRIEVAL_DEBUG_STATS`
- implemented normalized hybrid weighting and deterministic tie-break ordering in retrieval paths (SQLite + Postgres)
- added optional retrieval diagnostics logging (candidate counts + stage latency breakdown) behind `RETRIEVAL_DEBUG_STATS`
- updated eval metadata to surface effective hybrid weights and retrieval candidate limits
- expanded `make test-postgres` to include runtime Postgres retrieval tests (`tests/test_cloudsql_runtime.py`)
- added regression tests in `tests/test_retrieval_tuning.py` for weight normalization/fallback, eval config wiring, and deterministic sort ordering

## Decisions made

- Kept hybrid merge formula aligned with architecture docs (`score = lexical_weight * lexical_score + vector_weight * vector_score`) and normalized weights at runtime.
- Enforced deterministic ordering using explicit tie-break fields (score, lexical, vector, doc/chunk identifiers) to avoid unstable ranking on equal scores.
- Made diagnostics log-only and opt-in (`RETRIEVAL_DEBUG_STATS=1`) to avoid changing API contracts while still supporting performance debugging.

## Files changed

- `.env.example`
- `Makefile`
- `app/config.py`
- `app/main.py`
- `app/retrieval.py`
- `tests/test_retrieval_tuning.py`
- `docs/ARCHITECTURE/RETRIEVAL_PIPELINE.md`
- `docs/CONTRACTS.md`
- `docs/TUTORIAL.md`
- `CHANGELOG.md`
- `docs/BACKLOG/EXECUTION_LOG.md`

## Commands run

1. Re-grounding/task intake:
   - `git status --short --branch`
   - `sed -n ... docs/BACKLOG/QUEUE.md`
   - `sed -n ... docs/BACKLOG/CODEX_PLAYBOOK.md`
   - `sed -n ... docs/BACKLOG/MILESTONES.md`
   - `sed -n ... docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`
   - `sed -n ... AGENTS.md`
   - `sed -n ... harness.toml`
   - `sed -n ... docs/PRODUCT/PRODUCT_BRIEF.md`
   - `sed -n ... docs/DESIGN.md`
   - `sed -n ... docs/WORKFLOW.md`
   - `sed -n ... agents/tasks/TASK_HYBRID_RETRIEVAL_TUNING.md`
   - `sed -n ... docs/SPECS/CLOUDSQL_HARDENING.md`
2. Focused validation:
   - `uv run ruff check app/config.py app/retrieval.py app/main.py tests/test_retrieval_tuning.py`
   - `uv run pytest -q tests/test_retrieval_tuning.py`
   - `uv run python -m app.cli eval data/eval/smoke.jsonl --k 5`
3. Full required validation:
   - `make dev-doctor`
   - `python scripts/harness.py lint`
   - `python scripts/harness.py typecheck`
   - `python scripts/harness.py test`
   - `make test-postgres`
   - `make backlog-audit`

## Validation results (summarized)

- `uv run ruff check ...`: PASS
- `uv run pytest -q tests/test_retrieval_tuning.py`: PASS (`3 passed`)
- `uv run python -m app.cli eval data/eval/smoke.jsonl --k 5`: PASS (`examples=3 hit@5=1.000 mrr=1.000`)
- `make dev-doctor`: PASS
- `python scripts/harness.py lint`: PASS
- `python scripts/harness.py typecheck`: PASS
- `python scripts/harness.py test`: PASS (`92 passed, 3 skipped` in Python; `16 passed` in web Vitest)
- `make test-postgres`: PASS (`2 skipped` in this local environment; Docker/psycopg-dependent)
- `make backlog-audit`: PASS (`OK`)

## Follow-up notes

- Retrieval smoke dataset (`data/eval/smoke.jsonl`) is now explicitly documented in tutorial/architecture as a lightweight ranking-regression guardrail.
- `make test-postgres` includes runtime retrieval coverage now; in CI with Docker + psycopg available this lane executes fully.

## What’s next

- Commit `TASK_HYBRID_RETRIEVAL_TUNING` on this branch and open PR.
- After merge, continue with the next unsequenced task by maintainer priority.
