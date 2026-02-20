import * as React from 'react'

import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from './portfolio-ui'

type Props = {
  children: React.ReactNode
}

type State = {
  error: Error | null
}

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Intentionally log to console; this is a last-resort crash surface.
    console.error('UI error boundary caught an error:', error, info)
  }

  render() {
    const error = this.state.error
    if (!error) return this.props.children

    return (
      <div className="mx-auto max-w-3xl p-6">
        <Card>
          <CardHeader>
            <CardTitle>Something went wrong</CardTitle>
            <CardDescription>The UI hit an unexpected error. Reloading usually fixes this.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="rounded-md border bg-muted/30 p-3 text-sm whitespace-pre-wrap">{error.message}</div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => window.location.reload()}>Reload</Button>
              <Button
                variant="outline"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(String(error.stack ?? error.message))
                  } catch {
                    // ignore
                  }
                }}
              >
                Copy error
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }
}
