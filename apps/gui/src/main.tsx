import { createRoot } from 'react-dom/client'
import { ErrorBoundary } from 'react-error-boundary'
import '@github/spark/spark'

import App from './App.tsx'
import { ErrorFallback } from './ErrorFallback.tsx'
import './main.css'
import './styles/theme.css'
import './index.css'

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
})

window.addEventListener('error', (event) => {
  console.error('Unhandled application error:', event.error)
})

const root = document.getElementById('root')

if (!root) {
  throw new Error('Physics Foundry root element was not found')
}

createRoot(root).render(
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <App />
  </ErrorBoundary>,
)
