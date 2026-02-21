import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { useMemo, useState } from 'react'

import { api, ChunkSearchResult } from '../api'
import { useOfflineStatus } from '../lib/offline'
import {
  Badge,
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
  Page,
  Section,
  Spinner,
} from '../portfolio-ui'

function fmtScore(v: number | null | undefined): string {
  if (v == null) return '—'
  try {
    return v.toFixed(3)
  } catch {
    return String(v)
  }
}

export function SearchPage() {
  const offline = useOfflineStatus()
  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: 30_000 })
  const chunkViewEnabled = Boolean(metaQuery.data?.chunk_view_enabled)

  const [chunkOpen, setChunkOpen] = useState(false)
  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(null)

  const chunkDetailQuery = useQuery({
    queryKey: ['chunk', selectedChunkId],
    queryFn: () => api.chunkDetail(selectedChunkId as string),
    enabled: chunkViewEnabled && chunkOpen && Boolean(selectedChunkId),
    staleTime: 30_000,
  })

  const [q, setQ] = useState('')
  const [limit, setLimit] = useState(20)

  const enabled = q.trim().length >= 2
  const searchQuery = useQuery({
    queryKey: ['searchChunks', q, limit],
    queryFn: () => api.searchChunks(q, limit),
    enabled,
    staleTime: 2_000,
  })

  const results = searchQuery.data?.results ?? []

  const columns = useMemo(
    () => [
      {
        header: 'Doc',
        accessorKey: 'doc_title',
        cell: (info: any) => {
          const r = info.row.original as ChunkSearchResult
          return (
            <div className="space-y-1">
              <div className="font-medium">
                <Link to="/docs/$docId" params={{ docId: r.doc_id }} className="hover:underline">
                  {r.doc_title}
                </Link>
              </div>
              <div className="text-xs text-muted-foreground">{r.doc_source}</div>
              <div className="flex flex-wrap gap-1">
                <Badge variant="outline">{r.classification}</Badge>
                {r.tags.slice(0, 3).map((t) => (
                  <Badge key={t} variant="secondary">
                    {t}
                  </Badge>
                ))}
                {r.tags.length > 3 ? <Badge variant="secondary">+{r.tags.length - 3}</Badge> : null}
              </div>
            </div>
          )
        },
        meta: { minWidth: 240, maxWidth: 320 },
      },
      {
        header: 'Chunk',
        accessorKey: 'idx',
        cell: (info: any) => {
          const r = info.row.original as ChunkSearchResult
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
        cell: (info: any) => <span className="font-mono text-xs">{fmtScore(info.getValue())}</span>,
        meta: { width: 90 },
      },
      {
        header: 'Preview',
        accessorKey: 'text_preview',
        cell: (info: any) => {
          const r = info.row.original as ChunkSearchResult
          const preview = String(info.getValue() ?? '')
          if (!chunkViewEnabled) {
            return <div className="whitespace-pre-wrap text-xs">{preview}</div>
          }
          return (
            <button
              type="button"
              className="w-full text-left whitespace-pre-wrap text-xs hover:underline"
              onClick={() => {
                setSelectedChunkId(r.chunk_id)
                setChunkOpen(true)
              }}
              title="Open full chunk text"
            >
              {preview}
            </button>
          )
        },
        meta: { minWidth: 420 },
      },
    ],
    [chunkViewEnabled],
  )

  return (
    <Page title="Search" description="Find relevant evidence across indexed chunks and jump to source documents.">
      <Section
        title="Chunk search"
        description={
          <span>
            Search across indexed chunks. Uses SQLite FTS5 when available, otherwise falls back to a simple token-overlap
            score.
          </span>
        }
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Chunk Search
              <Badge variant="secondary">{results.length}</Badge>
            </CardTitle>
            <CardDescription>Tip: start with 2–3 keywords. Click a doc title to jump to its ingest lineage.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {offline ? (
              <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                Offline: search requires live API access and may be unavailable.
              </div>
            ) : null}
            <div className="grid gap-2 sm:grid-cols-3">
              <div className="sm:col-span-2">
                <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search chunks (keywords)…" />
              </div>
              <div>
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={String(limit)}
                  onChange={(e) => {
                    const n = parseInt(e.target.value, 10)
                    const clamped = Number.isFinite(n) ? Math.max(1, Math.min(n, 50)) : 20
                    setLimit(clamped)
                  }}
                  inputMode="numeric"
                  placeholder="Limit (max 50)"
                />
              </div>
            </div>

            {!enabled ? (
              <div className="text-sm text-muted-foreground">Enter at least 2 characters to search.</div>
            ) : null}

            {searchQuery.isLoading ? <Spinner /> : null}

            {searchQuery.isError ? (
              <div className="rounded-md border bg-destructive/10 p-3 text-sm">
                {offline ? 'Offline: search endpoint unreachable.' : (searchQuery.error as Error).message}
              </div>
            ) : null}

            <DataTable<ChunkSearchResult> data={results} columns={columns} height={560} />
          </CardContent>
        </Card>
      </Section>

      <Dialog
        open={chunkOpen}
        onOpenChange={(open) => {
          setChunkOpen(open)
          if (!open) setSelectedChunkId(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Chunk</DialogTitle>
            <DialogDescription>
              Full chunk text (only available when chunk viewing is enabled).
            </DialogDescription>
          </DialogHeader>
          <div className="mt-3 space-y-2">
            {chunkDetailQuery.isLoading ? <Spinner /> : null}
            {chunkDetailQuery.isError ? (
              <div className="rounded-md border bg-destructive/10 p-3 text-sm">{(chunkDetailQuery.error as Error).message}</div>
            ) : null}
            {chunkDetailQuery.data ? (
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground">
                  <span className="font-mono">{chunkDetailQuery.data.chunk.chunk_id}</span>
                  {' · '}
                  <Link to="/docs/$docId" params={{ docId: chunkDetailQuery.data.chunk.doc_id }} className="hover:underline">
                    {chunkDetailQuery.data.chunk.doc_title ?? chunkDetailQuery.data.chunk.doc_id}
                  </Link>
                </div>
                <div className="max-h-[60vh] overflow-y-auto whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm leading-relaxed">
                  {chunkDetailQuery.data.chunk.text}
                </div>
              </div>
            ) : null}
          </div>
        </DialogContent>
      </Dialog>
    </Page>
  )
}
