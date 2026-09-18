import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'

export interface ProjectDraft {
  title: string
  topic: string
  duration: number
}

interface ProjectCreationProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreateProject: (project: ProjectDraft) => void
}

const MIN_DURATION_SECONDS = 10
const MAX_DURATION_SECONDS = 600

export default function ProjectCreation({
  open,
  onOpenChange,
  onCreateProject,
}: ProjectCreationProps) {
  const [title, setTitle] = useState('')
  const [topic, setTopic] = useState('')
  const [duration, setDuration] = useState('')

  const reset = () => {
    setTitle('')
    setTopic('')
    setDuration('')
  }

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    const parsedDuration = Number(duration)

    if (
      !title.trim() ||
      !topic.trim() ||
      !Number.isInteger(parsedDuration) ||
      parsedDuration < MIN_DURATION_SECONDS ||
      parsedDuration > MAX_DURATION_SECONDS
    ) {
      return
    }

    onCreateProject({
      title: title.trim(),
      topic: topic.trim(),
      duration: parsedDuration,
    })
    reset()
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <div className="flex flex-wrap items-center gap-2">
            <DialogTitle>Create Physics Request</DialogTitle>
            <Badge variant="outline">local request record</Badge>
          </div>
          <DialogDescription>
            Capture the bounded request accepted by the orchestrator. Renderer/model availability is reported separately by the backend and is not implied by this form.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="project-title">Title</Label>
            <Input
              id="project-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Simple harmonic motion"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-topic">Physics request</Label>
            <Textarea
              id="project-topic"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Describe the bounded concept, derivation, or visualization to plan."
              className="min-h-28"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-duration">Target duration (seconds)</Label>
            <Input
              id="project-duration"
              type="number"
              min={MIN_DURATION_SECONDS}
              max={MAX_DURATION_SECONDS}
              step="1"
              value={duration}
              onChange={(event) => setDuration(event.target.value)}
              placeholder="60"
              required
            />
            <p className="text-xs text-muted-foreground">
              Backend contract: integer duration from {MIN_DURATION_SECONDS} to {MAX_DURATION_SECONDS} seconds.
            </p>
          </div>

          <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            Creating this record does not claim that an LLM, Manim, Blender, Taichi, GPU encoder, or audio aligner is available. Use Pipeline and System to inspect real backend state.
          </div>

          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                reset()
                onOpenChange(false)
              }}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!title.trim() || !topic.trim() || !duration}>
              Create Request
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
