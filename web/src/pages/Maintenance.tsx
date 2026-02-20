import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { useMemo } from 'react'

import { api, ExpiredDoc } from '../api'
import { formatUnixSeconds } from '../lib/time'
import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  DataTable,
  Page,
  Section,
  Separator,
  Spinner,
} from '../portfolio-ui'

export function MaintenancePage() {
  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: 30_000 })
  const expiredQuery = useQuery({
    queryKey: ['maintenance', 'retention', 'expired'],
    queryFn: () => api.maintenanceRetentionExpired(),
    staleTime: 5_000,
  })

  const expired = expiredQuery.data?.expired ?? []

  const columns = useMemo(
    () => [
      {
        header: 'Doc',
        accessorKey: 'title',
        cell: (info: any) => {
          const row = info.row.original as ExpiredDoc
          return (
            <div className="space-y-0.5">
              <div className="font-medium">
                <Link to="/docs/$docId" params={{ docId: row.doc_id }} className="hover:underline">
                  {row.title}
                </Link>
              </div>
              <div className="font-mono text-[11px] text-muted-foreground">{row.doc_id}</div>
            </div>
          )
        },
      },
      {
        header: 'Retention',
        accessorKey: 'retention',
        cell: (info: any) => <span className="font-mono text-xs">{String(info.getValue() ?? '')}</span>,
      },
      {
        header: 'Updated',
        accessorKey: 'updated_at',
        cell: (info: any) => <span className="text-xs">{formatUnixSeconds(Number(info.getValue() ?? 0))}</span>,
      },
    ],
    [],
  )

  const demo = metaQuery.data?.public_demo_mode ?? false

  return (
    <Page title="Maintenance" description="Read-only operational helpers (no destructive actions)">
      <Section title="Retention" description="See what would be purged based on the doc retention policy.">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Expired docs
              {expiredQuery.isLoading ? <Spinner /> : <Badge variant="secondary">{expired.length}</Badge>}
              {demo && <Badge variant="warning">demo</Badge>}
            </CardTitle>
            <CardDescription>
              This endpoint is read-only. To actually delete expired docs, use the CLI:
              <span className="ml-2 font-mono">make purge-expired</span>
              <span className="mx-1">/</span>
              <span className="font-mono">make purge-expired-apply</span>.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {expiredQuery.isError ? (
              <div className="text-sm text-red-600">{String((expiredQuery.error as any)?.message ?? expiredQuery.error)}</div>
            ) : expiredQuery.isLoading ? (
              <div className="text-sm text-muted-foreground">Loading…</div>
            ) : expired.length ? (
              <DataTable columns={columns as any} data={expired as any} />
            ) : (
              <div className="text-sm text-muted-foreground">No expired docs found.</div>
            )}
          </CardContent>
        </Card>

        <Separator className="my-6" />

        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>
              <span className="font-medium">Why this exists:</span> retention is a governance control.
              The platform models retention policies at the doc level and can purge expired docs.
            </div>
            <div>
              <span className="font-medium">Production tip:</span> Cloud Run has an ephemeral filesystem.
              If you need durable retention enforcement, migrate storage to Cloud SQL (or another managed store)
              and schedule a purge job.
            </div>
          </CardContent>
        </Card>
      </Section>
    </Page>
  )
}
