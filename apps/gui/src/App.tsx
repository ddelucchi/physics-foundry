import { useState } from 'react'
import { useKV } from '@github/spark/hooks'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import ProjectDashboard from '@/components/ProjectDashboard'
import ProjectCreation, { ProjectDraft } from '@/components/ProjectCreation'
import SystemMonitor from '@/components/SystemMonitor'
import RenderPreview from '@/components/RenderPreview'
import QAAnalysisDashboard from '@/components/QAAnalysisDashboard'
import PipelineMonitor from '@/components/PipelineMonitor'
import LiveCodeWorkspace from '@/components/LiveCodeWorkspace'
import AudioAlignmentWorkspace from '@/components/AudioAlignmentWorkspace'
import { Project } from '@/lib/types'
import { RenderSequence } from '@/lib/qa-types'
import { PhysicsVideoRequest } from '@/lib/pipeline-orchestrator'
import { DATA_PROVENANCE } from '@/lib/dataProvenance'
import {
  demoAnalyzeFrame,
  demoQAMetrics,
  demoRenderSequence,
  demoUploadSequence,
  generateDemoFrameAnalyses,
} from '@/lib/demoQAData'

function App() {
  const [projects, setProjects] = useKV<Project[]>('physics-video-projects', [])
  const [activeTab, setActiveTab] = useState('dashboard')
  const [showCreateProject, setShowCreateProject] = useState(false)
  const [currentSequence, setCurrentSequence] = useKV<RenderSequence | null>(
    'current-qa-sequence',
    demoRenderSequence,
  )
  const [currentRequest, setCurrentRequest] = useState<PhysicsVideoRequest | null>(null)

  const createProject = (projectData: ProjectDraft) => {
    const newProject: Project = {
      ...projectData,
      id: `project-${Date.now()}`,
      createdAt: new Date().toISOString(),
      status: 'initializing',
      progress: {
        outline: 0,
        script: 0,
        shots: 0,
        renders: 0,
        qa: 0,
        assembly: 0,
      },
    }

    setProjects((current) => [...current, newProject])
    setShowCreateProject(false)

    setCurrentRequest({
      topic: projectData.topic,
      duration: projectData.duration,
      level: 'intermediate',
      style: {
        colorTheme: 'scientific',
        fontStack: ['Inter', 'JetBrains Mono'],
        motionVocabulary: 'smooth',
      },
    })
    setActiveTab('pipeline')
  }

  const handleUploadSequence = async (files: FileList) => {
    try {
      const sequence = await demoUploadSequence(files)
      setCurrentSequence(sequence)
      setActiveTab('qa-preview')
    } catch (error) {
      console.error('Local sequence selection failed:', error)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between gap-6">
            <div>
              <h1 className="text-2xl font-bold font-sans tracking-tight text-card-foreground">
                Physics Foundry
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Evidence-aware scientific-media orchestration prototype
              </p>
            </div>

            <Button onClick={() => setShowCreateProject(true)} className="gap-2">
              <Plus size={16} />
              New Request
            </Button>
          </div>

          <div
            className="mt-4 rounded-md border border-border bg-muted/50 px-4 py-3 text-sm"
            role="status"
            aria-label="Data provenance notice"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded border border-border bg-background px-2 py-0.5 text-xs font-semibold uppercase tracking-wide">
                Mixed provenance prototype
              </span>
              <span className="text-muted-foreground">
                Pipeline and system panels read backend state. Code, QA, and alignment examples remain explicitly deterministic demos. {DATA_PROVENANCE.demo.description}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="dashboard">Requests</TabsTrigger>
            <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
            <TabsTrigger value="code">Code Review</TabsTrigger>
            <TabsTrigger value="audio">Audio Review</TabsTrigger>
            <TabsTrigger value="qa-analysis">QA Demo</TabsTrigger>
            <TabsTrigger value="qa-preview">Frame Review</TabsTrigger>
            <TabsTrigger value="system">System</TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            <ProjectDashboard projects={projects} onCreateProject={createProject} />
          </TabsContent>

          <TabsContent value="pipeline" className="space-y-6">
            <PipelineMonitor
              request={currentRequest || undefined}
              onComplete={(videoPath) => {
                console.log('Real pipeline completion callback:', videoPath)
                setActiveTab('qa-preview')
              }}
            />
          </TabsContent>

          <TabsContent value="code" className="space-y-6">
            <LiveCodeWorkspace
              onCodeUpdate={(sceneId) => {
                console.log('Local demo review state updated for scene:', sceneId)
              }}
            />
          </TabsContent>

          <TabsContent value="audio" className="space-y-6">
            <AudioAlignmentWorkspace />
          </TabsContent>

          <TabsContent value="qa-analysis" className="space-y-6">
            <QAAnalysisDashboard
              metrics={demoQAMetrics}
              recentAnalyses={generateDemoFrameAnalyses(20)}
            />
          </TabsContent>

          <TabsContent value="qa-preview" className="space-y-6">
            <RenderPreview
              sequence={currentSequence || undefined}
              onUploadSequence={handleUploadSequence}
              onAnalyzeFrame={demoAnalyzeFrame}
            />
          </TabsContent>

          <TabsContent value="system" className="space-y-6">
            <SystemMonitor />
          </TabsContent>
        </Tabs>
      </main>

      <ProjectCreation
        open={showCreateProject}
        onOpenChange={setShowCreateProject}
        onCreateProject={createProject}
      />
    </div>
  )
}

export default App
