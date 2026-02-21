import { describe, expect, it } from 'vitest'

import type { IngestionRunSummary } from '../api'
import {
  dateInputToUnixSeconds,
  filterIngestionRuns,
  runErrorsCount,
  statusBadgeVariant,
  summarizeRunError,
} from './ingestionRuns'

function run(overrides: Partial<IngestionRunSummary>): IngestionRunSummary {
  return {
    run_id: 'r1',
    started_at: 1730000000,
    finished_at: 1730000300,
    status: 'succeeded',
    trigger_type: 'connector',
    trigger_payload: {},
    principal: 'api_key:abcd',
    objects_scanned: 5,
    docs_changed: 2,
    docs_unchanged: 3,
    bytes_processed: 1024,
    errors: [],
    event_count: 2,
    ...overrides,
  }
}

describe('statusBadgeVariant', () => {
  it('maps known statuses to consistent badge variants', () => {
    expect(statusBadgeVariant('succeeded')).toBe('success')
    expect(statusBadgeVariant('running')).toBe('warning')
    expect(statusBadgeVariant('failed')).toBe('destructive')
    expect(statusBadgeVariant('cancelled')).toBe('secondary')
    expect(statusBadgeVariant('other')).toBe('outline')
  })
})

describe('filterIngestionRuns', () => {
  const runs = [
    run({ run_id: 'a', status: 'succeeded', trigger_type: 'connector', started_at: 1730000000 }),
    run({ run_id: 'b', status: 'failed', trigger_type: 'cli', started_at: 1730500000 }),
    run({ run_id: 'c', status: 'running', trigger_type: 'ui', started_at: 1731000000 }),
  ]

  it('filters by status and trigger type', () => {
    const out = filterIngestionRuns(runs, {
      status: 'failed',
      triggerType: 'cli',
      startedFromDate: '',
    })
    expect(out.map((r) => r.run_id)).toEqual(['b'])
  })

  it('filters by start date when provided', () => {
    const out = filterIngestionRuns(runs, {
      status: '',
      triggerType: '',
      startedFromDate: '2024-11-05',
    })
    expect(out.map((r) => r.run_id)).toEqual(['c'])
  })
})

describe('dateInputToUnixSeconds and runErrorsCount', () => {
  it('handles invalid date and counts errors safely', () => {
    expect(dateInputToUnixSeconds('')).toBeNull()
    expect(dateInputToUnixSeconds('not-a-date')).toBeNull()
    expect(runErrorsCount(run({ errors: ['a', 'b'] }))).toBe(2)
  })
})

describe('summarizeRunError', () => {
  it('returns compacted and bounded error text', () => {
    expect(summarizeRunError('   upstream\n\n timeout   ')).toBe('upstream timeout')
    expect(summarizeRunError('', 50)).toBe('Unknown ingestion error')
    expect(summarizeRunError('x'.repeat(20), 10)).toBe(`${'x'.repeat(10)}…`)
  })
})
