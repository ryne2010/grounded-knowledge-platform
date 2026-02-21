import type { DocUpdateRequest } from '../api'

const TAG_RE = /[^a-z0-9:_\-]+/g
const MAX_TAGS = 20
const MAX_TAG_CHARS = 32

function normalizeTag(raw: string): string {
  return raw.toLowerCase().replace(TAG_RE, '-').replace(/^-+|-+$/g, '').slice(0, MAX_TAG_CHARS)
}

export function normalizeMetadataTags(raw: string): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  for (const token of raw.split(',')) {
    const normalized = normalizeTag(token.trim())
    if (!normalized || seen.has(normalized)) {
      continue
    }
    seen.add(normalized)
    out.push(normalized)
    if (out.length >= MAX_TAGS) {
      break
    }
  }
  return out
}

function normalizeAllowedValues(values: string[]): Set<string> {
  return new Set(values.map((value) => value.trim().toLowerCase()).filter(Boolean))
}

function humanList(values: string[]): string {
  return values.join(', ')
}

export function buildMetadataUpdatePayload(opts: {
  title: string
  source: string
  classification: string
  retention: string
  tagsRaw: string
  allowedClassifications: string[]
  allowedRetentions: string[]
}): { payload: DocUpdateRequest | null; normalizedTags: string[]; error: string | null } {
  const title = opts.title.trim()
  const source = opts.source.trim()
  const classification = opts.classification.trim().toLowerCase()
  const retention = opts.retention.trim().toLowerCase()

  if (!title) {
    return { payload: null, normalizedTags: [], error: 'Title is required.' }
  }
  if (!source) {
    return { payload: null, normalizedTags: [], error: 'Source is required.' }
  }

  const allowedClassifications = normalizeAllowedValues(opts.allowedClassifications)
  if (!allowedClassifications.has(classification)) {
    return {
      payload: null,
      normalizedTags: [],
      error: `Classification must be one of: ${humanList(Array.from(allowedClassifications))}.`,
    }
  }

  const allowedRetentions = normalizeAllowedValues(opts.allowedRetentions)
  if (!allowedRetentions.has(retention)) {
    return {
      payload: null,
      normalizedTags: [],
      error: `Retention must be one of: ${humanList(Array.from(allowedRetentions))}.`,
    }
  }

  const normalizedTags = normalizeMetadataTags(opts.tagsRaw)
  return {
    payload: {
      title,
      source,
      classification,
      retention,
      tags: normalizedTags,
    },
    normalizedTags,
    error: null,
  }
}

export function toActionableApiError(error: unknown): string {
  const raw = error instanceof Error ? error.message : String(error)
  const jsonStart = raw.indexOf('{')
  if (jsonStart >= 0) {
    try {
      const parsed = JSON.parse(raw.slice(jsonStart)) as { detail?: unknown }
      if (typeof parsed.detail === 'string' && parsed.detail.trim()) {
        return parsed.detail.trim()
      }
    } catch {
      // Fall through to raw message.
    }
  }
  const parts = raw.split(':')
  if (parts.length >= 3 && parts[0].includes('HTTP')) {
    return parts.slice(2).join(':').trim()
  }
  return raw.trim()
}
