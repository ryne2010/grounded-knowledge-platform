import { useQuery } from '@tanstack/react-query'
import { api } from '../api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Page } from '../portfolio-ui'

export function MetaPage() {
  const q = useQuery({ queryKey: ['meta'], queryFn: api.meta })

  return (
    <Page
      title="Meta"
      description="Runtime flags and configuration (useful for operations, audits, and runbooks)."
    >
      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
          <CardDescription>This endpoint is intentionally safe to expose in public read-only environments.</CardDescription>
        </CardHeader>
        <CardContent>
          {q.isLoading ? <div className="text-sm text-muted-foreground">Loading…</div> : null}
          {q.isError ? <div className="text-sm text-destructive">Error: {(q.error as Error).message}</div> : null}
          {q.data ? (
            <pre className="overflow-x-auto rounded-md border bg-muted/30 p-4 text-xs">
{JSON.stringify(q.data, null, 2)}
            </pre>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notes</CardTitle>
          <CardDescription>Local-first hosting option</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div>
            <span className="font-medium">What it means:</span> you can run this platform as a single local service using
            SQLite (no Cloud SQL required).
          </div>
          <div>
            <span className="font-medium">How to tell:</span> in the configuration above,{' '}
            <span className="font-mono">database_backend</span> is <span className="font-mono">sqlite</span> when running
            local-first.
          </div>
          <div>
            <span className="font-medium">When to use it:</span> local development, demos, and low-cost single-operator
            setups.
          </div>
          <div>
            <span className="font-medium">Hosted durability:</span> for durable multi-revision hosting, set{' '}
            <span className="font-mono">DATABASE_URL</span> so the app uses Postgres/Cloud SQL instead of local disk.
          </div>
        </CardContent>
      </Card>
    </Page>
  )
}
