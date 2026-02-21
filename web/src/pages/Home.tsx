import * as React from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'

import { api, type Doc, type QueryResponse, type RetrievalDebug } from '../api'
import { buildCitationClipboardText, buildDocCitationHref } from '../lib/citations'
import { useOfflineStatus } from '../lib/offline'
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Checkbox,
  DataTable,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Label,
  Page,
  RangeSlider,
  Separator,
  Textarea,
} from '../portfolio-ui'

const FALLBACK_EXAMPLES = [
  "Summarize this platform's safety and evidence guarantees.",
  'How does hybrid retrieval (BM25 + embeddings) work in this system?',
  'What architecture choices improve reliability on Cloud Run?',
  'What controls mitigate prompt injection in enterprise deployments?',
]

function _docLabel(doc: Doc): string {
  const title = doc.title?.trim()
  if (title) return title
  const source = doc.source?.trim()
  if (source) return source
  return doc.doc_id
}

function buildCorpusExamples(docs: Doc[]): string[] {
  if (!docs.length) return FALLBACK_EXAMPLES

  const ranked = [...docs]
    .sort((a, b) => (b.updated_at - a.updated_at) || (b.content_bytes - a.content_bytes))
    .slice(0, 4)

  const examples: string[] = []
  const seen = new Set<string>()

  const push = (q: string) => {
    const normalized = q.trim()
    if (!normalized || seen.has(normalized)) return
    seen.add(normalized)
    examples.push(normalized)
  }

  for (const doc of ranked) {
    const label = _docLabel(doc)
    push(`Summarize the key engineering guidance in "${label}".`)
  }

  if (ranked.length >= 2) {
    const a = _docLabel(ranked[0])
    const b = _docLabel(ranked[1])
    push(`Compare the recommendations in "${a}" and "${b}".`)
  }

  const tagCounts = new Map<string, number>()
  for (const doc of docs) {
    for (const raw of doc.tags ?? []) {
      const tag = String(raw || '').trim().toLowerCase()
      if (!tag) continue
      tagCounts.set(tag, (tagCounts.get(tag) ?? 0) + 1)
    }
  }
  const topTag = [...tagCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0]
  if (topTag) {
    push(`What does this corpus say about ${topTag.replace(/[-_]+/g, ' ')}?`)
  }

  if (!examples.length) return FALLBACK_EXAMPLES
  return examples.slice(0, 6)
}

type ChatTurn = {
  id: string
  created_at: string
  question: string
  top_k: number
  debug: boolean
  response?: QueryResponse
  error?: string
}

const STORAGE_KEY = 'gkp.chat.v1'
const MAX_TURNS = 20

function loadTurns(): ChatTurn[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed as ChatTurn[]
  } catch {
    return []
  }
}

function saveTurns(turns: ChatTurn[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(turns))
  } catch {
    // Ignore storage failures (private browsing, quota, etc.)
  }
}

function exportTurnsMarkdown(turns: ChatTurn[]): string {
  const lines: string[] = []
  lines.push('# Grounded Knowledge Platform — Conversation Export')
  lines.push('')
  lines.push(`Exported: ${new Date().toISOString()}`)
  lines.push('')

  const ordered = [...turns].sort((a, b) => a.created_at.localeCompare(b.created_at))
  for (const t of ordered) {
    lines.push('---')
    lines.push('')
    lines.push(`## Q: ${t.question}`)
    lines.push('')

    if (t.error) {
      lines.push(`**Error:** ${t.error}`)
      lines.push('')
      continue
    }

    const ans = t.response?.answer
    if (!ans) {
      lines.push('_No answer captured._')
      lines.push('')
      continue
    }

    lines.push(ans)
    lines.push('')

    if (t.response?.refused && t.response?.refusal_reason) {
      lines.push(`> Refusal reason: \`${t.response.refusal_reason}\``)
      lines.push('')
    }

    const citations = t.response?.citations ?? []
    if (citations.length) {
      lines.push('### Citations')
      lines.push('')
      for (const c of citations) {
        const title = c.doc_title ?? c.doc_id
        const source = c.doc_source ? ` (${c.doc_source})` : ''
        lines.push(`- **${title}**${source}`)
        if (c.quote) {
          lines.push(`  - Quote: “${c.quote.replace(/\n+/g, ' ').trim()}”`)
        }
      }
      lines.push('')
    }

    const retrieval = t.response?.retrieval ?? []
    if (retrieval.length) {
      lines.push(`_Retrieval debug: ${retrieval.length} chunks returned._`)
      lines.push('')
    }
  }

  return lines.join('\n')
}

