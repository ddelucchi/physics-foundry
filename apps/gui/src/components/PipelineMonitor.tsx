import { useEffect, useRef, useState } from 'react'
import { Activity, AlertCircle, Brain, CheckCircle, Clock, Play, RotateCcw, Video } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PhysicsVideoRequest } from '@/lib/pipeline-orchestrator'

type PipelineStatus =
  | 'idle'
  | 'planning'
  | 'scripting'
  | 'rendering'
  | 'assembling'
  | 'complete'
  | 'fixture_complete'
  | 'unsupported'
  | 'error'

interface PipelineLogEntry {
  timestamp: string
  level: 'debug' | 'info' | 'warn' | 'error'
  message: string
  component: string
  metadata: Record<string, unknown>
}

interface PipelineArtifact {
  id: string
  type: 'video' | 'audio' | 'image' | 'data' | 'code'
  path: string
  size: number
  checksum: string
  metadata: Record<string, unknown>
  created_at: string
}

interface PipelineState {
  pipeline_id: string
  status: PipelineStatus
  current_step: number
  total_steps: number
  progress: number
  current_operation: string
  logs: PipelineLogEntry[]
  artifacts: PipelineArtifact[]
  created_at?: string
  updated_at?: string
}

interface PipelineMonitorProps {
  request?: PhysicsVideoRequest
  onComplete: (videoPath: string) => void
}

const API_BASE_URL =
  (import.meta.env.VITE_ORCHESTRATOR_URL as string | undefined)?.replace(/\/$/, '') ||
  'http://127.0.0.1:8000'

const EMPTY_STATE: PipelineState = {
  pipeline_id: '',
  status: 'idle',
  current_step: 0,
  total_steps: 1,
  progress: 0,
  current_operation: 'No pipeline job started',
  logs: [],
  artifacts: [],
}

const TERMINAL_STATES = new Set<PipelineStatus>([
  'complete',
  'fixture_complete',
  'unsupported',
  'error',
])

const mapLevel = (level: PhysicsVideoRequest['level']): 'beginner' | 'intermediate' | 'advanced' => {
  if (level === 'intro') return 'beginner'
  if (level === 'expert') return 'advanced'
  return 'intermediate'
}

