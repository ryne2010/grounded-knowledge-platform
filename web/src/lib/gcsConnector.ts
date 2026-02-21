import type { GcsSyncResponse, MetaResponse } from '../api'

export type ConnectorAvailability = {
  enabled: boolean
  message: string
}

export function getConnectorAvailability(meta?: MetaResponse): ConnectorAvailability {
  if (!meta) {
    return {
      enabled: false,
      message: 'Loading deployment configuration...',
    }
  }

  if (meta.public_demo_mode) {
    return {
      enabled: false,
      message: 'Connectors are disabled in public demo mode (read-only, demo corpus only).',
    }
  }

  if (!meta.connectors_enabled) {
    return {
      enabled: false,
      message: 'Connectors are disabled for this deployment. Set ALLOW_CONNECTORS=1 in private mode.',
    }
  }

  return {
    enabled: true,
    message: 'Run an add/update-only sync from a GCS prefix.',
  }
}

export type GcsSyncSummary = {
  scanned: number
  skippedUnsupported: number
  ingested: number
  changed: number
  unchanged: number
  wouldIngest: number
  errors: string[]
}

export function summarizeGcsSyncRun(run: GcsSyncResponse): GcsSyncSummary {
  let unchanged = 0
  let wouldIngest = 0
  const errors: string[] = []

  for (const row of run.results ?? []) {
    if (row.action === 'would_ingest') {
      wouldIngest += 1
    }

    if (row.changed === false) {
      unchanged += 1
    }

    if (typeof row.error === 'string' && row.error.trim()) {
      errors.push(`${row.gcs_uri}: ${row.error.trim()}`)
    }
  }

  for (const err of run.errors ?? []) {
    const normalized = String(err || '').trim()
    if (normalized) {
      errors.push(normalized)
    }
  }

  return {
    scanned: Number(run.scanned || 0),
    skippedUnsupported: Number(run.skipped_unsupported || 0),
    ingested: Number(run.ingested || 0),
    changed: Number(run.changed || 0),
    unchanged,
    wouldIngest,
    errors,
  }
}
