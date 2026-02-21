export type MetaResponse = {
  version?: string
  public_demo_mode: boolean
  auth_mode?: string
  database_backend?: string
  uploads_enabled: boolean
  eval_enabled: boolean
  chunk_view_enabled: boolean
  doc_delete_enabled: boolean
  citations_required: boolean
  rate_limit_enabled?: boolean
  rate_limit_scope?: string
  rate_limit_window_s?: number
  rate_limit_max_requests?: number
  api_docs_url?: string
  max_upload_bytes: number
  max_top_k: number
  top_k_default: number
  max_question_chars?: number
  llm_provider: string
  embeddings_backend: string
  ocr_enabled: boolean
  stats?: { docs: number; chunks: number; embeddings: number }
  index_signature?: Record<string, string | null>
  doc_classifications: string[]
  doc_retentions: string[]
}

export type Doc = {
  doc_id: string
  title: string
  source: string
  classification: string
  retention: string
  tags: string[]
  content_sha256: string | null
  content_bytes: number
  num_chunks: number
  doc_version: number
  created_at: number
  updated_at: number
}

export type DocsResponse = {
  docs: Doc[]
}

export type IngestEvent = {
  event_id: string
  doc_id: string
  doc_version: number
  ingested_at: number
  content_sha256: string
  prev_content_sha256: string | null
  changed: boolean
  num_chunks: number
  embedding_backend: string
  embeddings_model: string
  embedding_dim: number
  chunk_size_chars: number
  chunk_overlap_chars: number
  schema_fingerprint?: string | null
  contract_sha256?: string | null
  validation_status?: 'pass' | 'warn' | 'fail' | null
  validation_errors?: string[]
  schema_drifted?: boolean
  notes: string | null
}


export type IngestEventView = IngestEvent & {
  doc_title: string
  doc_source: string
  classification: string
  retention: string
  tags: string[]
}

export type IngestEventsResponse = {
  events: IngestEventView[]
}

export type DocDetailResponse = {
  doc: Doc
  ingest_events: IngestEvent[]
}

export type DocUpdateRequest = {
  title?: string
  source?: string
  classification?: string
  retention?: string
  tags?: string[]
}

export type DocUpdateResponse = {
  doc: Doc
}

export type ChunkSummary = {
  chunk_id: string
  doc_id: string
  idx: number
  text_preview: string
}

export type DocChunksResponse = {
  doc: Doc
  chunks: ChunkSummary[]
  limit: number
  offset: number
}

export type ChunkDetail = {
  chunk_id: string
  doc_id: string
  idx: number
  text: string
  doc_title: string | null
  doc_source: string | null
}

export type ChunkDetailResponse = {
  chunk: ChunkDetail
}

export type IngestTextRequest = {
  title: string
  source: string
  text: string
  doc_id?: string
  classification?: string
  retention?: string
  tags?: string[]
  notes?: string
}

export type IngestResponse = {
  doc_id: string
  doc_version: number
  changed: boolean
  num_chunks: number
  embedding_dim: number
  content_sha256: string
}

export type QueryCitation = {
  chunk_id: string
  doc_id: string
  idx: number
  quote: string
  doc_title: string | null
  doc_source: string | null
  doc_version: number | null
}

export type RetrievalDebug = {
  chunk_id: string
  doc_id: string
  idx: number
  score: number
  lexical_score: number
  vector_score: number
  text_preview: string
  text?: string
}

export type QueryExplainEvidence = {
  doc_id: string
  doc_title: string | null
  doc_source: string | null
  snippet: string
  selected: boolean
  why_selected: string
  chunk_id?: string
  idx?: number
  score?: number
  lexical_score?: number
  vector_score?: number
}

export type QueryExplain = {
  question: string
  evidence_used: QueryExplainEvidence[]
  how_retrieval_works: {
    summary: string
    top_k: number
    retrieved_chunks: number
    public_demo_mode: boolean
    debug_details_included: boolean
  }
  refusal: {
    refused: boolean
    code: string | null
    category: string | null
    message: string
  }
}

