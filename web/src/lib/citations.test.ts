import { beforeEach, describe, expect, it, vi } from 'vitest'

import { buildDocCitationHref, parseCitationJump, scrollToCitationTarget } from './citations'

describe('citation navigation', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    window.history.replaceState({}, '', '/')
  })

  it('clicking a citation link navigates and focuses the highlighted target', () => {
    const href = buildDocCitationHref(
      'doc-123',
      {
        chunk_id: 'chunk-42',
        quote: 'evidence snippet',
        doc_title: 'Deployment ADR',
        doc_source: 'docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md',
      },
      0.913,
    )

    const target = document.createElement('button')
    target.dataset.citationTarget = 'chunk-42'
    const scrollSpy = vi.fn()
    const focusSpy = vi.fn()
    Object.defineProperty(target, 'scrollIntoView', { value: scrollSpy, configurable: true })
    Object.defineProperty(target, 'focus', { value: focusSpy, configurable: true })
    document.body.appendChild(target)

    const link = document.createElement('a')
    link.href = href
    link.textContent = 'Open doc context'
    link.addEventListener('click', (event) => {
      event.preventDefault()
      const nextHref = link.getAttribute('href')
      if (!nextHref) return
      window.history.pushState({}, '', nextHref)
      const jump = parseCitationJump(window.location.search)
      if (jump) {
        scrollToCitationTarget(jump.chunkId)
      }
    })
    document.body.appendChild(link)

    link.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }))

    expect(window.location.pathname).toBe('/docs/doc-123')
    expect(window.location.search).toContain('cite_chunk=chunk-42')
    expect(scrollSpy).toHaveBeenCalledTimes(1)
    expect(scrollSpy).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' })
    expect(focusSpy).toHaveBeenCalledTimes(1)
    expect(target.getAttribute('tabindex')).toBe('-1')
  })
})
