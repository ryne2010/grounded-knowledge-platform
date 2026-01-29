import { createRootRoute, createRoute, createRouter, Outlet } from '@tanstack/react-router'
import { AppShell, PortfolioDevtools } from './portfolio-ui'
import { HomePage } from './pages/Home'
import { DocsPage } from './pages/Docs'
import { MetaPage } from './pages/Meta'

const rootRoute = createRootRoute({
  component: () => (
    <AppShell
      appName="Grounded Knowledge Platform"
      appBadge="Public Demo Safe"
      nav={[
        { to: '/', label: 'Ask' },
        { to: '/documents', label: 'Documents' },
        { to: '/meta', label: 'Meta' },
      ]}
      docsHref="/docs"
    >
      <Outlet />
      <PortfolioDevtools />
    </AppShell>
  ),
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: HomePage,
})

const docsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/documents',
  component: DocsPage,
})

const metaRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/meta',
  component: MetaPage,
})

export const routeTree = rootRoute.addChildren([indexRoute, docsRoute, metaRoute])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
