import {
  AnalysisIssue,
  FrameAnalysis,
  FrameComparisonResult,
  OverallQAMetrics,
  RenderSequence,
} from './qa-types'

/**
 * Deterministic QA demo data for interface development.
 *
 * Nothing in this module is measured renderer output. The deterministic values
 * exist only so the GUI can exercise tables, plots, issue states, and preview
 * interactions reproducibly while the real backend QA path is integrated.
 */

const DEMO_FRAME_COUNT = 720
const DEMO_FRAMERATE = 30

const unit = (seed: number): number => {
  const value = Math.sin(seed * 12.9898) * 43758.5453
  return value - Math.floor(value)
}

export const demoRenderSequence: RenderSequence = {
  id: 'demo-seq-001',
  name: 'DEMO · Quantum Harmonic Oscillator · Shot 03',
  frameCount: DEMO_FRAME_COUNT,
  framerate: DEMO_FRAMERATE,
  duration: DEMO_FRAME_COUNT / DEMO_FRAMERATE,
  resolution: { width: 1920, height: 1080 },
  frames: Array.from(
    { length: DEMO_FRAME_COUNT },
    (_, index) => `/demo-frames/frame_${String(index + 1).padStart(4, '0')}.png`,
  ),
  uploadedAt: new Date(0),
  status: 'complete',
}

export const demoQAMetrics: OverallQAMetrics = {
  averageSSIM: 0.924,
  motionStabilityScore: 0.887,
  textLegibilityScore: 0.854,
  overallQualityScore: 0.888,
  totalFramesAnalyzed: 156,
  issuesDetected: 23,
  criticalIssues: 2,
  lastAnalysisTime: new Date(0),
}

const frameAnalysisCache = new Map<number, FrameAnalysis>()

const getFrameType = (
  frameIndex: number,
): 'intro' | 'equation' | 'animation' | 'diagram' | 'transition' => {
  if (frameIndex < 60) return 'intro'
  if (frameIndex < 180) return 'equation'
  if (frameIndex < 420) return 'animation'
  if (frameIndex < 600) return 'diagram'
  return 'transition'
}

const generateDemoIssues = (frameIndex: number, frameType: string): AnalysisIssue[] => {
  const issues: AnalysisIssue[] = []

  if (frameType === 'equation' && unit(frameIndex + 11) > 0.7) {
    issues.push({
      type: 'text-legibility',
      severity: unit(frameIndex + 12) > 0.8 ? 'high' : 'medium',
      description: 'DEMO: equation legibility warning',
      suggestion: 'Demo suggestion: increase size or contrast',
      location: {
        x: 200 + Math.floor(unit(frameIndex + 13) * 400),
        y: 150 + Math.floor(unit(frameIndex + 14) * 300),
        width: 300 + Math.floor(unit(frameIndex + 15) * 200),
        height: 80 + Math.floor(unit(frameIndex + 16) * 40),
      },
    })
  }

  if (frameType === 'animation' && unit(frameIndex + 21) > 0.8) {
    issues.push({
      type: 'motion-artifact',
      severity: 'medium',
      description: 'DEMO: motion-artifact warning',
      suggestion: 'Demo suggestion: inspect animation timing',
    })
  }

  if (frameType === 'diagram' && unit(frameIndex + 31) > 0.85) {
    issues.push({
      type: 'composition',
      severity: 'low',
      description: 'DEMO: composition margin warning',
      suggestion: 'Demo suggestion: increase diagram margin',
      location: { x: 0, y: 0, width: 50, height: 1080 },
    })
  }

  if (frameIndex > 300 && frameIndex < 350 && unit(frameIndex + 41) > 0.6) {
    issues.push({
      type: 'color-issue',
      severity: 'medium',
      description: 'DEMO: color-transition warning',
      suggestion: 'Demo suggestion: inspect color grading',
    })
  }

  if (unit(frameIndex + 51) > 0.9) {
    issues.push({
      type: 'technical',
      severity: 'medium',
      description: 'DEMO: compression-artifact warning',
      suggestion: 'Demo suggestion: inspect codec/render settings',
    })
  }

  return issues
}

