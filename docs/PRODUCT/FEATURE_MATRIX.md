# Feature matrix

This matrix defines what is allowed in the **public demo** vs **private deployments**.

Source of truth for the posture: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

| Capability | Public demo (anonymous) | Private deployment (per-client) |
|---|---|---|
| Ask questions | ✅ Yes | ✅ Yes |
| Citations required | ✅ Forced on | ✅ Default on (recommended) |
| Answering mode | ✅ **Extractive only** | ✅ Extractive by default; optional LLM providers behind auth |
| View docs list/detail | ✅ Yes | ✅ Yes |
| View full chunk text | ❌ Disabled | ✅ Optional (`ALLOW_CHUNK_VIEW=1`) |
| Delete docs | ❌ Disabled | ✅ Optional (`ALLOW_DOC_DELETE=1`, admin) |
| Upload files / paste text | ❌ Disabled | ✅ Optional (`ALLOW_UPLOADS=1`, editor/admin) |
| Demo corpus bootstrap | ✅ Yes (`data/demo_corpus/`) | ⚠️ Optional |
| Connectors (GCS sync) | ❌ Disabled | ✅ Optional (`ALLOW_CONNECTORS=1`, admin) |
| Connector behavior | N/A | ✅ **Add/update only** (no deletions) |
| Event-driven ingestion (Pub/Sub push) | ❌ Disabled | ✅ Planned (optional) |
| Scheduled sync (Cloud Scheduler) | ❌ Disabled | ✅ Planned (optional) |
| Tabular contracts validation | ✅ Read-only (docs only) | ✅ Optional on ingest (CSV/TSV/XLSX) |
| Schema drift capture | ✅ Read-only | ✅ Captured on ingest; operator-visible |
| Ingest lineage events | ✅ Read-only | ✅ Visible (and expandable) |
| Replay/backfill tooling | ❌ Disabled | ✅ Planned (CLI + runbook) |
| Eval harness (run) | ❌ Disabled | ✅ Optional (`ALLOW_EVAL=1`, admin) |
| Persist eval runs | ❌ Disabled | ✅ Planned |
| Auth | ❌ None | ✅ Recommended (`AUTH_MODE=api_key`) |
| Rate limiting | ✅ Enabled | ✅ Optional |
| Observability (logs/metrics) | ✅ Basic | ✅ Expanded (OTEL, dashboards, SLOs) |
| BigQuery export | ❌ Disabled | ✅ Planned |

## Notes

- The public demo is designed to be safe and cheap to host: no uploads, no connectors, no eval endpoints.
- Private deployments can enable richer features behind auth, but should retain citations-required defaults.
