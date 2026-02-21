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
