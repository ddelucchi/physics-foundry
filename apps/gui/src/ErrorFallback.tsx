import { FallbackProps } from 'react-error-boundary'
import { AlertTriangleIcon, RefreshCwIcon } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from './components/ui/alert'
import { Button } from './components/ui/button'

export const ErrorFallback = ({ error, resetErrorBoundary }: FallbackProps) => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <Alert variant="destructive" className="mb-6">
          <AlertTriangleIcon />
          <AlertTitle>Physics Foundry encountered a runtime error</AlertTitle>
          <AlertDescription>
            The interface stopped before it could safely continue. No success state is inferred from this failure.
          </AlertDescription>
        </Alert>

        <div className="mb-6 rounded-lg border bg-card p-4">
          <h3 className="mb-2 text-sm font-semibold text-muted-foreground">Error details</h3>
          <pre className="max-h-40 overflow-auto rounded border bg-muted/50 p-3 text-xs text-destructive">
            {error.message}
          </pre>
        </div>

        <Button onClick={resetErrorBoundary} className="w-full gap-2" variant="outline">
          <RefreshCwIcon size={16} />
          Reset interface
        </Button>
      </div>
    </div>
  )
}
