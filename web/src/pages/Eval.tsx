import { Link } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as React from 'react'

import { api } from '../api'
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Page,
  Section,
  Spinner,
} from '../portfolio-ui'

function clampInt(n: number, min: number, max: number): number {
  if (!Number.isFinite(n)) return min
  return Math.max(min, Math.min(max, Math.trunc(n)))
}

function formatTs(ts: number | null | undefined): string {
  if (typeof ts !== 'number' || !Number.isFinite(ts) || ts <= 0) return '—'
  return new Date(ts * 1000).toLocaleString()
}

function formatPct(v: number): string {
  return `${(Math.max(0, Math.min(1, v)) * 100).toFixed(1)}%`
}

function sparklinePoints(values: number[]): string {
  if (!values.length) return ''
  if (values.length === 1) {
    const y = 30 - Math.max(0, Math.min(1, values[0])) * 30
    return `0,${y.toFixed(2)} 100,${y.toFixed(2)}`
  }

  const clamped = values.map((v) => Math.max(0, Math.min(1, v)))
  const min = Math.min(...clamped)
  const max = Math.max(...clamped)
  const range = max - min || 1

  return clamped
    .map((v, i) => {
      const x = (i / (clamped.length - 1)) * 100
      const y = 30 - ((v - min) / range) * 30
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')
}

export function EvalPage() {
  const qc = useQueryClient()
  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: 30_000 })
  const meta = metaQuery.data
  const enabled = Boolean(meta?.eval_enabled)

  const [goldenPath, setGoldenPath] = React.useState('data/eval/golden.jsonl')
  const [kStr, setKStr] = React.useState('5')

  const k = clampInt(parseInt(kStr || '5', 10), 1, 20)
  const goldenOk = Boolean(goldenPath.trim())

  const runsQuery = useQuery({
    queryKey: ['eval-runs'],
    queryFn: () => api.listEvalRuns(50),
    enabled,
    staleTime: 15_000,
  })

  const runMutation = useMutation({
    mutationFn: async () => api.runEval({ golden_path: goldenPath.trim(), k, include_details: true }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['eval-runs'] })
    },
  })

  const history = runsQuery.data?.runs ?? []
  const trend = [...history].reverse().map((r) => Number(r.summary.pass_rate || 0))
  const trendLine = sparklinePoints(trend)

  return (
    <Page>
      <Section title="Eval" description="Run retrieval evaluation, compare runs, and inspect per-case outcomes.">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Retrieval eval
              {meta?.public_demo_mode ? <Badge variant="warning">public read-only</Badge> : null}
              {!enabled ? <Badge variant="secondary">disabled</Badge> : <Badge variant="outline">enabled</Badge>}
            </CardTitle>
            <CardDescription>
              This endpoint is disabled in <span className="font-mono">PUBLIC_DEMO_MODE</span>. For private environments,
              enable <span className="font-mono">ALLOW_EVAL=1</span>.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {!enabled ? (
              <div className="rounded-md border bg-muted p-3 text-sm text-muted-foreground">Eval is disabled.</div>
            ) : (
              <>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="goldenPath">Golden set path</Label>
                    <Input
                      id="goldenPath"
                      value={goldenPath}
                      onChange={(e) => setGoldenPath(e.target.value)}
                      placeholder="data/eval/golden.jsonl"
                    />
                    <div className="text-xs text-muted-foreground">
                      Path is interpreted relative to the server filesystem (e.g. in the container on Cloud Run).
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="k">K</Label>
                    <Input
                      id="k"
                      type="number"
                      min={1}
                      max={20}
                      inputMode="numeric"
                      value={kStr}
                      onChange={(e) => setKStr(e.target.value)}
                    />
                    <div className="text-xs text-muted-foreground">Clamped to 1–20 (current: {k}).</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button onClick={() => runMutation.mutate()} disabled={!goldenOk || runMutation.isPending}>
                    {runMutation.isPending ? (
                      <span className="inline-flex items-center gap-2">
                        <Spinner size="sm" /> Running…
                      </span>
                    ) : (
                      'Run eval'
                    )}
                  </Button>

                  {!goldenOk ? <span className="text-sm text-muted-foreground">Provide a golden set path.</span> : null}
                </div>

                {runMutation.isError ? (
                  <div className="rounded-md border bg-destructive/10 p-3 text-sm">{(runMutation.error as Error).message}</div>
                ) : null}

                {runMutation.isSuccess ? (
                  <div className="rounded-md border bg-emerald-500/10 p-3 text-sm">
                    <div className="font-medium">Run {runMutation.data.run_id}</div>
                    <div>
                      pass rate {formatPct(runMutation.data.pass_rate)} · pass {runMutation.data.passed}/{runMutation.data.examples}
                    </div>
                    <div>
                      hit@{runMutation.data.k}: {runMutation.data.hit_at_k.toFixed(3)} · mrr {runMutation.data.mrr.toFixed(3)}
                    </div>
                    <div className="mt-2">
                      <Link className="underline" to="/eval/runs/$runId" params={{ runId: runMutation.data.run_id }}>
                        Open run details
                      </Link>
                    </div>
                  </div>
                ) : null}
              </>
            )}
          </CardContent>
        </Card>

        {enabled ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-2">
                <span>Eval history</span>
                {runsQuery.isFetching ? <Badge variant="outline">refreshing</Badge> : null}
              </CardTitle>
              <CardDescription>Recent runs with aggregate metrics and run-to-run deltas.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {runsQuery.isLoading ? (
                <div className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                  <Spinner size="sm" /> Loading runs…
                </div>
              ) : runsQuery.isError ? (
                <div className="rounded-md border bg-destructive/10 p-3 text-sm">{(runsQuery.error as Error).message}</div>
              ) : history.length === 0 ? (
                <div className="rounded-md border bg-muted p-3 text-sm text-muted-foreground">No eval runs yet.</div>
              ) : (
                <>
                  <div className="rounded-md border p-3">
                    <div className="mb-2 text-sm font-medium">Pass-rate trend</div>
                    <div className="flex items-center gap-3">
                      <svg viewBox="0 0 100 30" className="h-10 w-48" aria-label="Eval pass-rate trend sparkline">
                        <polyline
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          points={trendLine}
                          className="text-primary"
                        />
                      </svg>
                      <div className="text-xs text-muted-foreground">
                        latest {formatPct(history[0].summary.pass_rate)} · {history.length} run{history.length === 1 ? '' : 's'}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    {history.map((run) => (
                      <div key={run.run_id} className="rounded-md border p-3">
                        <div className="flex flex-wrap items-center gap-2 text-sm">
                          <Badge variant={run.status === 'succeeded' ? 'success' : 'destructive'}>{run.status}</Badge>
                          <span className="font-mono text-xs text-muted-foreground">{run.run_id}</span>
                          <span className="text-muted-foreground">{formatTs(run.started_at)}</span>
                          <span className="text-muted-foreground">dataset {run.dataset_name}</span>
                        </div>

                        <div className="mt-2 text-sm">
                          pass {run.summary.passed}/{run.summary.examples} ({formatPct(run.summary.pass_rate)}) · hit@{run.k}{' '}
                          {run.summary.hit_at_k.toFixed(3)} · mrr {run.summary.mrr.toFixed(3)}
                        </div>

                        <div className="mt-1 text-xs text-muted-foreground">
                          delta pass-rate {(run.diff_from_prev.delta.pass_rate * 100).toFixed(1)}pp · regressions{' '}
                          {run.diff_from_prev.case_changes.regressions} · improvements {run.diff_from_prev.case_changes.improvements}
                        </div>

                        <div className="mt-2 text-sm">
                          <Link className="underline" to="/eval/runs/$runId" params={{ runId: run.run_id }}>
                            View details
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        ) : null}
      </Section>
    </Page>
  )
}
