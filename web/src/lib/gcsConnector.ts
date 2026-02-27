import type { GcsSyncResponse, MetaResponse } from '../api'

export type ConnectorAvailability = {
  enabled: boolean
  message: string
}

export type ParsedGcsDirectoryLink = {
  bucket: string
  prefix: string
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

export function parseGcsDirectoryLink(raw: string): ParsedGcsDirectoryLink {
  const input = String(raw || '').trim()
  if (!input) {
    throw new Error('Directory link is required.')
  }
  if (!input.startsWith('gs://')) {
    throw new Error('Directory link must start with gs://')
  }

  const rest = input.slice('gs://'.length)
  const slash = rest.indexOf('/')
  const bucket = (slash === -1 ? rest : rest.slice(0, slash)).trim()
  if (!bucket) {
    throw new Error('Directory link must include a bucket.')
  }
  if (/\s/.test(bucket)) {
    throw new Error('Directory link bucket is invalid.')
  }

  const rawPrefix = slash === -1 ? '' : rest.slice(slash + 1)
  const prefix = rawPrefix.replace(/^\/+/, '').replace(/\/+$/, '').trim()
  return { bucket, prefix }
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
