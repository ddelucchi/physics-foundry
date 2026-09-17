import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Cpu, HardDrive, Monitor } from 'lucide-react'

interface ProjectCreationProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreateProject: (project: {
    title: string
    topic: string
    duration: number
    settings: {
      quality: 'draft' | 'standard' | 'high'
      renderer: 'auto' | 'manim' | 'blender' | 'taichi'
      resolution: '720p' | '1080p' | '4k'
    }
  }) => void
}

export default function ProjectCreation({ open, onOpenChange, onCreateProject }: ProjectCreationProps) {
  const [title, setTitle] = useState('')
  const [topic, setTopic] = useState('')
  const [duration, setDuration] = useState('')
  const [quality, setQuality] = useState<'draft' | 'standard' | 'high'>('standard')
  const [renderer, setRenderer] = useState<'auto' | 'manim' | 'blender' | 'taichi'>('auto')
  const [resolution, setResolution] = useState<'720p' | '1080p' | '4k'>('1080p')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!title.trim() || !topic.trim() || !duration) {
      return
    }

    onCreateProject({
      title: title.trim(),
      topic: topic.trim(),
      duration: parseFloat(duration),
      settings: {
        quality,
        renderer,
        resolution
      }
    })

    // Reset form
    setTitle('')
    setTopic('')
    setDuration('')
    setQuality('standard')
    setRenderer('auto')
    setResolution('1080p')
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="font-sans">Create Physics Video Project</DialogTitle>
          <DialogDescription>
            Generate a complete physics video with AI-driven script, multi-engine rendering, and automated QA
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="project-title">Project Title</Label>
              <Input
                id="project-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Maxwell's Equations Explained"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="project-topic">Physics Topic</Label>
              <Textarea
                id="project-topic"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Describe the physics concept you want to explain in detail..."
                className="min-h-24"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="project-duration">Target Duration (minutes)</Label>
              <Input
                id="project-duration"
                type="number"
                step="0.5"
                min="1"
                max="60"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                placeholder="10"
                required
              />
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold font-sans">Pipeline Settings</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Monitor size={16} />
                    Quality
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Select value={quality} onValueChange={(value: any) => setQuality(value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="draft">
                        <div className="space-y-1">
                          <div>Draft</div>
                          <div className="text-xs text-muted-foreground">Fast iteration</div>
                        </div>
                      </SelectItem>
                      <SelectItem value="standard">
                        <div className="space-y-1">
                          <div>Standard</div>
                          <div className="text-xs text-muted-foreground">Balanced quality</div>
                        </div>
                      </SelectItem>
                      <SelectItem value="high">
                        <div className="space-y-1">
                          <div>High</div>
                          <div className="text-xs text-muted-foreground">High fidelity</div>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Cpu size={16} />
                    Renderer
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Select value={renderer} onValueChange={(value: any) => setRenderer(value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">Auto Select</SelectItem>
                      <SelectItem value="manim">Manim (Math)</SelectItem>
                      <SelectItem value="blender">Blender (3D)</SelectItem>
                      <SelectItem value="taichi">Taichi (Physics)</SelectItem>
                    </SelectContent>
                  </Select>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <HardDrive size={16} />
                    Resolution
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Select value={resolution} onValueChange={(value: any) => setResolution(value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="720p">720p</SelectItem>
                      <SelectItem value="1080p">1080p</SelectItem>
                      <SelectItem value="4k">4K</SelectItem>
                    </SelectContent>
                  </Select>
                </CardContent>
              </Card>
            </div>

            <Card className="border-accent/20 bg-accent/5">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-accent-foreground">Pipeline Overview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                  <Badge variant="outline">NeoX-20B Local LLM</Badge>
                  <Badge variant="outline">LLaVA Vision QA</Badge>
                  <Badge variant="outline">Multi-Engine Rendering</Badge>
                  <Badge variant="outline">Force-Aligned VO</Badge>
                  <Badge variant="outline">OTIO Timeline</Badge>
                  <Badge variant="outline">NVENC Encoding</Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Fully local pipeline optimized for i9-9900KS + RTX 2080 Ti
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!title.trim() || !topic.trim() || !duration}>
              Create Project
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}