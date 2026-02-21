import { Link, useParams } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'

import { api } from '../api'
import { Badge, Card, CardContent, CardHeader, CardTitle, Page, Section, Spinner } from '../portfolio-ui'

function formatTs(ts: number | null | undefined): string {
  if (typeof ts !== 'number' || !Number.isFinite(ts) || ts <= 0) return '—'
  return new Date(ts * 1000).toLocaleString()
}

function formatPct(v: number): string {
  return `${(Math.max(0, Math.min(1, v)) * 100).toFixed(1)}%`
}

export function EvalRunDetailPage() {
  const { runId } = useParams({ from: '/eval/runs/$runId' })

  const detailQuery = useQuery({
    queryKey: ['eval-run', runId],
    queryFn: () => api.getEvalRun(runId),
    staleTime: 15_000,
  })

  if (detailQuery.isLoading) {
    return (
      <Page>
        <Section title="Eval run detail" description="Loading run details.">
          <div className="inline-flex items-center gap-2 text-sm text-muted-foreground">
            <Spinner size="sm" /> Loading…
          </div>
        </Section>
      </Page>
    )
  }

  if (detailQuery.isError) {
    return (
      <Page>
        <Section title="Eval run detail" description="Could not load run details.">
          <div className="rounded-md border bg-destructive/10 p-3 text-sm">{(detailQuery.error as Error).message}</div>
          <div className="mt-3 text-sm">
            <Link to="/eval" className="underline">
              Back to eval history
            </Link>
          </div>
        </Section>
      </Page>
    )
  }

  if (!detailQuery.data) {
    return (
      <Page>
        <Section title="Eval run detail" description="Run details are unavailable.">
          <div className="rounded-md border bg-muted p-3 text-sm text-muted-foreground">No run details were returned.</div>
          <div className="mt-3 text-sm">
            <Link to="/eval" className="underline">
              Back to eval history
            </Link>
          </div>
        </Section>
      </Page>
    )
  }

  const run = detailQuery.data.run
  const details = detailQuery.data.details
  const regressions = new Set(run.diff_from_prev.case_changes.regression_case_ids)
  const improvements = new Set(run.diff_from_prev.case_changes.improvement_case_ids)

  return (
    <Page>
      <Section
        title="Eval run detail"
        description={`Run ${run.run_id} · dataset ${run.dataset_name} · started ${formatTs(run.started_at)}`}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex flex-wrap items-center gap-2">
              <Badge variant={run.status === 'succeeded' ? 'success' : 'destructive'}>{run.status}</Badge>
              <span className="font-mono text-xs text-muted-foreground">{run.run_id}</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>
              pass {run.summary.passed}/{run.summary.examples} ({formatPct(run.summary.pass_rate)}) · hit@{run.k}{' '}
              {run.summary.hit_at_k.toFixed(3)} · mrr {run.summary.mrr.toFixed(3)}
            </div>
            <div className="text-muted-foreground">
              started {formatTs(run.started_at)} · finished {formatTs(run.finished_at)}
            </div>
            <div className="text-muted-foreground">
              app {run.app_version} · embeddings {run.embeddings_backend}/{run.embeddings_model} · provider{' '}
              {run.provider_config.provider}
              {run.provider_config.model ? `/${run.provider_config.model}` : ''}
            </div>
            <div className="text-muted-foreground">
              retrieval k={run.retrieval_config.k} · hybrid lexical {run.retrieval_config.hybrid_weights.lexical.toFixed(2)} / vector{' '}
              {run.retrieval_config.hybrid_weights.vector.toFixed(2)}
            </div>
            <div className="text-muted-foreground">
              delta pass-rate {(run.diff_from_prev.delta.pass_rate * 100).toFixed(1)}pp · delta hit@k{' '}
              {run.diff_from_prev.delta.hit_at_k.toFixed(3)} · delta mrr {run.diff_from_prev.delta.mrr.toFixed(3)}
            </div>
            <div className="text-muted-foreground">
              regressions {run.diff_from_prev.case_changes.regressions} · improvements{' '}
              {run.diff_from_prev.case_changes.improvements} · unchanged {run.diff_from_prev.case_changes.unchanged}
            </div>
            <div className="pt-1">
              <Link to="/eval" className="underline">
                Back to eval history
              </Link>
              {run.diff_from_prev.previous_run_id ? (
                <>
                  {' '}
                  ·{' '}
                  <Link to="/eval/runs/$runId" params={{ runId: run.diff_from_prev.previous_run_id }} className="underline">
                    Open previous run
                  </Link>
                </>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Case results</CardTitle>
          </CardHeader>
          <CardContent>
            {!details.length ? (
              <div className="rounded-md border bg-muted p-3 text-sm text-muted-foreground">No per-case details were stored.</div>
            ) : (
              <div className="space-y-2">
                {details.map((d) => {
                  const caseId = d.case_id
                  const status = d.status
                  const change = regressions.has(caseId)
                    ? 'regressed'
                    : improvements.has(caseId)
                      ? 'improved'
                      : 'unchanged'

                  return (
                    <details key={caseId} className="rounded-md border p-3">
                      <summary className="cursor-pointer select-none">
                        <span className="mr-2 font-mono text-xs text-muted-foreground">{caseId}</span>
                        <Badge variant={status === 'pass' ? 'success' : 'warning'}>{status}</Badge>
                        <span className="ml-2 text-sm">{d.question}</span>
                        <span className="ml-2 text-xs text-muted-foreground">
                          {change} · rank {d.rank ?? '—'} · rr {Number(d.rr || 0).toFixed(3)}
                        </span>
                      </summary>

                      <div className="mt-3 space-y-2 text-xs text-muted-foreground">
                        <div>
                          expected_doc_ids: {d.expected_doc_ids.length ? d.expected_doc_ids.join(', ') : '—'}
                        </div>
                        <div>
                          expected_chunk_ids: {d.expected_chunk_ids.length ? d.expected_chunk_ids.join(', ') : '—'}
                        </div>
                        <div className="text-foreground">
                          Top retrieved: {d.retrieved.length}
                        </div>
                        <div className="space-y-1">
                          {d.retrieved.map((r, idx) => (
                            <div key={`${caseId}-${r.chunk_id}-${idx}`} className="rounded border bg-muted/30 p-2">
                              <div className="font-mono">
                                {idx + 1}. doc {r.doc_id} · chunk {r.chunk_id} · idx {r.idx}
                              </div>
                              <div>
                                score {Number(r.score).toFixed(4)} (lex {Number(r.lexical_score).toFixed(4)} · vec{' '}
                                {Number(r.vector_score).toFixed(4)})
                              </div>
                              <div className="mt-1 text-foreground">{r.text_preview}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </details>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </Section>
    </Page>
  )
}
