export type Meta = {
  public_demo_mode: boolean
  uploads_enabled: boolean
  eval_enabled: boolean
  llm_provider: string
  embeddings_backend: string
  ocr_enabled: boolean
}

export type Doc = {
  doc_id: string
  title: string
  source: string
  created_at: number
}

export type QueryCitation = {
  chunk_id: string
  doc_id: string
  idx: number
  quote?: string
}

export type QueryResponse = {
  question: string
  answer: string
  refused: boolean
  refusal_reason?: string | null
  provider: string
  citations: QueryCitation[]
  retrieval?: Array<{
    chunk_id: string
    doc_id: string
    idx: number
    score: number
    lexical_score: number | null
    vector_score: number | null
    text_preview: string
    text?: string
  }>
}

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...(init?.headers || {}),
    },
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Request failed: ${res.status}`)
  }
  return (await res.json()) as T
}

export const api = {
  meta: () => jsonFetch<Meta>('/api/meta'),
  docs: () => jsonFetch<{ docs: Doc[] }>('/api/docs'),
  query: (payload: { question: string; top_k: number; debug: boolean }) =>
    jsonFetch<QueryResponse>('/api/query', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
}
