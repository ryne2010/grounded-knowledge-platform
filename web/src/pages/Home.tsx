import React from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useForm } from '@tanstack/react-form'
import type { ColumnDef } from '@tanstack/react-table'
import { api, type IngestTextRequest, type QueryCitation, type QueryResponse } from '../api'
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
  Input,
  Label,
  Page,
  RangeSlider,
  Textarea,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../portfolio-ui'

function formatEpochSeconds(ts: number) {
  const d = new Date(ts * 1000)
  return d.toLocaleString()
}

export function HomePage() {
  const metaQ = useQuery({ queryKey: ['meta'], queryFn: api.meta })

  const mutation = useMutation({
    mutationFn: api.query,
  })

  const fileMutation = useMutation({
    mutationFn: api.ingestFile,
  })

  const textMutation = useMutation({
    mutationFn: api.ingestText,
  })

  const form = useForm({
    defaultValues: {
      question: '',
      top_k: 6,
      debug: false,
    },
    onSubmit: async ({ value }) => {
      await mutation.mutateAsync(value)
    },
  })


  const [chunkOpen, setChunkOpen] = React.useState(false)
  const [selectedChunk, setSelectedChunk] = React.useState<{
    chunk: NonNullable<QueryResponse['retrieval']>[number] | null
    citation: QueryCitation | null
  } | null>(null)

  const [uploadFile, setUploadFile] = React.useState<File | null>(null)
  const [textTitle, setTextTitle] = React.useState('')
  const [textSource, setTextSource] = React.useState('')
  const [textBody, setTextBody] = React.useState('')
  const [textDocId, setTextDocId] = React.useState('')
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const citations = mutation.data?.citations ?? []
  const retrieval = mutation.data?.retrieval ?? []
  const showEvidence = Boolean(mutation.data && !mutation.data.refused)

  // Highlight retrieved chunks that were actually cited in the final answer.
  // This improves transparency: "what did we retrieve" vs "what did we rely on".
  const citedChunkIds = React.useMemo(() => {
    return new Set((citations ?? []).map((c) => c.chunk_id))
  }, [citations])

  const citationByChunkId = React.useMemo(() => {
    const map = new Map<string, QueryCitation>()
    for (const c of citations) map.set(c.chunk_id, c)
    return map
  }, [citations])

  const openChunkFromRetrieval = React.useCallback(
    (hit: NonNullable<QueryResponse['retrieval']>[number]) => {
      setSelectedChunk({ chunk: hit, citation: citationByChunkId.get(hit.chunk_id) ?? null })
      setChunkOpen(true)
    },
    [citationByChunkId],
  )

  const openChunkFromCitation = React.useCallback(
    (citation: QueryCitation) => {
      const hit =
        retrieval.find((r) => r.chunk_id === citation.chunk_id) ??
        retrieval.find((r) => r.doc_id === citation.doc_id && r.idx === citation.idx) ??
        null
      setSelectedChunk({ chunk: hit, citation })
      setChunkOpen(true)
    },
    [retrieval],
  )

  const findQuoteSpan = React.useCallback((text: string, quote: string) => {
    const cleanedQuote = quote.trim().replace(/\s+/g, ' ').toLowerCase()
    if (!cleanedQuote) return null

    let normalized = ''
    const map: number[] = []
    let inWs = false
    for (let i = 0; i < text.length; i += 1) {
      const ch = text[i]
      if (/\s/.test(ch)) {
        if (!inWs) {
          normalized += ' '
          map.push(i)
          inWs = true
        }
        continue
      }
      normalized += ch.toLowerCase()
      map.push(i)
      inWs = false
    }

    const idx = normalized.indexOf(cleanedQuote)
    if (idx === -1) return null
    const start = map[idx] ?? 0
    const end = (map[idx + cleanedQuote.length - 1] ?? start) + 1
    return [start, end] as const
  }, [])

  const renderHighlighted = React.useCallback(
    (text: string, quote?: string) => {
      if (!quote) return text
      const needle = quote.trim()
      if (!needle) return text

      const lowerText = text.toLowerCase()
      const lowerNeedle = needle.toLowerCase()
      let start = lowerText.indexOf(lowerNeedle)
      let end = start === -1 ? -1 : start + needle.length

      if (start === -1) {
        const span = findQuoteSpan(text, needle)
        if (span) {
          ;[start, end] = span
        }
      }

      if (start === -1) return text

      return (
        <>
          {text.slice(0, start)}
          <mark className="rounded bg-amber-200/70 px-1 text-foreground">
            {text.slice(start, end)}
          </mark>
          {text.slice(end)}
        </>
      )
    },
    [findQuoteSpan],
  )

  const citationCols = React.useMemo<ColumnDef<QueryCitation>[]>(() => {
    return [
      {
        header: '',
        id: 'view',
        meta: { width: 96 },
        cell: ({ row }) => (
          <Button variant="outline" size="sm" onClick={() => openChunkFromCitation(row.original)}>
            View
          </Button>
        ),
      },
      { header: 'Doc', accessorKey: 'doc_id' },
      { header: 'Chunk', accessorKey: 'idx' },
      {
        header: 'Quote',
        accessorKey: 'quote',
        cell: (info) => {
          const v = String(info.getValue() ?? '')
          return v ? (
            <span className="text-muted-foreground">{v.slice(0, 50)}{v.length > 50 ? '…' : ''}</span>
          ) : (
            <span className="text-muted-foreground">—</span>
          )
        },
      },
      {
        header: 'Chunk ID',
        accessorKey: 'chunk_id',
        cell: (info) => (
          <span className="font-mono text-xs text-muted-foreground">{String(info.getValue())}</span>
        ),
      },
    ]
  }, [openChunkFromCitation])

  const retrievalCols = React.useMemo<ColumnDef<NonNullable<QueryResponse['retrieval']>[number]>[]>(() => {
    return [
      {
        header: '',
        id: 'view',
        meta: { width: 96 },
        cell: ({ row }) => (
          <Button variant="outline" size="sm" onClick={() => openChunkFromRetrieval(row.original)}>
            View
          </Button>
        ),
      },
      { header: 'Doc', accessorKey: 'doc_id' },
      { header: 'Chunk', accessorKey: 'idx' },
      {
        header: 'Score',
        accessorKey: 'score',
        cell: (info) => <span className="font-mono text-xs">{Number(info.getValue()).toFixed(4)}</span>,
      },
      {
        header: 'Lex',
        accessorKey: 'lexical_score',
        cell: (info) => {
          const v = info.getValue() as any
          return v == null ? (
            <span className="text-muted-foreground">—</span>
          ) : (
            <span className="font-mono text-xs">{Number(v).toFixed(4)}</span>
          )
        },
      },
      {
        header: 'Vec',
        accessorKey: 'vector_score',
        cell: (info) => {
          const v = info.getValue() as any
          return v == null ? (
            <span className="text-muted-foreground">—</span>
          ) : (
            <span className="font-mono text-xs">{Number(v).toFixed(4)}</span>
          )
        },
      },
      {
        header: 'Preview',
        accessorKey: 'text_preview',
        cell: (info) => {
          const v = String(info.getValue() ?? '')
          return v ? (
            <span className="text-muted-foreground">{v.slice(0, 50)}{v.length > 50 ? '…' : ''}</span>
          ) : (
            <span className="text-muted-foreground">—</span>
          )
        },
      },
    ]
  }, [openChunkFromRetrieval])

  const meta = metaQ.data
  const uploadsEnabled = Boolean(meta?.uploads_enabled)

  const _didInitDebug = React.useRef(false)
  React.useEffect(() => {
    if (!meta) return
    if (meta.public_demo_mode) return
    if (_didInitDebug.current) return
    // In local/private mode, default to debug=true for transparency.
    form.setFieldValue('debug', true)
    _didInitDebug.current = true
  }, [meta])

  return (
    <Page
      title="Ask"
      description={
        <span>
          Grounded RAG demo with citations + refusal behavior. Public demo mode defaults to{' '}
          <Badge variant="secondary">extractive-only</Badge> and disables uploads.
        </span>
      }
      actions={
        meta ? (
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={meta.public_demo_mode ? 'success' : 'secondary'}>
              {meta.public_demo_mode ? 'PUBLIC_DEMO_MODE=1' : 'demo'}
            </Badge>
            <Badge variant="outline">LLM: {meta.llm_provider}</Badge>
            <Badge variant="outline">Embeddings: {meta.embeddings_backend}</Badge>
            <Badge variant={meta.ocr_enabled ? 'secondary' : 'outline'}>OCR: {meta.ocr_enabled ? 'on' : 'off'}</Badge>
            <Badge variant={meta.uploads_enabled ? 'secondary' : 'outline'}>
              Uploads: {meta.uploads_enabled ? 'on' : 'off'}
            </Badge>
          </div>
        ) : null
      }
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Question</CardTitle>
              <CardDescription>Submit a question. The answer will include citations, or refuse when unsupported.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  form.handleSubmit()
                }}
                className="space-y-4"
              >
                <form.Field
                  name="question"
                  validators={{
                    onSubmit: ({ value }) => (!value?.trim() ? 'Question is required' : undefined),
                  }}
                >
                  {(field) => (
                    <div className="space-y-2">
                      <Label htmlFor={field.name}>Question</Label>
                      <Textarea
                        id={field.name}
                        value={field.state.value}
                        onChange={(e) => field.handleChange(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key !== 'Enter') return
                          if (e.shiftKey) return
                          if (e.nativeEvent.isComposing) return
                          e.preventDefault()
                          form.handleSubmit()
                        }}
                        placeholder="e.g., What does the demo say about PUBLIC_DEMO_MODE?"
                      />
                      {field.state.meta.errors?.length ? (
                        <div className="text-xs text-destructive">{field.state.meta.errors.join(', ')}</div>
                      ) : null}
                    </div>
                  )}
                </form.Field>

                <form.Field name="top_k">
                  {(field) => (
                    <RangeSlider
                      min={2}
                      max={12}
                      step={1}
                      value={field.state.value}
                      onChange={(v) => field.handleChange(v)}
                      label="Top-K chunks"
                      format={(n) => `${n}`}
                    />
                  )}
                </form.Field>
                {meta?.public_demo_mode ? null : (
                  <form.Field name="debug">
                    {(field) => (
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={field.state.value}
                          onChange={(e) => field.handleChange((e.target as HTMLInputElement).checked)}
                          disabled={Boolean(meta?.public_demo_mode)}
                        />
                        <Label>
                          Include retrieval debug{' '}
                          {meta?.public_demo_mode ? <span className="text-muted-foreground">(disabled in public demo)</span> : null}
                        </Label>
                      </div>
                    )}
                  </form.Field>
                )}

                <Button type="submit" disabled={mutation.isPending} className="w-full">
                  {mutation.isPending ? 'Running…' : 'Ask'}
                </Button>
              </form>

              {mutation.isError ? (
                <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm">
                  <div className="font-medium">Request failed</div>
                  <div className="text-muted-foreground">{(mutation.error as Error).message}</div>
                </div>
              ) : null}

              {mutation.data ? (
                <div className="text-xs text-muted-foreground">
                  Provider: <span className="font-mono">{mutation.data.provider}</span> •{' '}
                  {meta?.public_demo_mode ? 'Public demo mode' : 'Normal mode'} •{' '}
                  {formatEpochSeconds(Math.floor(Date.now() / 1000))}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Upload</CardTitle>
              <CardDescription>Add documents to the index. Supports .txt, .md, and .pdf.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {!meta ? <div className="text-sm text-muted-foreground">Loading…</div> : null}
              {meta && !uploadsEnabled ? (
                <div className="text-sm text-muted-foreground">
                  Uploads are disabled in this deployment.
                </div>
              ) : null}
              {uploadsEnabled ? (
                <>
                  <div className="space-y-3">
                    <div className="text-sm font-medium">Upload file</div>
                    <form
                      onSubmit={async (e) => {
                        e.preventDefault()
                        if (!uploadFile) return
                        await fileMutation.mutateAsync(uploadFile)
                        setUploadFile(null)
                        if (fileInputRef.current) fileInputRef.current.value = ''
                      }}
                      className="space-y-3"
                    >
                      <Input
                        ref={fileInputRef}
                        type="file"
                        accept=".txt,.md,.pdf"
                        disabled={fileMutation.isPending}
                        onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
                      />
                      <div className="flex items-center gap-3">
                        <Button type="submit" disabled={!uploadFile || fileMutation.isPending}>
                          {fileMutation.isPending ? 'Uploading…' : 'Upload file'}
                        </Button>
                        {uploadFile ? (
                          <span className="text-xs text-muted-foreground">{uploadFile.name}</span>
                        ) : null}
                      </div>
                      {fileMutation.isError ? (
                        <div className="text-xs text-destructive">{(fileMutation.error as Error).message}</div>
                      ) : null}
                      {fileMutation.isSuccess ? (
                        <div className="text-xs text-muted-foreground">
                          Ingested {fileMutation.data.doc_id} ({fileMutation.data.num_chunks} chunks).
                        </div>
                      ) : null}
                    </form>
                  </div>

                  <div className="space-y-3">
                    <div className="text-sm font-medium">Paste text</div>
                    <form
                      onSubmit={async (e) => {
                        e.preventDefault()
                        if (!textTitle.trim() || !textSource.trim() || !textBody.trim()) return
                        const payload: IngestTextRequest = {
                          title: textTitle.trim(),
                          source: textSource.trim(),
                          text: textBody.trim(),
                          doc_id: textDocId.trim() || undefined,
                        }
                        await textMutation.mutateAsync(payload)
                        setTextTitle('')
                        setTextSource('')
                        setTextBody('')
                        setTextDocId('')
                      }}
                      className="space-y-3"
                    >
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div className="space-y-2">
                          <Label>Title</Label>
                          <Input value={textTitle} onChange={(e) => setTextTitle(e.target.value)} placeholder="Quarterly report" />
                        </div>
                        <div className="space-y-2">
                          <Label>Source</Label>
                          <Input value={textSource} onChange={(e) => setTextSource(e.target.value)} placeholder="internal:reports/q1" />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Doc ID (optional)</Label>
                        <Input value={textDocId} onChange={(e) => setTextDocId(e.target.value)} placeholder="optional-stable-id" />
                      </div>
                      <div className="space-y-2">
                        <Label>Text</Label>
                        <Textarea
                          value={textBody}
                          onChange={(e) => setTextBody(e.target.value)}
                          placeholder="Paste the content to ingest…"
                          rows={6}
                        />
                      </div>
                      <div className="flex items-center gap-3">
                        <Button
                          type="submit"
                          disabled={
                            textMutation.isPending ||
                            !textTitle.trim() ||
                            !textSource.trim() ||
                            !textBody.trim()
                          }
                        >
                          {textMutation.isPending ? 'Ingesting…' : 'Ingest text'}
                        </Button>
                      </div>
                      {textMutation.isError ? (
                        <div className="text-xs text-destructive">{(textMutation.error as Error).message}</div>
                      ) : null}
                      {textMutation.isSuccess ? (
                        <div className="text-xs text-muted-foreground">
                          Ingested {textMutation.data.doc_id} ({textMutation.data.num_chunks} chunks).
                        </div>
                      ) : null}
                    </form>
                  </div>
                </>
              ) : null}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Answer
              <Badge variant="secondary">provider: {mutation.data?.provider ?? '—'}</Badge>
              {mutation.data?.refused ? <Badge variant="warning">refused</Badge> : <Badge variant="outline">grounded</Badge>}
              {mutation.data?.refusal_reason ? (
                <Badge variant="destructive" title={mutation.data.refusal_reason}>
                  reason
                </Badge>
              ) : null}
            </CardTitle>
            <CardDescription>
              Answers are grounded in retrieved text. If the system cannot support a claim, it should refuse.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!mutation.data ? (
              <div className="text-sm text-muted-foreground">Ask a question to see an answer and citations.</div>
            ) : (
              <>
                {mutation.data.refused && mutation.data.refusal_reason ? (
                  <div className="rounded-md border bg-destructive/10 p-3 text-sm">
                    <span className="font-medium">Refusal reason:</span>{' '}
                    <span className="font-mono">{mutation.data.refusal_reason}</span>
                  </div>
                ) : null}
                <div className="whitespace-pre-wrap rounded-md border border-primary/20 bg-muted/40 p-4 text-sm leading-relaxed shadow">
                  {mutation.data.answer}
                </div>

                {showEvidence ? (
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Citations</div>
                    {citations.length ? (
                      <DataTable<QueryCitation> data={citations} columns={citationCols} height={240} />
                    ) : (
                      <div className="text-sm text-muted-foreground">No citations returned.</div>
                    )}
                  </div>
                ) : null}

                {showEvidence && form.state.values.debug && retrieval.length ? (
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Retrieval debug</div>
                    <div className="text-xs text-muted-foreground flex flex-wrap items-center gap-3">
                      <span className="inline-flex items-center gap-2">
                        <span className="h-3 w-3 rounded-sm bg-amber-50/60 dark:bg-amber-950/25 border border-amber-400" />
                        <span>Highlighted rows were cited in the final answer.</span>
                      </span>
                      <span className="inline-flex items-center gap-2">
                        <span className="h-3 w-3 rounded-sm border border-border" />
                        <span>Other rows were retrieved but not cited.</span>
                      </span>
                    </div>
                    <DataTable
                      data={retrieval}
                      columns={retrievalCols}
                      height={260}
                      getRowClassName={(row) =>
                        citedChunkIds.has((row as any).chunk_id)
                          ? 'bg-amber-50/60 dark:bg-amber-950/25 border-l-4 border-amber-400'
                          : ''
                      }
                    />
                    <div className="text-xs text-muted-foreground">
                      Debug shows hybrid scores and chunk previews (useful for tuning).
                    </div>
                  </div>
                ) : null}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={chunkOpen} onOpenChange={setChunkOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Retrieved chunk</DialogTitle>
            <DialogDescription>
              {selectedChunk ? (
                <span className="font-mono text-xs">
                  {selectedChunk.chunk?.doc_id ?? selectedChunk.citation?.doc_id ?? '—'} / idx{' '}
                  {selectedChunk.chunk?.idx ?? selectedChunk.citation?.idx ?? '—'}
                  {selectedChunk.chunk ? ` • score ${Number(selectedChunk.chunk.score).toFixed(4)}` : ''}
                </span>
              ) : null}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-3 max-h-[60vh] overflow-auto rounded-lg border bg-muted p-3">
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {selectedChunk
                ? renderHighlighted(
                    selectedChunk.chunk?.text ??
                      selectedChunk.chunk?.text_preview ??
                      selectedChunk.citation?.quote ??
                      '',
                    selectedChunk.citation?.quote,
                  )
                : ''}
            </div>
          </div>
        </DialogContent>
      </Dialog>
</Page>
  )
}
