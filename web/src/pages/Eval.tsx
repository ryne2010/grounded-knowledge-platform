import { useMutation, useQuery } from '@tanstack/react-query'
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

export function EvalPage() {
  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: 30_000 })
  const meta = metaQuery.data
  const enabled = Boolean(meta?.eval_enabled)

  const [goldenPath, setGoldenPath] = React.useState('data/eval/golden.jsonl')
  const [kStr, setKStr] = React.useState('5')

  const k = clampInt(parseInt(kStr || '5', 10), 1, 20)
  const goldenOk = Boolean(goldenPath.trim())

  const runMutation = useMutation({
    mutationFn: async () => api.runEval({ golden_path: goldenPath.trim(), k, include_details: true }),
  })

  return (
    <Page>
      <Section title="Eval" description="Run retrieval evaluation against a JSONL golden set.">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Retrieval eval
              {meta?.public_demo_mode ? <Badge variant="warning">demo</Badge> : null}
              {!enabled ? <Badge variant="secondary">disabled</Badge> : <Badge variant="outline">enabled</Badge>}
            </CardTitle>
            <CardDescription>
              This endpoint is disabled in <span className="font-mono">PUBLIC_DEMO_MODE</span>. For private deployments,
              enable <span className="font-mono">ALLOW_EVAL=1</span>.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {!enabled ? (
              <div className="rounded-md border bg-muted p-3 text-sm text-muted-foreground">Eval is disabled.</div>
            ) : (
              <>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="md:col-span-2 space-y-2">
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
                  <Button
                    onClick={() => runMutation.mutate()}
                    disabled={!goldenOk || runMutation.isPending}
                  >
                    {runMutation.isPending ? (
                      <span className="inline-flex items-center gap-2">
                        <Spinner size="sm" /> Running…
                      </span>
                    ) : (
                      'Run eval'
                    )}
                  </Button>

                  {!goldenOk ? (
                    <span className="text-sm text-muted-foreground">Provide a golden set path.</span>
                  ) : null}
                </div>

                {runMutation.isError ? (
                  <div className="rounded-md border bg-destructive/10 p-3 text-sm">{(runMutation.error as Error).message}</div>
                ) : null}

                {runMutation.isSuccess ? (
                  <div className="space-y-3">
                    <div className="rounded-md border bg-emerald-500/10 p-3 text-sm">
                      <div>examples: {runMutation.data.examples}</div>
                      <div>
                        hit@{k}: {runMutation.data.hit_at_k.toFixed(3)}
                      </div>
                      <div>mrr: {runMutation.data.mrr.toFixed(3)}</div>
                    </div>

                    {runMutation.data.details?.length ? (
                      <div className="space-y-2">
                        <div className="text-sm font-medium">Per-example details</div>
                        <div className="space-y-2">
                          {runMutation.data.details.map((ex, i) => (
                            <details key={i} className="rounded-md border p-3">
                              <summary className="cursor-pointer select-none">
                                <span className="font-mono text-xs text-muted-foreground mr-2">#{i + 1}</span>
                                {ex.hit ? <Badge variant="outline">hit</Badge> : <Badge variant="warning">miss</Badge>}
                                <span className="ml-2 text-sm">{ex.question}</span>
                                <span className="ml-2 text-xs text-muted-foreground">
                                  {ex.rank ? `rank ${ex.rank}` : 'rank —'} · rr {ex.rr.toFixed(3)}
                                </span>
                              </summary>

                              <div className="mt-3 space-y-2">
                                <div className="text-xs text-muted-foreground">
                                  expected_doc_ids: {ex.expected_doc_ids.length ? ex.expected_doc_ids.join(', ') : '—'}
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  expected_chunk_ids: {ex.expected_chunk_ids.length ? ex.expected_chunk_ids.join(', ') : '—'}
                                </div>

                                <div className="mt-2">
                                  <div className="text-xs font-medium mb-1">Top {k} retrieved</div>
                                  <div className="space-y-2">
                                    {ex.retrieved.map((r, j) => (
                                      <div key={j} className="rounded border bg-muted/30 p-2">
                                        <div className="font-mono text-xs">
                                          {j + 1}. doc {r.doc_id} · chunk {r.chunk_id} · idx {r.idx}
                                        </div>
                                        <div className="text-xs text-muted-foreground">
                                          score {r.score.toFixed(4)} (lex {r.lexical_score.toFixed(4)} · vec {r.vector_score.toFixed(4)})
                                        </div>
                                        <div className="mt-1 text-xs">{r.text_preview}</div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </details>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </>
            )}
          </CardContent>
        </Card>
      </Section>
    </Page>
  )
}
