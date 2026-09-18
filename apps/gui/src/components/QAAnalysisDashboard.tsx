import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Activity, AlertTriangle, BarChart, CheckCircle } from 'lucide-react'
import { FrameAnalysis, OverallQAMetrics } from '@/lib/qa-types'

interface QAAnalysisDashboardProps {
  metrics: OverallQAMetrics
  recentAnalyses: FrameAnalysis[]
}

export default function QAAnalysisDashboard({
  metrics,
  recentAnalyses,
}: QAAnalysisDashboardProps) {
  const qualityLabel = (score: number) => {
    if (score >= 0.9) return 'high'
    if (score >= 0.75) return 'moderate'
    return 'low'
  }

  const issueRows = recentAnalyses.flatMap((analysis) =>
    analysis.issues.map((issue) => ({
      frameIndex: analysis.frameIndex,
      ...issue,
    })),
  )

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity size={20} />
                Quality Analysis Demo
              </CardTitle>
              <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                Read-only deterministic fixture for exercising QA presentation. No analyzer,
                renderer, or remediation job is invoked by this dashboard.
              </p>
            </div>
            <Badge variant="outline">demo metrics</Badge>
          </div>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div className="rounded-md border p-4">
              <div className="text-2xl font-semibold">{metrics.totalFramesAnalyzed}</div>
              <div className="text-sm text-muted-foreground">fixture frames</div>
            </div>
            <div className="rounded-md border p-4">
              <div className="text-2xl font-semibold">{metrics.issuesDetected}</div>
              <div className="text-sm text-muted-foreground">fixture issues</div>
            </div>
            <div className="rounded-md border p-4">
              <div className="text-2xl font-semibold">{metrics.criticalIssues}</div>
              <div className="text-sm text-muted-foreground">fixture critical</div>
            </div>
            <div className="rounded-md border p-4">
              <div className="text-2xl font-semibold capitalize">
                {qualityLabel(metrics.overallQualityScore)}
              </div>
              <div className="text-sm text-muted-foreground">fixture quality band</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart size={20} />
            Deterministic metric fixture
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-5 md:grid-cols-2">
          {[
            ['SSIM', metrics.averageSSIM],
            ['Motion stability', metrics.motionStabilityScore],
            ['Text legibility', metrics.textLegibilityScore],
            ['Overall score', metrics.overallQualityScore],
          ].map(([label, rawScore]) => {
            const score = rawScore as number
            return (
              <div key={label as string} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>{label as string}</span>
                  <span className="font-mono">{score.toFixed(3)}</span>
                </div>
                <Progress value={score * 100} />
              </div>
            )
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Frame fixture</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Frame</TableHead>
                  <TableHead>SSIM</TableHead>
                  <TableHead>Motion</TableHead>
                  <TableHead>Text</TableHead>
                  <TableHead>Issues</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentAnalyses.slice(0, 12).map((analysis) => (
                  <TableRow key={analysis.frameIndex}>
                    <TableCell className="font-mono">{analysis.frameIndex + 1}</TableCell>
                    <TableCell className="font-mono">{analysis.metrics.ssim.toFixed(3)}</TableCell>
                    <TableCell className="font-mono">
                      {analysis.metrics.opticalFlowStability.toFixed(3)}
                    </TableCell>
                    <TableCell className="font-mono">
                      {analysis.metrics.textLegibility.toFixed(3)}
                    </TableCell>
                    <TableCell>
                      {analysis.issues.length === 0 ? (
                        <Badge variant="outline" className="gap-1">
                          <CheckCircle size={12} /> none
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="gap-1">
                          <AlertTriangle size={12} /> {analysis.issues.length}
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Fixture issues</CardTitle>
        </CardHeader>
        <CardContent>
          {issueRows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No issues in this deterministic fixture.</p>
          ) : (
            <div className="space-y-2">
              {issueRows.slice(0, 10).map((issue, index) => (
                <div
                  key={`${issue.frameIndex}-${issue.type}-${index}`}
                  className="rounded-md border p-3 text-sm"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">Frame {issue.frameIndex + 1}</span>
                    <Badge variant="outline">{issue.severity}</Badge>
                    <Badge variant="secondary">{issue.type}</Badge>
                  </div>
                  <p className="mt-2 text-muted-foreground">{issue.description}</p>
                  {issue.suggestion ? (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Fixture suggestion: {issue.suggestion}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
