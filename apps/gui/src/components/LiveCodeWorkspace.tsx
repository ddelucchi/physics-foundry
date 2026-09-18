import React, { useMemo, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Code, GitBranch, Lock, Unlock } from 'lucide-react'

interface CodeRevision {
  id: string
  engine: 'manim' | 'taichi' | 'blender'
  sceneId: string
  code: string
  changes: string[]
  status: 'draft' | 'approved' | 'rejected'
}

interface LiveCodeWorkspaceProps {
  sceneId?: string
  onCodeUpdate?: (sceneId: string, code: string) => void
}

const demoRevisions: CodeRevision[] = [
  {
    id: 'demo_rev_001',
    engine: 'manim',
    sceneId: 'intro_scene',
    code: `from manim import *

class IntroScene(Scene):
    def construct(self):
        title = Text("Quantum Harmonic Oscillator", font_size=48)
        equation = MathTex(
            r"H = \\frac{p^2}{2m} + \\frac{1}{2}m\\omega^2x^2"
        )

        self.play(Write(title))
        self.wait(1)
        self.play(Transform(title, equation))
        self.wait(2)`,
    changes: ['Initial deterministic review fixture'],
    status: 'approved',
  },
  {
    id: 'demo_rev_002',
    engine: 'manim',
    sceneId: 'intro_scene',
    code: `from manim import *

class IntroScene(Scene):
    def construct(self):
        title = Text("Quantum Harmonic Oscillator", font_size=48)
        equation = MathTex(
            r"H = \\frac{p^2}{2m} + \\frac{1}{2}m\\omega^2x^2"
        )
        levels = VGroup(*[
            Line(LEFT * 2, RIGHT * 2).shift(UP * (n + 0.5))
            for n in range(5)
        ])

        self.play(Write(title))
        self.wait(1)
        self.play(Transform(title, equation))
        self.play(FadeIn(levels, lag_ratio=0.2))
        self.wait(2)`,
    changes: ['Added deterministic energy-level geometry'],
    status: 'draft',
  },
]

const LiveCodeWorkspace: React.FC<LiveCodeWorkspaceProps> = ({
  sceneId = 'intro_scene',
  onCodeUpdate,
}) => {
  const initialIndex = demoRevisions.findIndex((revision) => revision.sceneId === sceneId)
  const [selectedIndex, setSelectedIndex] = useState(initialIndex >= 0 ? initialIndex : 0)
  const [isLocked, setIsLocked] = useState(true)
  const [showDiff, setShowDiff] = useState(false)
  const [statusOverrides, setStatusOverrides] = useState<Record<string, CodeRevision['status']>>({})

  const currentRevision = demoRevisions[selectedIndex]
  const previousRevision = demoRevisions[Math.max(0, selectedIndex - 1)]
  const currentStatus = statusOverrides[currentRevision.id] ?? currentRevision.status

  const changedLines = useMemo(() => {
    const previous = previousRevision.code.split('\n')
    return new Set(
      currentRevision.code
        .split('\n')
        .map((line, index) => (line !== previous[index] ? index : -1))
        .filter((index) => index >= 0),
    )
  }, [currentRevision, previousRevision])

  const setStatus = (status: CodeRevision['status']) => {
    setStatusOverrides((current) => ({ ...current, [currentRevision.id]: status }))
    if (status === 'approved') {
      onCodeUpdate?.(currentRevision.sceneId, currentRevision.code)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Code size={20} />
                Code Review Demo
              </CardTitle>
              <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                Deterministic Manim source used to exercise revision, diff, and approval UI.
                This panel is not receiving live LLM output and does not claim that approving
                a revision renders media.
              </p>
            </div>

            <Badge variant="outline">demo data</Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            {demoRevisions.map((revision, index) => (
              <Button
                key={revision.id}
                size="sm"
                variant={selectedIndex === index ? 'default' : 'outline'}
                onClick={() => setSelectedIndex(index)}
              >
                {revision.id}
              </Button>
            ))}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-3">
            <div className="space-y-1">
              <div className="text-sm font-medium">
                {currentRevision.engine} / {currentRevision.sceneId}
              </div>
              <div className="text-xs text-muted-foreground">
                Status is local review state only: <strong>{currentStatus}</strong>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowDiff((current) => !current)}
                className="gap-2"
              >
                <GitBranch size={14} />
                {showDiff ? 'Code' : 'Diff'}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setIsLocked((current) => !current)}
                className="gap-2"
              >
                {isLocked ? <Lock size={14} /> : <Unlock size={14} />}
                {isLocked ? 'Review locked' : 'Review unlocked'}
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={isLocked}
                onClick={() => setStatus('rejected')}
              >
                Reject
              </Button>
              <Button
                size="sm"
                disabled={isLocked}
                onClick={() => setStatus('approved')}
              >
                Approve
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {currentRevision.changes.map((change) => (
              <Badge key={change} variant="secondary">
                {change}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{showDiff ? 'Deterministic diff view' : 'Source fixture'}</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[480px] rounded-md border bg-muted/20 p-4">
            <pre className="text-sm leading-6">
              {currentRevision.code.split('\n').map((line, index) => (
                <div
                  key={`${index}-${line}`}
                  className={
                    showDiff && changedLines.has(index)
                      ? 'border-l-2 border-foreground/40 bg-muted px-2'
                      : 'px-2'
                  }
                >
                  <span className="mr-4 inline-block w-8 select-none text-right text-muted-foreground">
                    {index + 1}
                  </span>
                  <code>{line || ' '}</code>
                </div>
              ))}
            </pre>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

export default LiveCodeWorkspace