export type QueryResponse = {
  question: string
  answer: string
  refused: boolean
  refusal_reason: string | null
  provider: string
  citations: QueryCitation[]
  retrieval?: RetrievalDebug[]
  explain?: QueryExplain
}

export type QueryStreamDone = {
  question: string
  answer: string
  refused: boolean
  refusal_reason: string | null
  provider: string
  explain?: QueryExplain
}

export type QueryStreamHandlers = {
  onRetrieval?: (rows: RetrievalDebug[]) => void
  onToken?: (text: string) => void
  onCitations?: (citations: QueryCitation[]) => void
  onExplain?: (explain: QueryExplain) => void
  onDone?: (done: QueryStreamDone) => void
  onError?: (message: string) => void
}

export type EvalRequest = {
  golden_path: string
  k: number
  include_details?: boolean
}

export type EvalRetrieved = {
  chunk_id: string
  doc_id: string
  idx: number
  score: number
  lexical_score: number
  vector_score: number
  text_preview: string
}

export type EvalExample = {
  question: string
  expected_doc_ids: string[]
  expected_chunk_ids: string[]
  hit: boolean
  rank: number | null
  rr: number
  retrieved: EvalRetrieved[]
}

export type EvalResponse = {
  examples: number
  hit_at_k: number
  mrr: number
  details?: EvalExample[]
}

export type ChunkSearchResult = {
  chunk_id: string
  doc_id: string
  idx: number
  score: number | null
  text_preview: string
  doc_title: string
  doc_source: string
  classification: string
  tags: string[]
}

export type ChunkSearchResponse = {
  query: string
  results: ChunkSearchResult[]
}

export type TopTagStat = {
  tag: string
  count: number
}

export type StatsResponse = {
  docs: number
  chunks: number
  embeddings: number
  ingest_events: number
  by_classification: Record<string, number>
  by_retention: Record<string, number>
  top_tags: TopTagStat[]
}

export type ExpiredDoc = {
  doc_id: string
  title: string
  retention: string
  updated_at: number
}

export type ExpiredDocsResponse = {
  now: number
  expired: ExpiredDoc[]
}

const OFFLINE_EVENT = 'gkp:network-offline'
const ONLINE_EVENT = 'gkp:network-online'

function dispatchNetworkEvent(name: string) {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(name))
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  try {
    const res = await fetch(path, {
      ...init,
      headers: {
        ...(init?.headers ?? {}),
      },
    })
    dispatchNetworkEvent(ONLINE_EVENT)
    return res
  } catch (e) {
    dispatchNetworkEvent(OFFLINE_EVENT)
    throw e
  }
}

function formatHttpError(res: Response, bodyText: string): string {
  const reqId = res.headers.get('x-request-id')
  const prefix = reqId ? `[req ${reqId}] ` : ''
  return `${prefix}HTTP ${res.status}: ${bodyText}`
}

async function getJson<T>(path: string): Promise<T> {
  const res = await apiFetch(path)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(formatHttpError(res, text))
  }
  return (await res.json()) as T
}

async function postJson<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const res = await apiFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(formatHttpError(res, text))
  }
  return (await res.json()) as TRes
}

async function patchJson<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const res = await apiFetch(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(formatHttpError(res, text))
  }
  return (await res.json()) as TRes
}

function parseSseEvents(chunk: string): Array<{ event: string; data: string }> {
  const out: Array<{ event: string; data: string }> = []
  const blocks = chunk.split('\n\n')
  for (const block of blocks) {
    const trimmed = block.trim()
    if (!trimmed) continue
    let event = 'message'
    const dataLines: string[] = []
    for (const line of trimmed.split('\n')) {
      if (line.startsWith('event:')) {
        event = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trim())
      }
    }
    out.push({ event, data: dataLines.join('\n') })
  }
  return out
}

