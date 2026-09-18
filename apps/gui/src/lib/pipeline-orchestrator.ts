/**
 * Shared request types for the Physics Foundry orchestrator UI.
 *
 * Pipeline execution belongs to the FastAPI service. The frontend deliberately
 * does not maintain a second client-side implementation that simulates LLM,
 * render, QA, or assembly success.
 */

export interface PhysicsVideoRequest {
  topic: string
  duration: number
  level: 'intro' | 'intermediate' | 'expert'
  style?: {
    colorTheme?: string
    fontStack?: string[]
    motionVocabulary?: string
  }
}
