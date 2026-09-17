import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { useKV } from '@github/spark/hooks'
import { Cpu, HardDrive, Activity, Eye, Monitor, Download, CheckCircle, AlertTriangle } from 'lucide-react'

interface PipelineSettings {
  llmModel: string
  visionModel: string
  renderQuality: 'draft' | 'standard' | 'high'
  enableAutoFix: boolean
  maxRetries: number
  targetFramerate: number
  cudaEnabled: boolean
  optiXEnabled: boolean
  audioNormalization: boolean
}

export default function PipelineSettings() {
  const [settings, setSettings] = useKV<PipelineSettings>('pipeline-settings', {
    llmModel: 'neox-20b-q4-k-m',
    visionModel: 'llava-1.5-13b',
    renderQuality: 'standard',
    enableAutoFix: true,
    maxRetries: 3,
    targetFramerate: 30,
    cudaEnabled: true,
    optiXEnabled: true,
    audioNormalization: true
  })

  const [modelStatus, setModelStatus] = useState({
    neox: { status: 'not-downloaded', size: '12.8GB' },
    llava: { status: 'not-downloaded', size: '7.2GB' },
    whisper: { status: 'downloaded', size: '244MB' }
  })

  const updateSettings = <K extends keyof PipelineSettings>(key: K, value: PipelineSettings[K]) => {
    setSettings(current => ({
      ...current,
      [key]: value
    }))
  }

  const downloadModel = async (model: string) => {
    // Mock download process
    setModelStatus(current => ({
      ...current,
      [model]: { ...current[model], status: 'downloading' }
    }))
    
    // Simulate download progress
    setTimeout(() => {
      setModelStatus(current => ({
        ...current,
        [model]: { ...current[model], status: 'downloaded' }
      }))
    }, 3000)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'downloaded': return <CheckCircle size={16} className="text-green-600" />
      case 'downloading': return <Activity size={16} className="text-blue-600 animate-spin" />
      case 'not-downloaded': return <Download size={16} className="text-muted-foreground" />
      default: return <AlertTriangle size={16} className="text-yellow-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'downloaded': return 'text-green-600'
      case 'downloading': return 'text-blue-600'
      case 'not-downloaded': return 'text-muted-foreground'
      default: return 'text-yellow-600'
    }
  }

  return (
    <div className="space-y-6">
      <Alert>
        <Cpu className="h-4 w-4" />
        <AlertDescription>
          Configure the local AI pipeline optimized for i9-9900KS + 32GB RAM + RTX 2080 Ti. 
          All models run locally via llama.cpp with CUDA acceleration.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye size={20} />
              AI Models
            </CardTitle>
            <CardDescription>
              Local language and vision models for script generation and QA analysis
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(modelStatus.neox.status)}
                  <div>
                    <div className="font-medium text-sm">GPT-NeoX-20B (Q4_K_M)</div>
                    <div className="text-xs text-muted-foreground">
                      Script generation • {modelStatus.neox.size}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant={modelStatus.neox.status === 'downloaded' ? 'default' : 'outline'}
                    className={getStatusColor(modelStatus.neox.status)}
                  >
                    {modelStatus.neox.status.replace('-', ' ')}
                  </Badge>
                  {modelStatus.neox.status === 'not-downloaded' && (
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => downloadModel('neox')}
                    >
                      <Download size={14} />
                    </Button>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(modelStatus.llava.status)}
                  <div>
                    <div className="font-medium text-sm">LLaVA-1.5-13B</div>
                    <div className="text-xs text-muted-foreground">
                      Frame QA analysis • {modelStatus.llava.size}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant={modelStatus.llava.status === 'downloaded' ? 'default' : 'outline'}
                    className={getStatusColor(modelStatus.llava.status)}
                  >
                    {modelStatus.llava.status.replace('-', ' ')}
                  </Badge>
                  {modelStatus.llava.status === 'not-downloaded' && (
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => downloadModel('llava')}
                    >
                      <Download size={14} />
                    </Button>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(modelStatus.whisper.status)}
                  <div>
                    <div className="font-medium text-sm">Whisper Base.en</div>
                    <div className="text-xs text-muted-foreground">
                      Voice transcription • {modelStatus.whisper.size}
                    </div>
                  </div>
                </div>
                <Badge variant="default" className="text-green-600">
                  downloaded
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Render Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <VideoCamera size={20} />
              Render Pipeline
            </CardTitle>
            <CardDescription>
              Multi-engine rendering with Manim, Blender, and Taichi
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor="render-quality">Default Quality</Label>
                <Select 
                  value={settings.renderQuality} 
                  onValueChange={(value: any) => updateSettings('renderQuality', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="draft">Draft (Fast iteration)</SelectItem>
                    <SelectItem value="standard">Standard (Balanced)</SelectItem>
                    <SelectItem value="high">High (High fidelity)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="framerate">Target Framerate</Label>
                <Select 
                  value={settings.targetFramerate.toString()} 
                  onValueChange={(value) => updateSettings('targetFramerate', parseInt(value))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="24">24 FPS (Cinema)</SelectItem>
                    <SelectItem value="30">30 FPS (Standard)</SelectItem>
                    <SelectItem value="60">60 FPS (Smooth)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="cuda-enabled">CUDA Acceleration</Label>
                    <p className="text-xs text-muted-foreground">Enable GPU acceleration for rendering</p>
                  </div>
                  <Switch
                    id="cuda-enabled"
                    checked={settings.cudaEnabled}
                    onCheckedChange={(checked) => updateSettings('cudaEnabled', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="optix-enabled">OptiX Denoising</Label>
                    <p className="text-xs text-muted-foreground">RTX ray tracing acceleration</p>
                  </div>
                  <Switch
                    id="optix-enabled"
                    checked={settings.optiXEnabled}
                    onCheckedChange={(checked) => updateSettings('optiXEnabled', checked)}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* QA Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Monitor size={20} />
              Quality Analysis
            </CardTitle>
            <CardDescription>
              Automated QA and self-improvement settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="auto-fix">Auto-Fix Enabled</Label>
                  <p className="text-xs text-muted-foreground">Automatically retry failed renders</p>
                </div>
                <Switch
                  id="auto-fix"
                  checked={settings.enableAutoFix}
                  onCheckedChange={(checked) => updateSettings('enableAutoFix', checked)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="max-retries">Max Retry Attempts</Label>
                <Input
                  id="max-retries"
                  type="number"
                  min="1"
                  max="10"
                  value={settings.maxRetries}
                  onChange={(e) => updateSettings('maxRetries', parseInt(e.target.value) || 3)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Audio Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Microphone size={20} />
              Audio Pipeline
            </CardTitle>
            <CardDescription>
              Voice alignment and audio processing
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="audio-norm">EBU R128 Normalization</Label>
                  <p className="text-xs text-muted-foreground">Broadcast-standard loudness</p>
                </div>
                <Switch
                  id="audio-norm"
                  checked={settings.audioNormalization}
                  onCheckedChange={(checked) => updateSettings('audioNormalization', checked)}
                />
              </div>

              <Alert>
                <Microphone className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  Force-alignment will retime animations to match your voice recording using 
                  whisper.cpp with word-level timestamps.
                </AlertDescription>
              </Alert>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity size={20} />
            System Requirements
          </CardTitle>
          <CardDescription>
            Hardware compatibility for the physics video pipeline
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Cpu size={16} />
                <span className="text-sm font-medium">CPU</span>
              </div>
              <div className="text-xs text-muted-foreground">i9-9900KS recommended</div>
              <div className="text-xs text-green-600">✓ 32GB RAM available</div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <VideoCamera size={16} />
                <span className="text-sm font-medium">GPU</span>
              </div>
              <div className="text-xs text-muted-foreground">RTX 2080 Ti optimal</div>
              <div className="text-xs text-green-600">✓ CUDA 11.8 compatible</div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <HardDrive size={16} />
                <span className="text-sm font-medium">Storage</span>
              </div>
              <div className="text-xs text-muted-foreground">~25GB for models</div>
              <div className="text-xs text-green-600">✓ SSD storage available</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}