const PipelineMonitor: React.FC<PipelineMonitorProps> = ({ request, onComplete }) => {
  const [state, setState] = useState<PipelineState>(EMPTY_STATE)
  const [isRunning, setIsRunning] = useState(false)
  const [mode, setMode] = useState<string>('unknown')
  const [transportError, setTransportError] = useState<string | null>(null)
  const pollGeneration = useRef(0)
  const logsEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    return () => {
      pollGeneration.current += 1
    }
  }, [])

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.logs])

  const pollPipeline = async (pipelineId: string, generation: number) => {
    while (pollGeneration.current === generation) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/pipeline/${pipelineId}/status`, {
          headers: { Accept: 'application/json' },
        })

        if (!response.ok) {
          throw new Error(`status request returned HTTP ${response.status}`)
        }

        const nextState = (await response.json()) as PipelineState
        setState(nextState)
        setTransportError(null)

        if (TERMINAL_STATES.has(nextState.status)) {
          setIsRunning(false)

          if (nextState.status === 'complete') {
            const video = nextState.artifacts.find((artifact) => artifact.type === 'video')
            if (video?.path) onComplete(video.path)
          }
          return
        }
      } catch (caught) {
        setTransportError(caught instanceof Error ? caught.message : 'pipeline status unavailable')
        setIsRunning(false)
        return
      }

      await new Promise((resolve) => window.setTimeout(resolve, 750))
    }
  }

  const handleStart = async () => {
    if (!request || isRunning) return

    const generation = pollGeneration.current + 1
    pollGeneration.current = generation
    setIsRunning(true)
    setTransportError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/pipeline/create`, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: request.topic,
          duration: request.duration,
          level: mapLevel(request.level),
          style: {
            color_theme: request.style?.colorTheme ?? 'scientific',
            font_stack: request.style?.fontStack ?? ['Inter', 'JetBrains Mono'],
            motion_vocabulary: request.style?.motionVocabulary ?? 'smooth',
          },
        }),
      })

      if (!response.ok) {
        const detail = await response.text()
        throw new Error(`pipeline creation returned HTTP ${response.status}: ${detail}`)
      }

      const created = (await response.json()) as {
        pipeline_id: string
        status: string
        mode: string
      }

      setMode(created.mode)
      setState({
        ...EMPTY_STATE,
        pipeline_id: created.pipeline_id,
        status: 'planning',
        current_operation: 'Pipeline accepted by orchestrator',
      })

      await pollPipeline(created.pipeline_id, generation)
    } catch (caught) {
      setTransportError(caught instanceof Error ? caught.message : 'pipeline creation failed')
      setIsRunning(false)
    }
  }

  const handleReset = () => {
    pollGeneration.current += 1
    setIsRunning(false)
    setMode('unknown')
    setTransportError(null)
    setState(EMPTY_STATE)
  }

  const getStatusIcon = (status: PipelineStatus) => {
    if (status === 'complete' || status === 'fixture_complete') {
      return <CheckCircle className="h-4 w-4" />
    }
    if (status === 'error' || status === 'unsupported') {
      return <AlertCircle className="h-4 w-4" />
    }
    if (status === 'idle') return <Clock className="h-4 w-4 text-muted-foreground" />
    return <Activity className="h-4 w-4 animate-pulse" />
  }

  const statusVariant = () => {
    if (state.status === 'error') return 'destructive' as const
    if (state.status === 'fixture_complete' || state.status === 'unsupported') return 'secondary' as const
    return 'default' as const
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Orchestrator Pipeline
              {getStatusIcon(state.status)}
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline">API: {API_BASE_URL}</Badge>
              <Badge variant={mode === 'fixture' ? 'secondary' : 'outline'}>mode: {mode}</Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={() => void handleStart()} disabled={isRunning || !request} className="gap-2">
              <Play className="h-4 w-4" />
              Start via API
            </Button>
            <Button onClick={handleReset} variant="outline" className="gap-2">
              <RotateCcw className="h-4 w-4" />
              Reset view
            </Button>
          </div>

          {!request ? (
            <p className="text-sm text-muted-foreground">
              Create a request before starting an orchestrator pipeline.
            </p>
          ) : null}

          {transportError ? (
            <div className="rounded-md border border-border bg-muted/50 p-3 text-sm">
              <div className="font-medium">Orchestrator request failed</div>
              <div className="mt-1 text-muted-foreground">{transportError}</div>
            </div>
          ) : null}

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Step {state.current_step} of {state.total_steps}</span>
              <span>{Math.round(state.progress)}%</span>
            </div>
            <Progress value={state.progress} className="h-2" />
            <p className="text-sm text-muted-foreground">{state.current_operation}</p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={statusVariant()}>{state.status}</Badge>
            {state.pipeline_id ? <Badge variant="outline">{state.pipeline_id}</Badge> : null}
          </div>

          {state.status === 'fixture_complete' ? (
            <p className="text-sm text-muted-foreground">
              Fixture completion verifies orchestration semantics only. It does not represent a rendered video and does not trigger the completion callback.
            </p>
          ) : null}

          {state.status === 'unsupported' ? (
            <p className="text-sm text-muted-foreground">
              The backend explicitly reports that a required real capability is not yet wired or available. No simulated success is substituted.
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Tabs defaultValue="logs" className="space-y-4">
        <TabsList>
          <TabsTrigger value="logs">Backend logs</TabsTrigger>
          <TabsTrigger value="artifacts">Backend artifacts</TabsTrigger>
          <TabsTrigger value="execution">Execution semantics</TabsTrigger>
        </TabsList>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>Pipeline logs</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64">
                <div className="space-y-1 font-mono text-sm">
                  {state.logs.map((log, index) => (
                    <div key={`${log.timestamp}-${index}`}>
                      <span className="text-muted-foreground">
                        [{new Date(log.timestamp).toLocaleTimeString()}] [{log.component}] [{log.level}]
                      </span>{' '}
                      {log.message}
                    </div>
                  ))}
                  {state.logs.length === 0 ? (
                    <p className="font-sans text-sm text-muted-foreground">No backend log entries yet.</p>
                  ) : null}
                  <div ref={logsEndRef} />
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="artifacts">
          <Card>
            <CardHeader>
              <CardTitle>Persisted artifacts ({state.artifacts.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {state.artifacts.map((artifact) => (
                  <div key={artifact.id} className="flex items-start gap-3 rounded border p-3">
                    <Video className="mt-0.5 h-4 w-4" />
                    <div className="min-w-0">
                      <div className="font-medium">{artifact.id}</div>
                      <div className="text-sm text-muted-foreground">
                        {artifact.type} · {artifact.size.toLocaleString()} bytes
                      </div>
                      <div className="break-all font-mono text-xs text-muted-foreground">{artifact.path}</div>
                      <div className="break-all font-mono text-[11px] text-muted-foreground">
                        sha/checksum: {artifact.checksum}
                      </div>
                    </div>
                  </div>
                ))}
                {state.artifacts.length === 0 ? (
                  <p className="py-4 text-center text-muted-foreground">No backend artifacts reported.</p>
                ) : null}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="execution">
          <Card>
            <CardHeader>
              <CardTitle>Execution semantics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p><code>complete</code> is reserved for a real completed backend capability.</p>
              <p><code>fixture_complete</code> means deterministic orchestration testing only.</p>
              <p><code>unsupported</code> means the backend refused to invent success for an unavailable path.</p>
              <p>This component does not generate CPU/GPU telemetry or client-side render progress.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default PipelineMonitor