function downloadText(filename: string, text: string) {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export function HomePage() {
  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: 30_000 })
  const docsQuery = useQuery({ queryKey: ['docs'], queryFn: api.listDocs, staleTime: 30_000 })
  const meta = metaQuery.data

  const docsById = React.useMemo(() => {
    const m = new Map<string, { title: string; source: string }>()
    for (const d of docsQuery.data?.docs ?? []) {
      m.set(d.doc_id, { title: d.title ?? d.doc_id, source: d.source ?? '' })
    }
    return m
  }, [docsQuery.data])

  const retrievalColumns = React.useMemo(
    () => [
      {
        header: 'Doc',
        accessorKey: 'doc_id',
        cell: (info: any) => {
          const r = info.row.original as RetrievalDebug
          const d = docsById.get(r.doc_id)
          const title = d?.title ?? r.doc_id
          const source = d?.source ?? ''
          return (
            <div className="space-y-1">
              <div className="font-medium">
                <Link to="/docs/$docId" params={{ docId: r.doc_id }} className="hover:underline">
                  {title}
                </Link>
              </div>
              {source ? <div className="text-xs text-muted-foreground">{source}</div> : null}
            </div>
          )
        },
        meta: { minWidth: 220, maxWidth: 320 },
      },
      {
        header: 'Chunk',
        accessorKey: 'idx',
        cell: (info: any) => {
          const r = info.row.original as RetrievalDebug
          return (
            <div className="space-y-1">
              <div className="font-mono text-xs">#{r.idx}</div>
              <div className="font-mono text-[11px] text-muted-foreground">{r.chunk_id.slice(0, 10)}…</div>
            </div>
          )
        },
        meta: { width: 110 },
      },
      {
        header: 'Score',
        accessorKey: 'score',
        cell: (info: any) => <span className="font-mono text-xs">{Number(info.getValue() ?? 0).toFixed(3)}</span>,
        meta: { width: 90 },
      },
      {
        header: 'Lex',
        accessorKey: 'lexical_score',
        cell: (info: any) => <span className="font-mono text-xs">{Number(info.getValue() ?? 0).toFixed(3)}</span>,
        meta: { width: 80 },
      },
      {
        header: 'Vec',
        accessorKey: 'vector_score',
        cell: (info: any) => <span className="font-mono text-xs">{Number(info.getValue() ?? 0).toFixed(3)}</span>,
        meta: { width: 80 },
      },
      {
        header: 'Preview',
        accessorKey: 'text_preview',
        cell: (info: any) => <div className="whitespace-pre-wrap text-xs">{String(info.getValue() ?? '')}</div>,
        meta: { minWidth: 420 },
      },
    ],
    [docsById],
  )

  const [question, setQuestion] = React.useState('')
  const [topK, setTopK] = React.useState(5)
  const [debug, setDebug] = React.useState(false)
  const [useStreaming, setUseStreaming] = React.useState(true)
  const [streamingTurnId, setStreamingTurnId] = React.useState<string | null>(null)
  const streamAbortRef = React.useRef<AbortController | null>(null)
  const toastTimeoutRef = React.useRef<number | null>(null)
  const offline = useOfflineStatus()

  const [turns, setTurns] = React.useState<ChatTurn[]>(() => (typeof window === 'undefined' ? [] : loadTurns()))
  const [toastMessage, setToastMessage] = React.useState<string | null>(null)

  const showToast = React.useCallback((message: string) => {
    setToastMessage(message)
    if (toastTimeoutRef.current != null) {
      window.clearTimeout(toastTimeoutRef.current)
    }
    toastTimeoutRef.current = window.setTimeout(() => {
      setToastMessage(null)
      toastTimeoutRef.current = null
    }, 2500)
  }, [])

  const suggestedQuestions = React.useMemo(() => {
    const docs = docsQuery.data?.docs ?? []
    return buildCorpusExamples(docs)
  }, [docsQuery.data])

  React.useEffect(() => {
    if (meta?.top_k_default && Number.isFinite(meta.top_k_default)) {
      setTopK(meta.top_k_default)
    }
  }, [meta?.top_k_default])

  React.useEffect(() => {
    saveTurns(turns)
  }, [turns])

  React.useEffect(
    () => () => {
      if (toastTimeoutRef.current != null) {
        window.clearTimeout(toastTimeoutRef.current)
      }
    },
    [],
  )

  const queryMutation = useMutation({
    mutationFn: (vars: { question: string; top_k: number; debug: boolean }) =>
      api.query(vars.question, vars.top_k, vars.debug),
  })

  async function onAsk() {
    const q = question.trim()
    if (!q) return

    const id = crypto.randomUUID()
    const created_at = new Date().toISOString()

    const next: ChatTurn = {
      id,
      created_at,
      question: q,
      top_k: topK,
      debug,
    }

    setTurns((prev) => [...prev, next].slice(-MAX_TURNS))

    if (useStreaming) {
      const controller = new AbortController()
      streamAbortRef.current = controller
      setStreamingTurnId(id)
      setTurns((prev) =>
        prev.map((t) =>
          t.id === id
            ? {
                ...t,
                response: {
                  question: q,
                  answer: '',
                  refused: false,
                  refusal_reason: null,
                  provider: 'stream',
                  citations: [],
                  retrieval: [],
                },
              }
            : t,
        ),
      )

      try {
        const res = await api.queryStream(
          q,
          topK,
          {
            onRetrieval: (rows) => {
              setTurns((prev) =>
                prev.map((t) =>
                  t.id === id && t.response
                    ? {
                        ...t,
                        response: { ...t.response, retrieval: rows },
                      }
                    : t,
                ),
              )
            },
            onToken: (token) => {
              setTurns((prev) =>
                prev.map((t) =>
                  t.id === id && t.response
                    ? {
                        ...t,
                        response: {
                          ...t.response,
                          answer: `${t.response.answer}${t.response.answer ? ' ' : ''}${token}`,
                        },
                      }
                    : t,
                ),
              )
            },
            onCitations: (citations) => {
              setTurns((prev) =>
                prev.map((t) =>
                  t.id === id && t.response
                    ? {
                        ...t,
                        response: { ...t.response, citations },
                      }
                    : t,
                ),
              )
            },
          },
          controller.signal,
        )
        setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, response: res } : t)))
      } catch (e: unknown) {
        if ((e as Error)?.name === 'AbortError') {
          setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, error: 'Canceled' } : t)))
        } else {
          const msg = e instanceof Error ? e.message : String(e)
          setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, error: msg } : t)))
        }
      } finally {
        streamAbortRef.current = null
        setStreamingTurnId(null)
      }
      return
    }

    try {
      const res = await queryMutation.mutateAsync({ question: q, top_k: topK, debug })
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, response: res } : t)))
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, error: msg } : t)))
    }
  }

  const maxTopK = typeof meta?.max_top_k === 'number' ? meta.max_top_k : 8
  const isBusy = queryMutation.isPending || Boolean(streamingTurnId)

  const actions = (
    <>
      <Button
        variant="outline"
        onClick={() => {
          const md = exportTurnsMarkdown(turns)
          downloadText(`gkp-conversation-${new Date().toISOString().slice(0, 10)}.md`, md)
          showToast('Conversation exported as markdown.')
        }}
        disabled={!turns.length}
      >
        Export
      </Button>
      <Button
        variant="destructive"
        onClick={() => {
          if (confirm('Clear conversation history?')) {
            setTurns([])
            showToast('Conversation history cleared.')
          }
        }}
        disabled={!turns.length}
      >
        Clear
      </Button>
    </>
  )

  return (
    <>
      <Page
      title="Ask"
      description={
        meta?.public_demo_mode
          ? 'Public read-only mode: evidence-first responses with enforced citations.'
          : 'Private deployment mode: ingestion and evaluation controls depend on runtime policy.'
      }
      actions={actions}
    >
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Question</CardTitle>
              <CardDescription>
                Ask a question about what’s in the index. The system will refuse if it can’t cite enough evidence.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {offline ? (
                <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                  Offline mode: asking is disabled until the API is reachable.
                </div>
              ) : null}

              <div className="space-y-2">
                <Label htmlFor="question">Question</Label>
                <Textarea
                  id="question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question…"
                  rows={4}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <RangeSlider
                  label="top_k"
                  min={1}
                  max={Math.max(1, maxTopK)}
                  step={1}
                  value={topK}
                  onChange={setTopK}
                />

                <div className="flex items-center gap-2">
                  <Checkbox
                    id="debug"
                    checked={debug}
                    onChange={(e) => setDebug(e.currentTarget.checked)}
                    disabled={Boolean(meta?.public_demo_mode)}
                  />
                  <Label htmlFor="debug">Debug retrieval</Label>
                  {meta?.public_demo_mode ? (
                    <span className="text-xs text-muted-foreground">(locked in public read-only mode)</span>
                  ) : null}
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="streaming"
                    checked={useStreaming}
                    onChange={(e) => setUseStreaming(e.currentTarget.checked)}
                    disabled={isBusy}
                  />
                  <Label htmlFor="streaming">Streaming mode</Label>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {suggestedQuestions.map((ex) => (
                  <Button key={ex} variant="outline" size="sm" onClick={() => setQuestion(ex)}>
                    {ex}
                  </Button>
                ))}
              </div>

              <div className="flex items-center gap-2">
                <Button onClick={onAsk} disabled={!question.trim() || isBusy || offline}>
                  {isBusy ? 'Asking…' : 'Ask'}
                </Button>
                <Button variant="outline" onClick={() => setQuestion('')} disabled={!question}>
                  Reset
                </Button>
                {streamingTurnId ? (
                  <Button
                    variant="outline"
                    onClick={() => streamAbortRef.current?.abort()}
                    disabled={!streamingTurnId}
                  >
                    Cancel
                  </Button>
                ) : null}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Conversation</CardTitle>
              <CardDescription>
                Stored locally in your browser (up to {MAX_TURNS} turns). Export for a shareable markdown log.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!turns.length ? (
                <div className="text-sm text-muted-foreground">
                  No questions yet. Ask something above to start a local conversation.
                </div>
              ) : (
                <div className="space-y-4">
                  {[...turns]
                    .sort((a, b) => b.created_at.localeCompare(a.created_at))
                    .map((t) => {
                      const citations = t.response?.citations ?? []
                      const retrieval = t.response?.retrieval ?? []
                      const refused = Boolean(t.response?.refused)
                      const refusalReason = t.response?.refusal_reason
                      const provider = t.response?.provider
                      const answer = t.response?.answer

                      const citedChunkIds = new Set(citations.map((c) => c.chunk_id))
                      const retrievalScoreByChunk = new Map(retrieval.map((r) => [r.chunk_id, r.score] as const))

                      return (
                        <div key={t.id} className="rounded-xl border p-4">
                          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                            <div className="space-y-1">
                              <div className="text-sm font-semibold">Q</div>
                              <div className="text-sm">{t.question}</div>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                              {provider ? <Badge variant="outline">{provider}</Badge> : null}
                              {refused ? <Badge variant="warning">refused</Badge> : <Badge variant="success">answered</Badge>}
                              <Badge variant="secondary">top_k:{t.top_k}</Badge>
                              {t.debug ? <Badge variant="outline">debug</Badge> : null}
                            </div>
                          </div>

                          <Separator className="my-3" />

                          {t.error ? (
                            <div className="text-sm text-destructive">Error: {t.error}</div>
                          ) : !t.response ? (
                            <div className="text-sm text-muted-foreground">Working…</div>
                          ) : (
                            <div className="space-y-3">
                              <div className="text-sm font-semibold">A</div>
                              {answer ? (
                                <pre
                                  className="min-h-24 whitespace-pre-wrap rounded-lg bg-muted p-3 text-sm"
                                  aria-live={streamingTurnId === t.id ? 'polite' : undefined}
                                >
                                  {answer}
                                </pre>
                              ) : (
                                <div
                                  className="min-h-24 animate-pulse rounded-lg bg-muted p-3"
                                  aria-live="polite"
                                  aria-label="Answer is streaming"
                                />
                              )}

                              {refused && refusalReason ? (
                                <div className="text-xs text-muted-foreground">
                                  refusal_reason: <span className="font-mono">{refusalReason}</span>
                                </div>
                              ) : null}

                              {citations.length ? (
                                <div className="space-y-2">
                                  <div className="text-sm font-semibold">Citations</div>
                                  <div className="space-y-2">
                                    {citations.map((c) => {
                                      const score = retrievalScoreByChunk.get(c.chunk_id)
                                      const citationHref = buildDocCitationHref(c.doc_id, c, score)
                                      return (
                                        <div key={c.chunk_id} className="rounded-lg border p-3">
                                          <div className="flex flex-wrap items-start justify-between gap-2">
                                            <div className="space-y-1">
                                              <div className="text-sm font-semibold">{c.doc_title ?? 'Untitled'}</div>
                                              <div className="text-xs text-muted-foreground">{c.doc_source ?? c.doc_id}</div>
                                            </div>
                                            {typeof score === 'number' && Number.isFinite(score) ? (
                                              <Badge variant="outline">score {score.toFixed(3)}</Badge>
                                            ) : null}
                                          </div>
                                          {c.quote ? (
                                            <pre className="mt-2 whitespace-pre-wrap rounded bg-muted p-2 text-xs">{c.quote}</pre>
                                          ) : (
                                            <div className="mt-2 text-xs text-muted-foreground">No quote available.</div>
                                          )}
                                          <div className="mt-3 flex flex-wrap items-center gap-2">
                                            <a href={citationHref} className="text-sm underline">
                                              Open doc context
                                            </a>
                                            <Button
                                              type="button"
                                              size="sm"
                                              variant="outline"
                                              onClick={async () => {
                                                const quote = c.quote?.trim()
                                                if (!quote) return
                                                const text = buildCitationClipboardText({
                                                  quote,
                                                  docId: c.doc_id,
                                                  title: c.doc_title,
                                                  source: c.doc_source,
                                                  chunkId: c.chunk_id,
                                                })
                                                try {
                                                  await navigator.clipboard.writeText(text)
                                                  showToast('Citation quote copied.')
                                                } catch {
                                                  showToast('Copy failed.')
                                                }
                                              }}
                                              disabled={!c.quote?.trim()}
                                            >
                                              Copy citation
                                            </Button>
                                          </div>
                                        </div>
                                      )
                                    })}
                                  </div>
                                </div>
                              ) : null}

                              <div className="flex flex-wrap items-center gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={async () => {
                                    if (!answer) return
                                    try {
                                      await navigator.clipboard.writeText(answer)
                                      showToast('Answer copied to clipboard.')
                                    } catch {
                                      showToast('Copy failed.')
                                    }
                                  }}
                                  disabled={!answer}
                                >
                                  Copy answer
                                </Button>

                                <Dialog>
                                  <DialogTrigger asChild>
                                    <Button size="sm" variant="outline" disabled={!retrieval.length}>
                                      Retrieval ({retrieval.length})
                                    </Button>
                                  </DialogTrigger>
                                  <DialogContent className="max-h-[80vh] overflow-hidden">
                                    <DialogHeader>
                                      <DialogTitle>Retrieval debug</DialogTitle>
                                      <DialogDescription>
                                        Hybrid retrieval results (BM25 + embeddings). Highlighted rows are cited.
                                      </DialogDescription>
                                    </DialogHeader>

                                    {retrieval.length ? (
                                      <div className="space-y-2">
                                        <DataTable<RetrievalDebug>
                                          data={retrieval}
                                          columns={retrievalColumns}
                                          height={420}
                                          getRowClassName={(r) =>
                                            citedChunkIds.has((r as RetrievalDebug).chunk_id)
                                              ? 'bg-emerald-500/10'
                                              : ''
                                          }
                                        />
                                        <div className="text-xs text-muted-foreground">
                                          Note: full chunk text is only included when chunk view is enabled.
                                        </div>
                                      </div>
                                    ) : (
                                      <div className="text-sm text-muted-foreground">No retrieval debug returned.</div>
                                    )}
                                  </DialogContent>
                                </Dialog>
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Index</CardTitle>
              <CardDescription>Quick links and a snapshot of indexed content.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Link to="/docs" className="underline">
                  Docs
                </Link>
                <span className="text-muted-foreground">·</span>
                <Link to="/search" className="underline">
                  Search
                </Link>
                <span className="text-muted-foreground">·</span>
                <Link to="/dashboard" className="underline">
                  Dashboard
                </Link>
                <span className="text-muted-foreground">·</span>
                <Link to="/ingest" className="underline">
                  Ingest
                </Link>
              </div>

              <div className="grid grid-cols-3 gap-2 text-sm">
                <div className="rounded-lg border p-2">
                  <div className="text-xs text-muted-foreground">docs</div>
                  <div className="font-mono text-lg">{meta?.stats?.docs ?? '—'}</div>
                </div>
                <div className="rounded-lg border p-2">
                  <div className="text-xs text-muted-foreground">chunks</div>
                  <div className="font-mono text-lg">{meta?.stats?.chunks ?? '—'}</div>
                </div>
                <div className="rounded-lg border p-2">
                  <div className="text-xs text-muted-foreground">emb</div>
                  <div className="font-mono text-lg">{meta?.stats?.embeddings ?? '—'}</div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <div className="text-xs font-semibold text-muted-foreground">Recently indexed</div>
                {docsQuery.isError ? (
                  <div className="text-sm text-destructive">Failed to load docs list.</div>
                ) : docsQuery.data?.docs?.length ? (
                  <div className="space-y-1">
                    {docsQuery.data.docs.slice(0, 6).map((d) => (
                      <div key={d.doc_id} className="text-sm">
                        <Link to="/docs/$docId" params={{ docId: d.doc_id }} className="underline">
                          {d.title || d.doc_id}
                        </Link>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground">No docs.</div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Settings snapshot</CardTitle>
              <CardDescription>Operational flags reflected from the API.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Mode</span>
                {metaQuery.isError ? (
                  <Badge variant="destructive">api error</Badge>
                ) : meta ? (
                  meta.public_demo_mode ? (
                    <Badge variant="warning">public read-only</Badge>
                  ) : (
                    <Badge variant="success">private</Badge>
                  )
                ) : (
                  <Badge variant="secondary">loading…</Badge>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Uploads</span>
                <Badge variant={meta?.uploads_enabled ? 'success' : 'secondary'}>
                  {meta?.uploads_enabled ? 'enabled' : 'disabled'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Eval</span>
                <Badge variant={meta?.eval_enabled ? 'success' : 'secondary'}>
                  {meta?.eval_enabled ? 'enabled' : 'disabled'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Chunk view</span>
                <Badge variant={meta?.chunk_view_enabled ? 'success' : 'secondary'}>
                  {meta?.chunk_view_enabled ? 'enabled' : 'disabled'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Citations required</span>
                <Badge variant={meta?.citations_required ? 'success' : 'secondary'}>
                  {meta?.citations_required ? 'yes' : 'no'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">LLM</span>
                <Badge variant="outline">{meta?.llm_provider ?? '—'}</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      </Page>
      {toastMessage ? (
        <div className="pointer-events-none fixed bottom-4 right-4 z-50" aria-live="polite">
          <div className="rounded-lg border bg-background px-3 py-2 text-sm shadow-lg">{toastMessage}</div>
        </div>
      ) : null}
    </>
  )
}