export const api = {
  meta: () => getJson<MetaResponse>('/api/meta'),

  stats: () => getJson<StatsResponse>('/api/stats'),

  maintenanceRetentionExpired: (now?: number) => {
    const qs = new URLSearchParams()
    if (typeof now === 'number') qs.set('now', String(now))
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return getJson<ExpiredDocsResponse>(`/api/maintenance/retention/expired${suffix}`)
  },

  listDocs: () => getJson<DocsResponse>('/api/docs'),

  listIngestEvents: (limit = 100, docId?: string) => {
    const qs = new URLSearchParams({ limit: String(limit) })
    if (docId) qs.set('doc_id', docId)
    return getJson<IngestEventsResponse>(`/api/ingest/events?${qs.toString()}`)
  },

  searchChunks: (q: string, limit = 20) =>
    getJson<ChunkSearchResponse>(
      `/api/search/chunks?q=${encodeURIComponent(q)}&limit=${encodeURIComponent(String(limit))}`,
    ),

  docDetail: (docId: string) => getJson<DocDetailResponse>(`/api/docs/${encodeURIComponent(docId)}`),

  updateDoc: (docId: string, req: DocUpdateRequest) =>
    patchJson<DocUpdateRequest, DocUpdateResponse>(`/api/docs/${encodeURIComponent(docId)}`, req),

  docChunks: (docId: string, limit = 200, offset = 0) =>
    getJson<DocChunksResponse>(
      `/api/docs/${encodeURIComponent(docId)}/chunks?limit=${encodeURIComponent(String(limit))}&offset=${encodeURIComponent(
        String(offset),
      )}`,
    ),

  chunkDetail: (chunkId: string) =>
    getJson<ChunkDetailResponse>(`/api/chunks/${encodeURIComponent(chunkId)}`),

  docText: async (docId: string) => {
    const res = await apiFetch(`/api/docs/${encodeURIComponent(docId)}/text`)
    if (!res.ok) {
      const text = await res.text()
      throw new Error(formatHttpError(res, text))
    }
    return await res.text()
  },

  deleteDoc: async (docId: string) => {
    const res = await apiFetch(`/api/docs/${encodeURIComponent(docId)}`, { method: 'DELETE' })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(formatHttpError(res, text))
    }
    return (await res.json()) as { deleted: boolean; doc_id: string }
  },

  ingestText: (req: IngestTextRequest) => postJson<IngestTextRequest, IngestResponse>('/api/ingest/text', req),

  ingestFile: async (opts: {
    file: File
    contractFile?: File
    title?: string
    source?: string
    classification?: string
    retention?: string
    tags?: string
    notes?: string
  }) => {
    const form = new FormData()
    form.append('file', opts.file)
    if (opts.contractFile) form.append('contract_file', opts.contractFile)
    if (opts.title) form.append('title', opts.title)
    if (opts.source) form.append('source', opts.source)
    if (opts.classification) form.append('classification', opts.classification)
    if (opts.retention) form.append('retention', opts.retention)
    if (opts.tags) form.append('tags', opts.tags)
    if (opts.notes) form.append('notes', opts.notes)

    const res = await apiFetch('/api/ingest/file', {
      method: 'POST',
      body: form,
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(formatHttpError(res, text))
    }
    return (await res.json()) as IngestResponse
  },

  query: (question: string, top_k = 5, debug = false) =>
    postJson<{ question: string; top_k: number; debug: boolean }, QueryResponse>('/api/query', {
      question,
      top_k,
      debug,
    }),

  queryStream: async (
    question: string,
    top_k = 5,
    handlers: QueryStreamHandlers = {},
    signal?: AbortSignal,
  ): Promise<QueryResponse> => {
    const res = await apiFetch('/api/query/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k }),
      signal,
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(formatHttpError(res, text))
    }
    if (!res.body) {
      throw new Error('Streaming not supported by this browser')
    }

    const decoder = new TextDecoder()
    const reader = res.body.getReader()
    let buffer = ''

    let answer = ''
    let citations: QueryCitation[] = []
    let retrieval: RetrievalDebug[] | undefined
    let explain: QueryExplain | undefined
    let done: QueryStreamDone | null = null

    while (true) {
      const { value, done: doneReading } = await reader.read()
      if (doneReading) break
      buffer += decoder.decode(value, { stream: true })
      const boundary = buffer.lastIndexOf('\n\n')
      if (boundary < 0) continue

      const ready = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      const events = parseSseEvents(ready)

      for (const evt of events) {
        let parsed: any = {}
        try {
          parsed = evt.data ? JSON.parse(evt.data) : {}
        } catch {
          parsed = {}
        }

        if (evt.event === 'retrieval') {
          retrieval = Array.isArray(parsed) ? (parsed as RetrievalDebug[]) : []
          handlers.onRetrieval?.(retrieval)
          continue
        }
        if (evt.event === 'token') {
          const token = String(parsed?.text ?? '')
          answer += (answer ? ' ' : '') + token
          handlers.onToken?.(token)
          continue
        }
        if (evt.event === 'citations') {
          citations = Array.isArray(parsed) ? (parsed as QueryCitation[]) : []
          handlers.onCitations?.(citations)
          continue
        }
        if (evt.event === 'explain') {
          if (parsed && typeof parsed === 'object') {
            explain = parsed as QueryExplain
            handlers.onExplain?.(explain)
          }
          continue
        }
        if (evt.event === 'done') {
          const doneExplain = parsed?.explain && typeof parsed.explain === 'object'
            ? (parsed.explain as QueryExplain)
            : undefined
          if (doneExplain) {
            explain = doneExplain
            handlers.onExplain?.(doneExplain)
          }
          done = {
            question: String(parsed?.question ?? question),
            answer: String(parsed?.answer ?? answer),
            refused: Boolean(parsed?.refused),
            refusal_reason: parsed?.refusal_reason ?? null,
            provider: String(parsed?.provider ?? 'unknown'),
            explain: doneExplain ?? explain,
          }
          handlers.onDone?.(done)
          continue
        }
        if (evt.event === 'error') {
          handlers.onError?.(String(parsed?.message ?? 'stream error'))
        }
      }
    }

    if (buffer.trim()) {
      const tailEvents = parseSseEvents(buffer)
      for (const evt of tailEvents) {
        let parsed: any = {}
        try {
          parsed = evt.data ? JSON.parse(evt.data) : {}
        } catch {
          parsed = {}
        }
        if (evt.event === 'done') {
          const doneExplain = parsed?.explain && typeof parsed.explain === 'object'
            ? (parsed.explain as QueryExplain)
            : undefined
          if (doneExplain) {
            explain = doneExplain
          }
          done = {
            question: String(parsed?.question ?? question),
            answer: String(parsed?.answer ?? answer),
            refused: Boolean(parsed?.refused),
            refusal_reason: parsed?.refusal_reason ?? null,
            provider: String(parsed?.provider ?? 'unknown'),
            explain: doneExplain ?? explain,
          }
        } else if (evt.event === 'citations' && Array.isArray(parsed)) {
          citations = parsed as QueryCitation[]
        } else if (evt.event === 'retrieval' && Array.isArray(parsed)) {
          retrieval = parsed as RetrievalDebug[]
        } else if (evt.event === 'explain' && parsed && typeof parsed === 'object') {
          explain = parsed as QueryExplain
        }
      }
    }

    if (!done) {
      done = {
        question,
        answer,
        refused: false,
        refusal_reason: null,
        provider: 'unknown',
        explain,
      }
    }

    return {
      question: done.question,
      answer: done.answer || answer,
      refused: done.refused,
      refusal_reason: done.refusal_reason,
      provider: done.provider,
      citations,
      retrieval,
      explain: done.explain ?? explain,
    }
  },

  runEval: (req: EvalRequest) => postJson<EvalRequest, EvalResponse>('/api/eval/run', req),
}
