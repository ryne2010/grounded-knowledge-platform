import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { useMemo, useState } from 'react'

import { api, Doc } from '../api'
import { formatUnixSeconds } from '../lib/time'
import { Badge, Card, CardContent, CardDescription, CardHeader, CardTitle, DataTable, Input, Page, Section, Spinner } from '../portfolio-ui'


const RETENTION_TTLS_SECONDS: Record<string, number> = {
  '30d': 30 * 24 * 60 * 60,
  '90d': 90 * 24 * 60 * 60,
  '1y': 365 * 24 * 60 * 60,
}

function isExpired(doc: Doc, nowSec: number): boolean {
  const ttl = RETENTION_TTLS_SECONDS[String(doc.retention)]
  if (!ttl) return false
  return Number(doc.updated_at) <= nowSec - ttl
}

export function DocsPage() {
  const [q, setQ] = useState('')

  const docsQuery = useQuery({
    queryKey: ['docs'],
    queryFn: api.listDocs,
    staleTime: 5_000,
  })

  const docs = docsQuery.data?.docs ?? []

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase()
    if (!needle) return docs
    return docs.filter((d) => {
      const hay = `${d.title} ${d.source} ${d.classification} ${d.tags.join(' ')}`.toLowerCase()
      return hay.includes(needle)
    })
  }, [docs, q])

  const columns = useMemo(
    () => [
      {
        header: 'Title',
        accessorKey: 'title',
        cell: (info: any) => {
          const d = info.row.original as Doc
          return (
            <div className="space-y-1">
              <div className="font-medium">
                <Link to="/docs/$docId" params={{ docId: d.doc_id }} className="hover:underline">
                  {d.title}
                </Link>
              </div>
              <div className="text-xs text-muted-foreground">{d.source}</div>
            </div>
          )
        },
      },
      {
        header: 'Classification',
        accessorKey: 'classification',
        cell: (info: any) => {
          const v = String(info.getValue() ?? '')
          return <Badge variant="outline">{v}</Badge>
        },
      },
      {
        header: 'Retention',
        accessorKey: 'retention',
        cell: (info: any) => {
          const v = String(info.getValue() ?? '')
          return <Badge variant="outline">{v}</Badge>
        },
      },
      {
        header: 'Status',
        accessorKey: 'status',
        cell: (info: any) => {
          const d = info.row.original as Doc
          const nowSec = Math.floor(Date.now() / 1000)
          const expired = isExpired(d, nowSec)
          if (expired) return <Badge variant="destructive">expired</Badge>
          const ttl = RETENTION_TTLS_SECONDS[String(d.retention)]
          if (ttl) return <Badge variant="warning">active</Badge>
          return <Badge variant="success">kept</Badge>
        },
      },
      {
        header: 'Tags',
        accessorKey: 'tags',
        cell: (info: any) => {
          const d = info.row.original as Doc
          return d.tags.length ? (
            <div className="flex flex-wrap gap-1">
              {d.tags.slice(0, 4).map((t) => (
                <Badge key={t} variant="secondary">
                  {t}
                </Badge>
              ))}
              {d.tags.length > 4 ? <Badge variant="secondary">+{d.tags.length - 4}</Badge> : null}
            </div>
          ) : (
            <span className="text-xs text-muted-foreground">—</span>
          )
        },
      },
      { header: 'Chunks', accessorKey: 'num_chunks' },
      {
        header: 'Version',
        accessorKey: 'doc_version',
        cell: (info: any) => <span className="font-mono text-xs">v{String(info.getValue() ?? '')}</span>,
      },
      {
        header: 'Updated',
        accessorKey: 'updated_at',
        cell: (info: any) => <span className="text-xs">{formatUnixSeconds(Number(info.getValue() ?? 0))}</span>,
      },
    ],
    [],
  )

  return (
    <Page>
      <Section title="Docs" description="Browse the indexed documents (metadata + versioning).">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Documents
              <Badge variant="secondary">{filtered.length}</Badge>
            </CardTitle>
            <CardDescription>
              Click a doc title for details, ingest history, and chunks (when enabled).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by title/source/tag…" />
            {docsQuery.isLoading ? <Spinner /> : null}
            {docsQuery.isError ? (
              <div className="rounded-md border bg-destructive/10 p-3 text-sm">{(docsQuery.error as Error).message}</div>
            ) : null}
            <DataTable<Doc> data={filtered} columns={columns} height={520} />
          </CardContent>
        </Card>
      </Section>
    </Page>
  )
}
