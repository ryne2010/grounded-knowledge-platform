export type MetaResponse = {
  version?: string
  public_demo_mode: boolean
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

export type QueryResponse = {
  question: string
  answer: string
  refused: boolean
  refusal_reason: string | null
  provider: string
  citations: QueryCitation[]
  retrieval?: RetrievalDebug[]
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

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(path, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
    },
  })
  return res
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
    title?: string
    source?: string
    classification?: string
    retention?: string
    tags?: string
    notes?: string
  }) => {
    const form = new FormData()
    form.append('file', opts.file)
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

  runEval: (req: EvalRequest) => postJson<EvalRequest, EvalResponse>('/api/eval/run', req),
}
