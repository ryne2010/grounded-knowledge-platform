import * as React from 'react'
import { Link } from '@tanstack/react-router'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { cn } from '../lib/utils'
import { Separator } from '../ui/separator'
import { useOfflineStatus } from '../../lib/offline'

export type NavItem = {
  to: string
  label: string
}

export type AppShellProps = {
  appName: string
  appBadge?: string
  nav: NavItem[]
  docsHref?: string
  repoHref?: string
  headerRight?: React.ReactNode
  children: React.ReactNode
}

function getInitialTheme(): 'light' | 'dark' {
  try {
    const stored = localStorage.getItem('theme')
    return stored === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

export function AppShell(props: AppShellProps) {
  const [theme, setTheme] = React.useState<'light' | 'dark'>(() => getInitialTheme())
  const offline = useOfflineStatus()

  React.useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') root.classList.add('dark')
    else root.classList.remove('dark')
    try {
      localStorage.setItem('theme', theme)
    } catch {}
  }, [theme])

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto flex w-full max-w-[1440px] items-center gap-4 px-4 py-3">
          {/* Brand */}
          <div className="flex items-center gap-3">
            {/* Neutral brand mark (no custom palette/kit required) */}
            <div className="flex h-9 w-9 items-center justify-center rounded-md border bg-muted/30 text-foreground">
              <span className="text-[10px] font-semibold tracking-wide">GKP</span>
            </div>
            <div className="hidden sm:flex sm:flex-col sm:leading-tight">
              <span className="text-sm font-semibold tracking-tight">{props.appName}</span>
              <span className="text-xs text-muted-foreground">Grounded answers with citations</span>
            </div>
            <div className="sm:hidden">
              <span className="text-sm font-semibold tracking-tight">{props.appName}</span>
            </div>
            {props.appBadge ? <Badge variant="secondary">{props.appBadge}</Badge> : null}
          </div>

          {/* Mobile nav (desktop uses sidebar) */}
          <nav className="ml-2 flex items-center gap-1 md:hidden">
            {props.nav.map((item) => (
              <Link
                key={item.to}
                to={item.to as any}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                )}
                activeProps={{
                  className:
                    'rounded-md px-3 py-1.5 text-sm bg-accent text-accent-foreground',
                }}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Header utilities */}
          <div className="ml-auto flex items-center gap-2">
            {props.headerRight}
            {props.docsHref ? (
              <a
                href={props.docsHref}
                className="hidden text-sm text-muted-foreground hover:text-foreground md:inline"
                target="_blank"
                rel="noreferrer"
              >
                API Docs
              </a>
            ) : null}
            {props.repoHref ? (
              <>
                <Separator className="hidden h-5 w-px bg-border md:block" />
                <a
                  href={props.repoHref}
                  className="hidden text-sm text-muted-foreground hover:text-foreground md:inline"
                  target="_blank"
                  rel="noreferrer"
                >
                  Repo
                </a>
              </>
            ) : null}
            <Separator className="h-5 w-px bg-border" />
            <Button
              variant="outline"
              size="sm"
              onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
              aria-label="Toggle theme"
              title="Toggle theme"
            >
              {theme === 'dark' ? 'Light' : 'Dark'}
            </Button>
          </div>
        </div>

        {offline ? (
          <div className="border-t border-amber-300 bg-amber-50 px-4 py-2 text-xs text-amber-900">
            Connection unavailable. Cached pages are still accessible, but live API responses may be stale.
          </div>
        ) : null}
      </header>

      {/* Desktop shell */}
      <div className="mx-auto flex w-full max-w-[1440px] flex-1">
        <aside className="hidden w-64 shrink-0 border-r bg-muted/20 md:block">
          <div className="sticky top-[64px] p-3">
            <div className="mb-2 px-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Navigation
            </div>
            <nav className="space-y-1">
              {props.nav.map((item) => (
                <Link
                  key={item.to}
                  to={item.to as any}
                  className={cn(
                    'block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                  )}
                  activeProps={{
                    className:
                      'block rounded-md px-3 py-2 text-sm bg-accent text-accent-foreground',
                  }}
                >
                  {item.label}
                </Link>
              ))}
            </nav>

            {(props.docsHref || props.repoHref) ? (
              <div className="mt-6 px-2 text-xs text-muted-foreground">
                <div className="mb-2 font-medium uppercase tracking-wide">Links</div>
                <div className="flex flex-col gap-1">
                  {props.docsHref ? (
                    <a href={props.docsHref} target="_blank" rel="noreferrer" className="hover:text-foreground">
                      API Docs
                    </a>
                  ) : null}
                  {props.repoHref ? (
                    <a href={props.repoHref} target="_blank" rel="noreferrer" className="hover:text-foreground">
                      Repo
                    </a>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>
        </aside>

        <main className="min-w-0 flex-1 px-4 py-6">{props.children}</main>
      </div>

      <footer className="border-t py-6">
        <div className="mx-auto flex w-full max-w-[1440px] items-center justify-between gap-3 px-4 text-xs text-muted-foreground">
          <span>Built for production-like workflows (safety-first in public demo mode).</span>
          <span className="hidden sm:inline">© {new Date().getFullYear()} {props.appName}</span>
        </div>
      </footer>
    </div>
  )
}
