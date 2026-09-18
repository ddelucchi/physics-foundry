import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Clock, Pause, Play, Upload, Volume2, Waveform } from 'lucide-react'

interface DemoWordAlignment {
  word: string
  startTime: number
  endTime: number
  confidence: number
}

const demoAlignment: DemoWordAlignment[] = [
  { word: 'quantum', startTime: 0.0, endTime: 0.52, confidence: 0.94 },
  { word: 'harmonic', startTime: 0.52, endTime: 1.08, confidence: 0.91 },
  { word: 'oscillator', startTime: 1.08, endTime: 1.74, confidence: 0.89 },
  { word: 'energy', startTime: 1.74, endTime: 2.18, confidence: 0.93 },
  { word: 'levels', startTime: 2.18, endTime: 2.72, confidence: 0.92 },
]

const AudioAlignmentWorkspace: React.FC = () => {
  const audioRef = useRef<HTMLAudioElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [duration, setDuration] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl)
    }
  }, [audioUrl])

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  const demoDuration = useMemo(
    () => Math.max(...demoAlignment.map((word) => word.endTime)),
    [],
  )

  const formatTime = (seconds: number) => {
    if (!Number.isFinite(seconds)) return '0:00.00'
    const minutes = Math.floor(seconds / 60)
    const remainder = seconds - minutes * 60
    return `${minutes}:${remainder.toFixed(2).padStart(5, '0')}`
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (audioUrl) URL.revokeObjectURL(audioUrl)

    const nextUrl = URL.createObjectURL(file)
    setAudioUrl(nextUrl)
    setFileName(file.name)
    setCurrentTime(0)
    setDuration(0)
    setIsPlaying(false)
  }

  const togglePlayback = async () => {
    const audio = audioRef.current
    if (!audio || !audioUrl) return

    if (audio.paused) {
      await audio.play()
      setIsPlaying(true)
    } else {
      audio.pause()
      setIsPlaying(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Waveform size={20} />
                Audio Review Demo
              </CardTitle>
              <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                Audio upload and browser playback are real. Word timing below is a deterministic
                presentation fixture. No forced-alignment engine is currently invoked by this panel.
              </p>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline">live local playback</Badge>
              <Badge variant="secondary">demo alignment</Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            className="hidden"
            onChange={handleFileUpload}
          />

          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              className="gap-2"
            >
              <Upload size={16} />
              Select local audio
            </Button>

            <Button
              onClick={togglePlayback}
              disabled={!audioUrl}
              className="gap-2"
            >
              {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              {isPlaying ? 'Pause' : 'Play'}
            </Button>

            <span className="text-sm text-muted-foreground">
              {fileName ?? 'No local audio selected'}
            </span>
          </div>

          <audio
            ref={audioRef}
            src={audioUrl ?? undefined}
            onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)}
            onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
            onPause={() => setIsPlaying(false)}
            onPlay={() => setIsPlaying(true)}
            onEnded={() => setIsPlaying(false)}
          />

          <div className="space-y-2 rounded-md border p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <Volume2 size={14} />
                Browser playback position
              </span>
              <span className="font-mono">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            Alignment execution is intentionally disabled until a real backend transcription /
            forced-alignment path is wired and its output can be distinguished from demo fixtures.
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <CardTitle>Deterministic alignment fixture</CardTitle>
            <Badge variant="outline">not measured from uploaded audio</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative h-14 overflow-hidden rounded-md border bg-muted/30">
            {demoAlignment.map((word) => {
              const left = (word.startTime / demoDuration) * 100
              const width = ((word.endTime - word.startTime) / demoDuration) * 100
              return (
                <div
                  key={`${word.word}-${word.startTime}`}
                  className="absolute top-0 flex h-full items-center justify-center border-r px-1 text-xs"
                  style={{ left: `${left}%`, width: `${width}%` }}
                >
                  {word.word}
                </div>
              )
            })}
          </div>

          <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
            {demoAlignment.map((word) => (
              <div key={`${word.word}-details`} className="rounded-md border p-3 text-sm">
                <div className="font-medium">{word.word}</div>
                <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock size={12} />
                  {word.startTime.toFixed(2)}s → {word.endTime.toFixed(2)}s
                </div>
                <div className="mt-1 text-xs text-muted-foreground">
                  fixture confidence: {(word.confidence * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default AudioAlignmentWorkspace