const buildDemoFrameAnalysis = (frameIndex: number): FrameAnalysis => {
  const normalizedIndex = Math.max(0, Math.min(DEMO_FRAME_COUNT - 1, frameIndex))
  const cached = frameAnalysisCache.get(normalizedIndex)
  if (cached) return cached

  const frameType = getFrameType(normalizedIndex)
  const issues = generateDemoIssues(normalizedIndex, frameType)

  let ssim = 0.92 + unit(normalizedIndex + 61) * 0.07
  let opticalFlowStability = 0.88 + unit(normalizedIndex + 62) * 0.1
  let textLegibility = 0.85 + unit(normalizedIndex + 63) * 0.12
  let colorAccuracy = 0.9 + unit(normalizedIndex + 64) * 0.08

  for (const issue of issues) {
    if (issue.type === 'text-legibility') textLegibility *= 0.7
    if (issue.type === 'technical') ssim *= 0.8
    if (issue.type === 'motion-artifact') opticalFlowStability *= 0.6
    if (issue.type === 'color-issue') colorAccuracy *= 0.75
  }

  const analysis: FrameAnalysis = {
    frameIndex: normalizedIndex,
    timestamp: normalizedIndex / DEMO_FRAMERATE,
    status: 'complete',
    metrics: {
      ssim,
      opticalFlowStability,
      textLegibility,
      colorAccuracy,
      timestamp: normalizedIndex / DEMO_FRAMERATE,
    },
    issues,
    thumbnailUrl: `/demo-frames/frame_${String(normalizedIndex + 1).padStart(4, '0')}.png`,
  }

  frameAnalysisCache.set(normalizedIndex, analysis)
  return analysis
}

export const generateDemoFrameAnalyses = (count: number): FrameAnalysis[] =>
  Array.from({ length: Math.max(0, count) }, (_, index) =>
    buildDemoFrameAnalysis((index * 37 + 17) % DEMO_FRAME_COUNT),
  )

export const demoAnalyzeFrame = async (frameIndex: number): Promise<FrameAnalysis> =>
  buildDemoFrameAnalysis(frameIndex)

export const demoUploadSequence = async (files: FileList): Promise<RenderSequence> => {
  const frameCount = files.length
  return {
    id: `demo-upload-${Date.now()}`,
    name: `DEMO local sequence · ${new Date().toLocaleDateString()}`,
    frameCount,
    framerate: DEMO_FRAMERATE,
    duration: frameCount / DEMO_FRAMERATE,
    resolution: { width: 1920, height: 1080 },
    frames: Array.from(files, (file) => URL.createObjectURL(file)),
    uploadedAt: new Date(),
    status: 'complete',
  }
}

export const demoCompareFrames = async (
  frameA: number,
  frameB: number,
): Promise<FrameComparisonResult> => {
  const timeDiff = Math.abs(frameA - frameB)
  const ssimScore = Math.max(0.5, 1 - timeDiff * 0.01)
  const differences: FrameComparisonResult['differences'] = []

  if (timeDiff > 30) {
    differences.push({
      type: 'changed',
      region: { x: 150, y: 200, width: 400, height: 150 },
      description: 'DEMO: main content area changed',
    })
  }
  if (timeDiff > 10) {
    differences.push({
      type: 'changed',
      region: { x: 50, y: 50, width: 200, height: 80 },
      description: 'DEMO: text overlay changed',
    })
  }
  if (timeDiff > 60) {
    differences.push({
      type: 'added',
      region: { x: 800, y: 300, width: 300, height: 200 },
      description: 'DEMO: visual element added',
    })
  }

  return { frameA, frameB, ssimScore, differences }
}
