import { describe, expect, it } from 'vitest'

import type { GcsSyncResponse, MetaResponse } from '../api'
import { getConnectorAvailability, summarizeGcsSyncRun } from './gcsConnector'

function meta(overrides: Partial<MetaResponse>): MetaResponse {
  return {
    public_demo_mode: false,
    uploads_enabled: true,
    connectors_enabled: true,
    eval_enabled: false,
    chunk_view_enabled: false,
    doc_delete_enabled: false,
    citations_required: true,
    max_upload_bytes: 10_000_000,
    max_top_k: 8,
    top_k_default: 5,
    llm_provider: 'extractive',
    embeddings_backend: 'hash',
    ocr_enabled: false,
    doc_classifications: ['public', 'internal', 'confidential', 'restricted'],
    doc_retentions: ['none', '30d', '90d', '1y', 'indefinite'],
    ...overrides,
  }
}

describe('getConnectorAvailability', () => {
  it('disables connectors in public demo mode with explicit message', () => {
    const out = getConnectorAvailability(meta({ public_demo_mode: true, connectors_enabled: false }))
    expect(out.enabled).toBe(false)
    expect(out.message).toContain('public demo mode')
  })

  it('disables connectors when ALLOW_CONNECTORS is off', () => {
    const out = getConnectorAvailability(meta({ public_demo_mode: false, connectors_enabled: false }))
    expect(out.enabled).toBe(false)
    expect(out.message).toContain('ALLOW_CONNECTORS=1')
  })

  it('enables connectors for private deployments when flag is on', () => {
    const out = getConnectorAvailability(meta({ public_demo_mode: false, connectors_enabled: true }))
    expect(out.enabled).toBe(true)
  })
})

describe('summarizeGcsSyncRun', () => {
  it('computes dry-run and changed/unchanged counters', () => {
    const run: GcsSyncResponse = {
      run_id: 'r1',
      started_at: 1,
      finished_at: 2,
      bucket: 'b',
      prefix: 'docs/',
      dry_run: false,
      max_objects: 200,
      scanned: 4,
      skipped_unsupported: 1,
      ingested: 3,
      changed: 1,
      results: [
        { gcs_uri: 'gs://b/docs/a.md', changed: true },
        { gcs_uri: 'gs://b/docs/b.md', changed: false },
        { gcs_uri: 'gs://b/docs/c.md', action: 'would_ingest' },
        { gcs_uri: 'gs://b/docs/d.md', error: 'download timeout' },
      ],
      errors: ['token expired'],
    }

    const out = summarizeGcsSyncRun(run)
    expect(out.scanned).toBe(4)
    expect(out.skippedUnsupported).toBe(1)
    expect(out.changed).toBe(1)
    expect(out.unchanged).toBe(1)
    expect(out.wouldIngest).toBe(1)
    expect(out.errors).toEqual(['gs://b/docs/d.md: download timeout', 'token expired'])
  })
})
