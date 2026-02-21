import { describe, expect, it } from 'vitest'

import { buildMetadataUpdatePayload, normalizeMetadataTags, toActionableApiError } from './governanceMetadata'

describe('normalizeMetadataTags', () => {
  it('lowercases, trims, slugifies, and de-duplicates tags', () => {
    expect(normalizeMetadataTags(' Alpha,alpha,Hello World, ,ops:Runbook,ops:runbook')).toEqual([
      'alpha',
      'hello-world',
      'ops:runbook',
    ])
  })
})

describe('buildMetadataUpdatePayload', () => {
  it('returns a normalized payload for valid metadata', () => {
    const result = buildMetadataUpdatePayload({
      title: '  Quarterly Plan  ',
      source: '  wiki://plan  ',
      classification: ' Internal ',
      retention: ' 90D ',
      tagsRaw: 'alpha, Alpha, hello world',
      allowedClassifications: ['public', 'internal', 'confidential', 'restricted'],
      allowedRetentions: ['none', '30d', '90d', '1y', 'indefinite'],
    })
    expect(result.error).toBeNull()
    expect(result.payload).toEqual({
      title: 'Quarterly Plan',
      source: 'wiki://plan',
      classification: 'internal',
      retention: '90d',
      tags: ['alpha', 'hello-world'],
    })
  })

  it('returns actionable validation errors for invalid canonical values', () => {
    const classificationError = buildMetadataUpdatePayload({
      title: 'Doc',
      source: 'src',
      classification: 'secret',
      retention: '90d',
      tagsRaw: '',
      allowedClassifications: ['public', 'internal'],
      allowedRetentions: ['none', '90d'],
    })
    expect(classificationError.error).toContain('Classification must be one of')

    const retentionError = buildMetadataUpdatePayload({
      title: 'Doc',
      source: 'src',
      classification: 'public',
      retention: 'forever',
      tagsRaw: '',
      allowedClassifications: ['public', 'internal'],
      allowedRetentions: ['none', '90d'],
    })
    expect(retentionError.error).toContain('Retention must be one of')
  })
})

describe('toActionableApiError', () => {
  it('extracts server detail from formatted HTTP error messages', () => {
    expect(toActionableApiError('[req 123] HTTP 400: {"detail":"Invalid classification"}')).toBe(
      'Invalid classification',
    )
  })
})
