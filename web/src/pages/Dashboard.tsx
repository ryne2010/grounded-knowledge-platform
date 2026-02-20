import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { api } from '../api'
import { Badge, Card, CardContent, CardHeader, CardTitle, Page, Separator } from '../portfolio-ui'

function formatBool(v: boolean) {
  return v ? 'enabled' : 'disabled'
}

export function DashboardPage() {
  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: 30_000 })
  const statsQuery = useQuery({ queryKey: ['stats'], queryFn: api.stats, staleTime: 5_000 })
  const eventsQuery = useQuery({ queryKey: ['recent-ingest-events'], queryFn: () => api.listIngestEvents(100), staleTime: 5_000 })

  const meta = metaQuery.data ?? null
  const stats = statsQuery.data ?? null
  const error = (metaQuery.error || statsQuery.error) as any

  const topTags = useMemo(() => {
    if (!stats?.top_tags) return []
    return stats.top_tags.slice(0, 20)
  }, [stats])

  const validationFailures = useMemo(() => {
    const events = eventsQuery.data?.events ?? []
    return events
      .filter((e) => String(e.validation_status ?? '').toLowerCase() === 'fail')
      .slice(0, 8)
  }, [eventsQuery.data])

  return (
    <Page title="Dashboard" description="Index health, config flags, and quick diagnostics">
      {error && <div className="text-sm text-red-600">{String(error?.message ?? error)}</div>}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Docs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats?.docs ?? '—'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Chunks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats?.chunks ?? '—'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Embeddings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats?.embeddings ?? '—'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ingest events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{stats?.ingest_events ?? '—'}</div>
          </CardContent>
        </Card>
      </div>

      <Separator className="my-6" />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Deployment flags</CardTitle>
          </CardHeader>
          <CardContent>
            {meta ? (
              <div className="space-y-2 text-sm">
                <div>
                  <div className="text-muted-foreground">Version</div>
                  <div className="font-mono">{meta.version ?? 'unknown'}</div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Badge variant={meta.public_demo_mode ? 'secondary' : 'default'}>
                    PUBLIC_DEMO_MODE: {meta.public_demo_mode ? '1' : '0'}
                  </Badge>
                  <Badge variant={meta.citations_required ? 'default' : 'secondary'}>
                    CITATIONS_REQUIRED: {meta.citations_required ? '1' : '0'}
                  </Badge>
                  <Badge variant={meta.uploads_enabled ? 'default' : 'secondary'}>
                    uploads {formatBool(meta.uploads_enabled)}
                  </Badge>
                  <Badge variant={meta.eval_enabled ? 'default' : 'secondary'}>
                    eval {formatBool(meta.eval_enabled)}
                  </Badge>
                  <Badge variant={meta.chunk_view_enabled ? 'default' : 'secondary'}>
                    chunk view {formatBool(meta.chunk_view_enabled)}
                  </Badge>
                  <Badge variant={meta.doc_delete_enabled ? 'default' : 'secondary'}>
                    doc delete {formatBool(meta.doc_delete_enabled)}
                  </Badge>
                </div>

                <div className="pt-2">
                  <div className="text-muted-foreground">Provider</div>
                  <div>
                    LLM: <span className="font-mono">{meta.llm_provider}</span>
                  </div>
                  <div>
                    Embeddings: <span className="font-mono">{meta.embeddings_backend}</span>
                  </div>
                  <div>
                    OCR: <span className="font-mono">{meta.ocr_enabled ? 'enabled' : 'disabled'}</span>
                  </div>
                </div>

                <div className="pt-2">
                  <div className="text-muted-foreground">Upload limit</div>
                  <div className="font-mono">{meta.max_upload_bytes.toLocaleString()} bytes</div>
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">Loading…</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Index signature</CardTitle>
          </CardHeader>
          <CardContent>
            {meta?.index_signature ? (
              <div className="space-y-1 text-sm">
                {Object.entries(meta.index_signature).map(([k, v]) => (
                  <div key={k} className="flex items-start justify-between gap-2">
                    <div className="font-mono text-xs text-muted-foreground">{k}</div>
                    <div className="font-mono text-xs">{String(v ?? '')}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No signature yet (empty index).</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Separator className="my-6" />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Docs by classification</CardTitle>
          </CardHeader>
          <CardContent>
            {stats ? (
              <div className="space-y-1 text-sm">
                {Object.entries(stats.by_classification)
                  .sort((a, b) => b[1] - a[1])
                  .map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between">
                      <span className="font-mono">{k}</span>
                      <span className="font-mono">{v}</span>
                    </div>
                  ))}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">Loading…</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Docs by retention</CardTitle>
          </CardHeader>
          <CardContent>
            {stats ? (
              <div className="space-y-1 text-sm">
                {Object.entries(stats.by_retention)
                  .sort((a, b) => b[1] - a[1])
                  .map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between">
                      <span className="font-mono">{k}</span>
                      <span className="font-mono">{v}</span>
                    </div>
                  ))}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">Loading…</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Separator className="my-6" />

      <Card>
        <CardHeader>
          <CardTitle>Top tags</CardTitle>
        </CardHeader>
        <CardContent>
          {topTags.length ? (
            <div className="flex flex-wrap gap-2">
              {topTags.map((t) => (
                <Badge key={t.tag} variant="secondary">
                  {t.tag} · {t.count}
                </Badge>
              ))}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No tags yet.</div>
          )}
        </CardContent>
      </Card>

      <Separator className="my-6" />

      <Card>
        <CardHeader>
          <CardTitle>Recent validation failures</CardTitle>
        </CardHeader>
        <CardContent>
          {validationFailures.length ? (
            <div className="space-y-2 text-sm">
              {validationFailures.map((e) => (
                <div key={e.event_id} className="rounded border p-2">
                  <div className="font-medium">{e.doc_title}</div>
                  <div className="text-xs text-muted-foreground font-mono">{e.doc_id}</div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    <Badge variant="destructive">fail</Badge>
                    {e.schema_drifted ? <Badge variant="warning">drift</Badge> : null}
                  </div>
                  {e.validation_errors?.length ? (
                    <div className="mt-1 text-xs text-destructive">
                      {e.validation_errors.slice(0, 2).join(' · ')}
                      {e.validation_errors.length > 2 ? ' …' : ''}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No recent validation failures.</div>
          )}
        </CardContent>
      </Card>
    </Page>
  )
}
