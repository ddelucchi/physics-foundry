import { useCallback, useEffect, useState } from 'react'
import { Activity, Cpu, Database, Monitor } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface CapabilityResponse {
  mode: string
  capabilities: Record<string, boolean>
  note: string
}

interface StatusResponse {
  status: string
  timestamp: string
  version: string
  mode: string
  gpu_available: boolean
  sandbox_ready: boolean
  quality_gates_enabled: boolean
  capabilities: Record<string, boolean>
  observability: Record<string, boolean>
}

const API_BASE_URL =
  (import.meta.env.VITE_ORCHESTRATOR_URL as string | undefined)?.replace(/\/$/, '') ||
  'http://127.0.0.1:8000'

const CAPABILITY_LABELS: Record<string, string> = {
  fixture_mode: 'Fixture mode',
  manim_cli: 'Manim CLI',
  ffmpeg: 'FFmpeg',
  blender: 'Blender',
  taichi_python: 'Taichi Python',
  latex: 'LaTeX',
  nvidia_smi: 'NVIDIA tooling',
  firejail: 'Firejail installed',
  nsjail: 'nsjail installed',
  sandbox_execution_supported: 'Supported sandbox backend',
  local_llm_configured: 'Local LLM endpoint configured',
}

export default function SystemMonitor() {
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [capabilities, setCapabilities] = useState<CapabilityResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)

    try {
      const [statusResponse, capabilityResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/status`, { headers: { Accept: 'application/json' } }),
        fetch(`${API_BASE_URL}/capabilities`, { headers: { Accept: 'application/json' } }),
      ])

      if (!statusResponse.ok || !capabilityResponse.ok) {
        throw new Error(
          `orchestrator returned HTTP ${statusResponse.status}/${capabilityResponse.status}`,
        )
      }

      const [nextStatus, nextCapabilities] = await Promise.all([
        statusResponse.json() as Promise<StatusResponse>,
        capabilityResponse.json() as Promise<CapabilityResponse>,
      ])

      setStatus(nextStatus)
      setCapabilities(nextCapabilities)
      setError(null)
      setLastUpdated(new Date())
    } catch (caught) {
      setStatus(null)
      setCapabilities(null)
      setError(caught instanceof Error ? caught.message : 'orchestrator unavailable')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    const interval = window.setInterval(() => void refresh(), 5000)
    return () => window.clearInterval(interval)
  }, [refresh])

  const capabilityEntries = Object.entries(capabilities?.capabilities ?? {})
  const availableCount = capabilityEntries.filter(([, available]) => available).length

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>Orchestrator status</CardTitle>
              <p className="mt-1 text-xs text-muted-foreground">
                Live values from {API_BASE_URL}. No random telemetry is generated in this panel.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={status ? 'default' : 'secondary'}>
                {status ? 'Live service data' : 'Service unavailable'}
              </Badge>
              <Button size="sm" variant="outline" onClick={() => void refresh()} disabled={loading}>
                {loading ? 'Checking…' : 'Refresh'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="rounded-md border border-border bg-muted/50 p-4 text-sm">
              <div className="font-medium">No live orchestrator data</div>
              <div className="mt-1 text-muted-foreground">{error}</div>
              <div className="mt-2 text-xs text-muted-foreground">
                Start the API or set <code>VITE_ORCHESTRATOR_URL</code>. This panel intentionally does not fall back to demo hardware statistics.
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Activity size={16} /> Service
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-1 text-sm">
                  <div className="font-mono">{status?.status ?? 'unknown'}</div>
                  <div className="text-xs text-muted-foreground">
                    v{status?.version ?? 'unknown'} · {status?.mode ?? 'unknown'}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Monitor size={16} /> GPU tooling
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge variant={status?.gpu_available ? 'default' : 'secondary'}>
                    {status?.gpu_available ? 'Detected' : 'Not detected'}
                  </Badge>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Cpu size={16} /> Sandbox path
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge
                    variant={capabilities?.capabilities.sandbox_execution_supported ? 'default' : 'secondary'}
                  >
                    {capabilities?.capabilities.sandbox_execution_supported
                      ? 'Supported backend found'
                      : 'Unsupported on host'}
                  </Badge>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Database size={16} /> Dependencies
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-1">
                  <div className="font-mono text-lg">
                    {availableCount}/{capabilityEntries.length}
                  </div>
                  <div className="text-xs text-muted-foreground">reported available</div>
                </CardContent>
              </Card>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Capability matrix</CardTitle>
        </CardHeader>
        <CardContent>
          {capabilityEntries.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Capability data is unavailable until the orchestrator responds.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {capabilityEntries.map(([key, available]) => (
                <div
                  key={key}
                  className="flex items-center justify-between gap-4 rounded-md border p-3"
                >
                  <div>
                    <div className="text-sm font-medium">{CAPABILITY_LABELS[key] ?? key}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">{key}</div>
                  </div>
                  <Badge variant={available ? 'default' : 'secondary'}>
                    {available ? 'Available' : 'Unavailable'}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Evidence boundary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            Capability flags report dependency/configuration availability only. They do not establish that a complete prompt-to-render path works.
          </p>
          <p>
            The sandbox flag reports whether the currently supported isolation backend is present. It does not claim hostile multi-tenant hardening.
          </p>
          <p>
            {lastUpdated
              ? `Last successful service refresh: ${lastUpdated.toLocaleTimeString()}.`
              : 'No successful service refresh has occurred in this session.'}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
