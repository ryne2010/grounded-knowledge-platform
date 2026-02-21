import { describe, expect, it } from 'vitest'

import { DEMO_GUIDED_TOUR_STEPS, DEMO_SUGGESTED_QUERIES } from './demoOnboarding'

describe('demo onboarding config', () => {
  it('keeps curated suggested queries in the expected range', () => {
    expect(DEMO_SUGGESTED_QUERIES.length).toBeGreaterThanOrEqual(5)
    expect(DEMO_SUGGESTED_QUERIES.length).toBeLessThanOrEqual(10)
    const unique = new Set(DEMO_SUGGESTED_QUERIES.map((q) => q.trim()))
    expect(unique.size).toBe(DEMO_SUGGESTED_QUERIES.length)
    expect([...unique].every((q) => q.length > 10)).toBe(true)
  })

  it('keeps guided tour steps ordered with unique targets', () => {
    expect(DEMO_GUIDED_TOUR_STEPS.length).toBe(5)
    const targets = DEMO_GUIDED_TOUR_STEPS.map((step) => step.target)
    expect(new Set(targets).size).toBe(targets.length)
    expect(DEMO_GUIDED_TOUR_STEPS[0]?.target).toBe('demo-badge')
    expect(DEMO_GUIDED_TOUR_STEPS[4]?.target).toBe('refusal-behavior')
  })
})
