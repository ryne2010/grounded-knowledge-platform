import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from '@tanstack/react-router'
import { useMemo, useState } from 'react'

import { api, ChunkSummary, Doc, DocUpdateRequest, IngestEvent } from '../api'
import { formatUnixSeconds } from '../lib/time'
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  DataTable,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  Input,
  Label,
  Page,
  Section,
  Spinner,
} from '../portfolio-ui'

export function DocDetailPage() {
  const { docId } = useParams({ from: '/docs/$docId' })
  const navigate = useNavigate()
  const qc = useQueryClient()

  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: 30_000 })

  const docQuery = useQuery({
    queryKey: ['doc', docId],
    queryFn: () => api.docDetail(docId),
    staleTime: 5_000,
  })

  const meta = metaQuery.data
  const doc = docQuery.data?.doc
  const events = docQuery.data?.ingest_events ?? []

  const chunkViewEnabled = Boolean(meta?.chunk_view_enabled)

  const [chunkFilter, setChunkFilter] = useState('')
  const [copyStatus, setCopyStatus] = useState<string | null>(null)

  const classifications = meta?.doc_classifications ?? ['public', 'internal', 'confidential', 'restricted']
  const retentions = meta?.doc_retentions ?? ['none', '30d', '90d', '1y', 'indefinite']

  const [editOpen, setEditOpen] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editSource, setEditSource] = useState('')
  const [editClassification, setEditClassification] = useState('')
  const [editRetention, setEditRetention] = useState('')
  const [editTags, setEditTags] = useState('')
  const chunksQuery = useQuery({
    queryKey: ['docChunks', docId],
    queryFn: () => api.docChunks(docId, 200, 0),
    enabled: chunkViewEnabled,
    staleTime: 5_000,
  })

  const chunks = chunksQuery.data?.chunks ?? []

  const filteredChunks = useMemo(() => {
    const needle = chunkFilter.trim().toLowerCase()
    if (!needle) return chunks
    return chunks.filter((c) => c.text_preview.toLowerCase().includes(needle) || String(c.idx).includes(needle))
  }, [chunks, chunkFilter])

  const [chunkOpen, setChunkOpen] = useState(false)
  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(null)

  const chunkDetailQuery = useQuery({
    queryKey: ['chunk', selectedChunkId],
    queryFn: () => api.chunkDetail(selectedChunkId as string),
    enabled: chunkViewEnabled && chunkOpen && Boolean(selectedChunkId),
    staleTime: 60_000,
  })

  const deleteMutation = useMutation({
    mutationFn: async () => api.deleteDoc(docId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['docs'] })
      await qc.invalidateQueries({ queryKey: ['doc', docId] })
      navigate({ to: '/docs' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: async (payload: DocUpdateRequest) => api.updateDoc(docId, payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['docs'] })
      await qc.invalidateQueries({ queryKey: ['doc', docId] })
      setEditOpen(false)
    },
  })

  const editEnabled = Boolean(meta?.uploads_enabled) && !Boolean(meta?.public_demo_mode)

  const openEdit = () => {
    if (!doc) return
    setEditTitle(doc.title)
    setEditSource(doc.source)
    setEditClassification(doc.classification)
    setEditRetention(doc.retention)
    setEditTags(doc.tags?.join(', ') ?? '')
    setEditOpen(true)
  }

  const chunkCols = useMemo(
    () => [
      { header: 'Idx', accessorKey: 'idx' },
      {
        header: 'Preview',
        accessorKey: 'text_preview',
        cell: (info: any) => {
          const c = info.row.original as ChunkSummary
          return (
            <button
              className="text-left hover:underline"
              onClick={() => {
                setSelectedChunkId(c.chunk_id)
                setChunkOpen(true)
              }}
            >
              {c.text_preview}
            </button>
          )
        },
      },
      {
        header: 'Chunk ID',
        accessorKey: 'chunk_id',
        cell: (info: any) => <span className="font-mono text-xs">{String(info.getValue() ?? '')}</span>,
      },
    ],
    [],
  )

  const eventCols = useMemo(
    () => [
      {
        header: 'Time',
        accessorKey: 'ingested_at',
        cell: (info: any) => <span className="text-xs">{formatUnixSeconds(Number(info.getValue() ?? 0))}</span>,
      },
      {
        header: 'v',
        accessorKey: 'doc_version',
        cell: (info: any) => <span className="font-mono text-xs">v{String(info.getValue() ?? '')}</span>,
      },
      {
        header: 'Changed',
        accessorKey: 'changed',
        cell: (info: any) => (info.getValue() ? <Badge variant="warning">changed</Badge> : <Badge variant="outline">same</Badge>),
      },
      {
        header: 'Content SHA',
        accessorKey: 'content_sha256',
        cell: (info: any) => {
          const e = info.row.original as IngestEvent
          const cur = e.content_sha256 ? e.content_sha256.slice(0, 10) : '—'
          const prev = e.prev_content_sha256 ? e.prev_content_sha256.slice(0, 10) : null
          return (
            <div className="text-xs font-mono">
              <div>{cur}</div>
              {prev ? <div className="text-muted-foreground">prev {prev}</div> : null}
            </div>
          )
        },
      },
      { header: 'Chunks', accessorKey: 'num_chunks' },
      {
        header: 'Embedding',
        accessorKey: 'embedding_backend',
        cell: (info: any) => {
          const e = info.row.original as IngestEvent
          return (
            <div className="space-y-1">
              <div className="text-xs">
                <span className="font-mono">{e.embedding_backend}</span>
                {e.embeddings_model ? <span className="text-muted-foreground"> · {e.embeddings_model}</span> : null}
              </div>
              <div className="text-xs text-muted-foreground">dim {e.embedding_dim}</div>
            </div>
          )
        },
      },
      {
        header: 'Chunking',
        accessorKey: 'chunk_size_chars',
        cell: (info: any) => {
          const e = info.row.original as IngestEvent
          return (
            <span className="text-xs text-muted-foreground">
              {e.chunk_size_chars} / overlap {e.chunk_overlap_chars}
            </span>
          )
        },
      },
      {
        header: 'Note',
        accessorKey: 'notes',
        cell: (info: any) => <span className="text-xs">{String(info.getValue() ?? '')}</span>,
      },
    ],
    [],
  )

  const deleteEnabled = Boolean(meta?.doc_delete_enabled)

  return (
    <Page>
      <Section title="Doc detail" description="Metadata, ingest lineage, and chunk browser.">
        <div className="mb-4 flex items-center justify-between">
          <Link to="/docs" className="text-sm underline">
            ← Back to docs
          </Link>
          <div className="flex items-center gap-2">
            {editEnabled ? (
              <Button variant="secondary" onClick={openEdit} disabled={!doc || updateMutation.isPending}>
                Edit metadata
              </Button>
            ) : null}

            {deleteEnabled ? (
              <Button
                variant="destructive"
                onClick={() => {
                  if (confirm('Delete this document (and all chunks/embeddings)?')) {
                    deleteMutation.mutate()
                  }
                }}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? <Spinner size="sm" /> : 'Delete doc'}
              </Button>
            ) : null}
          </div>
        </div>

        {docQuery.isLoading ? <Spinner /> : null}
        {docQuery.isError ? (
          <div className="rounded-md border bg-destructive/10 p-3 text-sm">{(docQuery.error as Error).message}</div>
        ) : null}

        {doc ? (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-start justify-between gap-3">
                  <span className="min-w-0 truncate">{doc.title}</span>
                  <Badge variant="outline">v{doc.doc_version}</Badge>
                </CardTitle>
                <CardDescription className="truncate">{doc.source}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">{doc.classification}</Badge>
                  <Badge variant="secondary">retention: {doc.retention}</Badge>
                  <Badge variant="outline">{doc.num_chunks} chunks</Badge>
                  {doc.content_sha256 ? <Badge variant="outline">sha {doc.content_sha256.slice(0, 10)}…</Badge> : null}
                </div>

                {doc.tags.length ? (
                  <div className="flex flex-wrap gap-1">
                    {doc.tags.map((t) => (
                      <Badge key={t} variant="secondary">
                        {t}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground">No tags</div>
                )}

                {chunkViewEnabled ? (
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      onClick={() => window.open(`/api/docs/${encodeURIComponent(doc.doc_id)}/text`, '_blank')}
                    >
                      Open raw text
                    </Button>
                    <Button
                      variant="outline"
                      onClick={async () => {
                        try {
                          setCopyStatus('Fetching…')
                          const text = await api.docText(doc.doc_id)
                          await navigator.clipboard.writeText(text)
                          setCopyStatus('Copied doc text to clipboard')
                          setTimeout(() => setCopyStatus(null), 2000)
                        } catch (e: any) {
                          setCopyStatus(String(e?.message ?? e))
                        }
                      }}
                    >
                      Copy text
                    </Button>
                  </div>
                ) : null}

                {copyStatus ? <div className="text-xs text-muted-foreground">{copyStatus}</div> : null}

                <div className="grid grid-cols-1 gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                  <div>
                    <span className="font-medium">Doc ID:</span> <span className="font-mono text-xs">{doc.doc_id}</span>
                  </div>
                  <div>
                    <span className="font-medium">Bytes:</span> {doc.content_bytes}
                  </div>
                  <div>
                    <span className="font-medium">Created:</span> {formatUnixSeconds(doc.created_at)}
                  </div>
                  <div>
                    <span className="font-medium">Updated:</span> {formatUnixSeconds(doc.updated_at)}
                  </div>
                </div>

                {!chunkViewEnabled ? (
                  <div className="rounded-md border bg-muted p-3 text-sm text-muted-foreground">
                    Chunk browsing is disabled. Enable <span className="font-mono">ALLOW_CHUNK_VIEW=1</span> for private
                    deployments.
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Ingest lineage</CardTitle>
                <CardDescription>Each ingest creates an event with content hash + settings.</CardDescription>
              </CardHeader>
              <CardContent>
                {events.length ? (
                  <DataTable<IngestEvent> data={events} columns={eventCols} height={420} />
                ) : (
                  <div className="text-sm text-muted-foreground">No ingest events recorded.</div>
                )}
              </CardContent>
            </Card>

            <Card className="lg:col-span-3">
              <CardHeader>
                <CardTitle>Chunks</CardTitle>
                <CardDescription>Click a chunk preview to open full text (when enabled).</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {chunkViewEnabled ? (
                  <>
                    <Input value={chunkFilter} onChange={(e) => setChunkFilter(e.target.value)} placeholder="Filter chunks…" />
                    {chunksQuery.isLoading ? <Spinner /> : null}
                    {chunksQuery.isError ? (
                      <div className="rounded-md border bg-destructive/10 p-3 text-sm">{(chunksQuery.error as Error).message}</div>
                    ) : null}
                    <DataTable<ChunkSummary> data={filteredChunks} columns={chunkCols} height={360} />
                    <div className="text-xs text-muted-foreground">Showing up to 200 chunks. Use tags/retention to manage scale.</div>
                  </>
                ) : (
                  <div className="text-sm text-muted-foreground">Chunk browsing disabled.</div>
                )}
              </CardContent>
            </Card>
          </div>
        ) : null}

        <Dialog open={editOpen} onOpenChange={setEditOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit doc metadata</DialogTitle>
              <DialogDescription>
                Updates title/source/classification/retention/tags. This is disabled in public demo mode.
              </DialogDescription>
            </DialogHeader>

            <div className="mt-3 space-y-4">
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="editTitle">Title</Label>
                  <Input id="editTitle" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="editSource">Source</Label>
                  <Input id="editSource" value={editSource} onChange={(e) => setEditSource(e.target.value)} />
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="editClassification">Classification</Label>
                  <Input
                    id="editClassification"
                    list="doc-classifications"
                    value={editClassification}
                    onChange={(e) => setEditClassification(e.target.value)}
                    placeholder="public"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="editRetention">Retention</Label>
                  <Input
                    id="editRetention"
                    list="doc-retentions"
                    value={editRetention}
                    onChange={(e) => setEditRetention(e.target.value)}
                    placeholder="indefinite"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="editTags">Tags</Label>
                  <Input
                    id="editTags"
                    value={editTags}
                    onChange={(e) => setEditTags(e.target.value)}
                    placeholder="comma,separated,tags"
                  />
                </div>
              </div>

              <datalist id="doc-classifications">
                {classifications.map((c) => (
                  <option key={c} value={c} />
                ))}
              </datalist>
              <datalist id="doc-retentions">
                {retentions.map((r) => (
                  <option key={r} value={r} />
                ))}
              </datalist>

              {updateMutation.isError ? (
                <div className="rounded-md border bg-destructive/10 p-3 text-sm">
                  {(updateMutation.error as Error).message}
                </div>
              ) : null}

              <div className="flex items-center justify-end gap-2">
                <Button variant="secondary" onClick={() => setEditOpen(false)} disabled={updateMutation.isPending}>
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    const payload: DocUpdateRequest = {
                      title: editTitle.trim(),
                      source: editSource.trim(),
                      classification: editClassification.trim(),
                      retention: editRetention.trim(),
                      tags: editTags
                        .split(',')
                        .map((t) => t.trim())
                        .filter(Boolean),
                    }
                    updateMutation.mutate(payload)
                  }}
                  disabled={updateMutation.isPending}
                >
                  {updateMutation.isPending ? (
                    <span className="inline-flex items-center gap-2">
                      <Spinner size="sm" /> Saving…
                    </span>
                  ) : (
                    'Save'
                  )}
                </Button>
              </div>

              <div className="text-xs text-muted-foreground">
                Note: metadata edits do not reset the retention clock (retention is based on last content ingest).
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={chunkOpen} onOpenChange={setChunkOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Chunk</DialogTitle>
              <DialogDescription className="font-mono text-xs">{selectedChunkId}</DialogDescription>
            </DialogHeader>
            <div className="mt-3 max-h-[60vh] overflow-auto rounded-lg border bg-muted p-3">
              {chunkDetailQuery.isLoading ? <Spinner /> : null}
              {chunkDetailQuery.isError ? (
                <div className="rounded-md border bg-destructive/10 p-3 text-sm">{(chunkDetailQuery.error as Error).message}</div>
              ) : null}
              <div className="whitespace-pre-wrap text-sm leading-relaxed">{chunkDetailQuery.data?.chunk.text ?? ''}</div>
            </div>
          </DialogContent>
        </Dialog>
      </Section>
    </Page>
  )
}
