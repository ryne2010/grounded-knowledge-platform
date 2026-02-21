import type { IngestionRunSummary } from '../api'

export type IngestionRunFilters = {
  status: string
  triggerType: string
  startedFromDate: string
}

export function statusBadgeVariant(
  status: string,
): 'success' | 'warning' | 'destructive' | 'secondary' | 'outline' {
  const s = String(status || '').toLowerCase()
  if (s === 'succeeded') return 'success'
  if (s === 'running') return 'warning'
  if (s === 'failed') return 'destructive'
  if (s === 'cancelled') return 'secondary'
  return 'outline'
}

export function filterIngestionRuns(
  runs: IngestionRunSummary[],
  filters: IngestionRunFilters,
): IngestionRunSummary[] {
  const statusNeedle = filters.status.trim().toLowerCase()
  const triggerNeedle = filters.triggerType.trim().toLowerCase()
  const minStarted = dateInputToUnixSeconds(filters.startedFromDate)

  return runs.filter((run) => {
    if (statusNeedle && String(run.status || '').toLowerCase() !== statusNeedle) return false
    if (triggerNeedle && String(run.trigger_type || '').toLowerCase() !== triggerNeedle) return false
    if (typeof minStarted === 'number' && Number.isFinite(minStarted) && Number(run.started_at || 0) < minStarted) {
      return false
    }
    return true
  })
}

export function dateInputToUnixSeconds(raw: string): number | null {
  const v = String(raw || '').trim()
  if (!v) return null
  const d = new Date(`${v}T00:00:00`)
  const ms = d.getTime()
  if (!Number.isFinite(ms)) return null
  return Math.floor(ms / 1000)
}

export function runErrorsCount(run: IngestionRunSummary): number {
  return Array.isArray(run.errors) ? run.errors.length : 0
}

export function summarizeRunError(raw: string, maxLen = 220): string {
  const compact = String(raw || '')
    .replace(/\s+/g, ' ')
    .trim()
  if (!compact) return 'Unknown ingestion error'
  if (compact.length <= maxLen) return compact
  return `${compact.slice(0, maxLen)}…`
}
