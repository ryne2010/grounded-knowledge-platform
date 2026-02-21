import type { QueryCitation } from '../api'

export type CitationJump = {
  chunkId: string
  quote: string
  title: string
  source: string
  score: number | null
}

const PARAM_CHUNK = 'cite_chunk'
const PARAM_QUOTE = 'cite_quote'
const PARAM_TITLE = 'cite_title'
const PARAM_SOURCE = 'cite_source'
const PARAM_SCORE = 'cite_score'

function clean(value: string | null | undefined): string {
  return String(value ?? '').trim()
}

export function buildDocCitationHref(
  docId: string,
  citation: Pick<QueryCitation, 'chunk_id' | 'quote' | 'doc_title' | 'doc_source'>,
  score?: number,
): string {
  const params = new URLSearchParams()
  params.set(PARAM_CHUNK, citation.chunk_id)
  if (citation.quote?.trim()) params.set(PARAM_QUOTE, citation.quote.trim())
  if (citation.doc_title?.trim()) params.set(PARAM_TITLE, citation.doc_title.trim())
  if (citation.doc_source?.trim()) params.set(PARAM_SOURCE, citation.doc_source.trim())
  if (typeof score === 'number' && Number.isFinite(score)) {
    params.set(PARAM_SCORE, score.toFixed(3))
  }
  return `/docs/${encodeURIComponent(docId)}?${params.toString()}`
}

export function parseCitationJump(search: string): CitationJump | null {
  const params = new URLSearchParams(search)
  const chunkId = clean(params.get(PARAM_CHUNK))
  if (!chunkId) return null
  const rawScore = clean(params.get(PARAM_SCORE))
  const parsedScore = rawScore ? Number.parseFloat(rawScore) : Number.NaN

  return {
    chunkId,
    quote: clean(params.get(PARAM_QUOTE)),
    title: clean(params.get(PARAM_TITLE)),
    source: clean(params.get(PARAM_SOURCE)),
    score: Number.isFinite(parsedScore) ? parsedScore : null,
  }
}

export function scrollToCitationTarget(chunkId: string): boolean {
  const target = [...document.querySelectorAll<HTMLElement>('[data-citation-target]')].find(
    (node) => node.dataset.citationTarget === chunkId,
  )
  if (!target) return false

  if (!target.hasAttribute('tabindex')) {
    target.setAttribute('tabindex', '-1')
  }
  target.scrollIntoView({ behavior: 'smooth', block: 'center' })
  target.focus({ preventScroll: true })
  return true
}

export type HighlightSegment = {
  text: string
  match: boolean
}

export function buildCitationClipboardText(args: {
  quote: string
  docId: string
  title?: string | null
  source?: string | null
  chunkId?: string | null
}): string {
  const quote = clean(args.quote)
  const title = clean(args.title) || args.docId
  const source = clean(args.source)
  const chunkId = clean(args.chunkId)
  const lines = [`${quote}`, '', `— ${title}`, `doc_id: ${args.docId}`]
  if (source) lines.push(`source: ${source}`)
  if (chunkId) lines.push(`chunk_id: ${chunkId}`)
  return lines.join('\n')
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function buildHighlightSegments(text: string, snippet: string): HighlightSegment[] {
  const source = String(text ?? '')
  const needle = clean(snippet)
  if (!source || !needle) return [{ text: source, match: false }]

  const re = new RegExp(`(${escapeRegex(needle)})`, 'ig')
  const parts = source.split(re)
  if (parts.length <= 1) return [{ text: source, match: false }]
  return parts
    .filter((part) => part.length > 0)
    .map((part) => ({ text: part, match: part.toLowerCase() === needle.toLowerCase() }))
}
