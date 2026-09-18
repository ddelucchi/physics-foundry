import { useEffect, useState } from 'react'
import { AlertTriangle, ChevronLeft, ChevronRight, Upload } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { FrameAnalysis, RenderSequence } from '@/lib/qa-types'

interface RenderPreviewProps {
  sequence?: RenderSequence
  onUploadSequence: (files: FileList) => void
  onAnalyzeFrame: (frameIndex: number) => Promise<FrameAnalysis>
}

const scoreFromAnalysis = (analysis: FrameAnalysis) => {
  const values = [
    analysis.metrics.ssim,
    analysis.metrics.opticalFlowStability,
    analysis.metrics.textLegibility,
    analysis.metrics.colorAccuracy,
  ]
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

export default function RenderPreview({
  sequence,
  onUploadSequence,
  onAnalyzeFrame,
}: RenderPreviewProps) {
  const [currentFrame, setCurrentFrame] = useState(0)
  const [analysis, setAnalysis] = useState<FrameAnalysis | null>(null)
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    setCurrentFrame(0)
    setAnalysis(null)
  }, [sequence?.id])

  if (!sequence) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Frame Review</CardTitle>
        </CardHeader>
        <CardContent>
          <label className="flex cursor-pointer flex-col items-center gap-3 rounded-lg border border-dashed p-10 text-center">
            <Upload size={28} />
            <span className="font-medium">Select local frame images</span>
            <span className="text-sm text-muted-foreground">
              Local files are previewed in the browser. QA remains demo-only until a measured backend path is connected.
            </span>
            <input
              className="hidden"
              type="file"
              accept="image/*"
              multiple
              onChange={(event) => {
                if (event.target.files?.length) onUploadSequence(event.target.files)
              }}
            />
          </label>
        </CardContent>
      </Card>
    )
  }

  const maxFrame = Math.max(0, sequence.frames.length - 1)
  const clampedFrame = Math.min(currentFrame, maxFrame)
  const frameUrl = sequence.frames[clampedFrame]
  const isDemoPlaceholder = frameUrl?.startsWith('/demo-frames/') ?? false
  const progress = maxFrame > 0 ? (clampedFrame / maxFrame) * 100 : 0
  const aggregateScore = analysis ? scoreFromAnalysis(analysis) : null

  const selectFrame = (nextFrame: number) => {
    setCurrentFrame(Math.max(0, Math.min(maxFrame, nextFrame)))
    setAnalysis(null)
  }

  const analyzeCurrentFrame = async () => {
    setAnalyzing(true)
    try {
      setAnalysis(await onAnalyzeFrame(clampedFrame))
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <CardTitle>Frame Review</CardTitle>
              <p className="mt-2 text-sm text-muted-foreground">
                {sequence.name}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">
                {sequence.frames.length} frames · {sequence.framerate} fps
              </Badge>
              <Badge variant={isDemoPlaceholder ? 'secondary' : 'outline'}>
                {isDemoPlaceholder ? 'demo sequence' : 'local browser preview'}
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          <div className="flex min-h-[320px] items-center justify-center overflow-hidden rounded-lg border bg-muted/20">
            {isDemoPlaceholder ? (
              <div className="max-w-lg p-8 text-center">
                <div className="text-lg font-medium">Deterministic demo frame {clampedFrame + 1}</div>
                <p className="mt-2 text-sm text-muted-foreground">
                  The repository does not ship synthetic rendered frame images for this fixture. Upload local images to exercise actual browser preview.
                </p>
              </div>
            ) : frameUrl ? (
              <img
                src={frameUrl}
                alt={`Frame ${clampedFrame + 1} of ${sequence.frames.length}`}
                className="max-h-[560px] max-w-full object-contain"
              />
            ) : (
              <div className="text-sm text-muted-foreground">No frame available.</div>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Frame {clampedFrame + 1} / {Math.max(1, sequence.frames.length)}</span>
              <span className="font-mono">
                {(clampedFrame / Math.max(1, sequence.framerate)).toFixed(2)} s
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={clampedFrame === 0}
                onClick={() => selectFrame(clampedFrame - 1)}
                className="gap-2"
              >
                <ChevronLeft size={14} /> Previous
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={clampedFrame >= maxFrame}
                onClick={() => selectFrame(clampedFrame + 1)}
                className="gap-2"
              >
                Next <ChevronRight size={14} />
              </Button>
            </div>

            <div className="flex gap-2">
              <label>
                <span className="sr-only">Replace frame sequence</span>
                <input
                  className="hidden"
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(event) => {
                    if (event.target.files?.length) onUploadSequence(event.target.files)
                  }}
                />
                <span className="inline-flex h-9 cursor-pointer items-center rounded-md border px-3 text-sm">
                  Replace sequence
                </span>
              </label>
              <Button size="sm" onClick={analyzeCurrentFrame} disabled={analyzing}>
                {analyzing ? 'Loading demo metrics…' : 'Show demo QA'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {analysis ? (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CardTitle>Deterministic QA fixture</CardTitle>
              <Badge variant="outline">not measured from this displayed image</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-4">
              {[
                ['SSIM', analysis.metrics.ssim],
                ['Motion', analysis.metrics.opticalFlowStability],
                ['Text', analysis.metrics.textLegibility],
                ['Color', analysis.metrics.colorAccuracy],
              ].map(([label, value]) => (
                <div key={label as string} className="rounded-md border p-3">
                  <div className="text-xs text-muted-foreground">{label as string}</div>
                  <div className="mt-1 font-mono text-lg">{(value as number).toFixed(3)}</div>
                </div>
              ))}
            </div>

            <div className="text-sm text-muted-foreground">
              Fixture aggregate: {aggregateScore?.toFixed(3)}. This is presentation data from `demoQAData.ts`, not a measurement of the selected frame.
            </div>

            {analysis.issues.length ? (
              <div className="space-y-2">
                {analysis.issues.map((issue, index) => (
                  <div key={`${issue.type}-${index}`} className="flex gap-3 rounded-md border p-3 text-sm">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                    <div>
                      <div className="font-medium">{issue.type} · {issue.severity}</div>
                      <div className="text-muted-foreground">{issue.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No issues in this deterministic fixture.</div>
            )}
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
