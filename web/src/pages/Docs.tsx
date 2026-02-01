import { useDebouncedValue } from '@tanstack/react-pacer/debouncer'
import { useQuery } from '@tanstack/react-query'
import type { ColumnDef } from '@tanstack/react-table'
import React from 'react'
import { api, type Doc } from '../api'
import { Badge, Card, CardContent, CardDescription, CardHeader, CardTitle, DataTable, Input, Page } from '../portfolio-ui'

function formatEpochSeconds(ts: number) {
  const d = new Date(ts * 1000)
  return d.toLocaleString()
}

export function DocsPage() {
  const q = useQuery({ queryKey: ['docs'], queryFn: api.docs })
  const docs = q.data?.docs ?? []

  const [searchRaw, setSearchRaw] = React.useState('')
  const [search] = useDebouncedValue(searchRaw, { wait: 200 })

  const filtered = React.useMemo(() => {
    const s = search.trim().toLowerCase()
    if (!s) return docs
    return docs.filter((d) => `${d.title} ${d.source} ${d.doc_id}`.toLowerCase().includes(s))
  }, [docs, search])

  const cols = React.useMemo<ColumnDef<Doc>[]>(() => {
    return [
      { header: 'Title', accessorKey: 'title' },
      { header: 'Source', accessorKey: 'source', cell: (info) => <span className="text-muted-foreground">{String(info.getValue())}</span> },
      { header: 'Doc ID', accessorKey: 'doc_id', cell: (info) => <span className="font-mono text-xs">{String(info.getValue())}</span> },
      { header: 'Created', accessorKey: 'created_at', cell: (info) => <span className="text-muted-foreground">{formatEpochSeconds(Number(info.getValue()))}</span> },
    ]
  }, [])

  return (
    <Page
      title="Documents"
      description={
        <span>
          Indexed documents available for retrieval. In public demo mode, these are open-source sample docs only.
        </span>
      }
      actions={
        <div className="flex items-center gap-2">
          <Badge variant="outline">{filtered.length} docs</Badge>
          <Input value={searchRaw} onChange={(e) => setSearchRaw(e.target.value)} placeholder="Search title/source/doc id…" />
        </div>
      }
    >
      <Card>
        <CardHeader>
          <CardTitle>Library</CardTitle>
          <CardDescription>Virtualized table (TanStack Table + Virtual) with debounced client-side search (TanStack Pacer).</CardDescription>
        </CardHeader>
        <CardContent>
          {q.isLoading ? <div className="text-sm text-muted-foreground">Loading…</div> : null}
          {q.isError ? <div className="text-sm text-destructive">Error: {(q.error as Error).message}</div> : null}
          <DataTable<Doc> data={filtered} columns={cols} />
        </CardContent>
      </Card>
    </Page>
  )
}
