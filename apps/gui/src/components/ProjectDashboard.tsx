import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { FileText, Plus } from 'lucide-react'
import { Project } from '@/lib/types'
import { ProjectDraft } from '@/components/ProjectCreation'

interface ProjectDashboardProps {
  projects: Project[]
  onCreateProject?: (project: ProjectDraft) => void
}

const statusLabel = (status: Project['status']) => status.replaceAll('-', ' ')

export default function ProjectDashboard({
  projects,
  onCreateProject,
}: ProjectDashboardProps) {
  const createDemoRequest = () => {
    onCreateProject?.({
      title: 'Simple Harmonic Motion',
      topic: 'Visualize x(t) = A cos(ωt + φ) and the relationship between displacement, velocity, acceleration, and restoring force.',
      duration: 45,
    })
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <CardTitle>Request Ledger</CardTitle>
              <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                These entries are local GUI request records. They are not renderer jobs and their local status metadata should not be read as backend execution evidence.
              </p>
            </div>
            <Badge variant="outline">{projects.length} local records</Badge>
          </div>
        </CardHeader>
      </Card>

      {projects.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
            <FileText size={32} className="text-muted-foreground" />
            <div>
              <div className="font-medium">No request records yet</div>
              <div className="mt-1 text-sm text-muted-foreground">
                Create a bounded request, then use the Pipeline panel to submit it to the actual orchestrator.
              </div>
            </div>
            {onCreateProject ? (
              <Button variant="outline" onClick={createDemoRequest} className="gap-2">
                <Plus size={14} /> Add deterministic example
              </Button>
            ) : null}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {projects.map((project) => (
            <Card key={project.id}>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="text-lg">{project.title}</CardTitle>
                    <p className="mt-2 line-clamp-3 text-sm text-muted-foreground">
                      {project.topic}
                    </p>
                  </div>
                  <Badge variant="secondary">{project.duration}s</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline">local status: {statusLabel(project.status)}</Badge>
                  <span>created {new Date(project.createdAt).toLocaleString()}</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Backend execution state is intentionally shown only in Pipeline/System surfaces.
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
