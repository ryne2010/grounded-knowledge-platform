import { Outlet, createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'

import { api } from './api'
import { AppShell, Badge } from './portfolio-ui'
import { DocsPage } from './pages/Docs'
import { DashboardPage } from './pages/Dashboard'
import { IngestPage } from './pages/Ingest'
import { DocDetailPage } from './pages/DocDetail'
import { EvalPage } from './pages/Eval'
import { HomePage } from './pages/Home'
import { MaintenancePage } from './pages/Maintenance'
import { MetaPage } from './pages/Meta'
import { SearchPage } from './pages/Search'

function RootLayout() {
  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: 30_000 })
  const meta = metaQuery.data

  const nav = [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/', label: 'Ask' },
    { to: '/search', label: 'Search' },
    { to: '/docs', label: 'Docs' },
    { to: '/ingest', label: 'Ingest' },
    ...(meta?.eval_enabled ? [{ to: '/eval', label: 'Eval' }] : []),
    { to: '/maintenance', label: 'Maintenance' },
    { to: '/meta', label: 'Meta' },
  ]

  const headerRight = (
    <div className="hidden items-center gap-2 md:flex">
      {metaQuery.isError ? (
        <Badge variant="destructive">api error</Badge>
      ) : meta ? (
        <>
          {meta.public_demo_mode ? <Badge variant="warning">demo</Badge> : <Badge variant="success">private</Badge>}
          {meta.citations_required && <Badge variant="secondary">citations</Badge>}
          <Badge variant="outline">llm:{meta.llm_provider}</Badge>
        </>
      ) : (
        <Badge variant="secondary">loading…</Badge>
      )}
    </div>
  )

  return (
    <AppShell
      appName="Grounded Knowledge Platform"
      appBadge={meta?.version ? `v${meta.version}` : 'v—'}
      nav={nav}
      docsHref="/api/swagger"
      headerRight={headerRight}
    >
      <Outlet />
    </AppShell>
  )
}

const rootRoute = createRootRoute({ component: RootLayout })

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  component: DashboardPage,
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: HomePage,
})

const docsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/docs',
  component: DocsPage,
})

const ingestRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/ingest',
  component: IngestPage,
})

const docDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/docs/$docId',
  component: DocDetailPage,
})

const evalRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/eval',
  component: EvalPage,
})

const maintenanceRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/maintenance',
  component: MaintenancePage,
})

const metaRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/meta',
  component: MetaPage,
})

const searchRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/search',
  component: SearchPage,
})

const routeTree = rootRoute.addChildren([
  dashboardRoute,
  indexRoute,
  searchRoute,
  docsRoute,
  ingestRoute,
  docDetailRoute,
  evalRoute,
  maintenanceRoute,
  metaRoute,
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
