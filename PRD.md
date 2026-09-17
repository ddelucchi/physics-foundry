# Physics Video Pipeline Control Center

> **Document status:** target-state product/design document. The repository [README](README.md) is authoritative for what is implemented today. Features described below may be planned, partial, mocked, or experimental and must not be read as current production capabilities.

A comprehensive control interface for managing a fully local, AI-driven physics video production pipeline that transforms topics into publishable content through automated script generation, multi-engine rendering, and self-review loops.

**Experience Qualities**:
1. **Technical Precision** - Interface reflects the sophisticated nature of the underlying pipeline with detailed metrics and granular control
2. **High-Fidelity Design** - Clean, professional aesthetic oriented toward detailed technical review  
3. **Workflow Focused** - Streamlined navigation through complex multi-stage processes with clear progress indicators

**Complexity Level**: Complex Application (advanced functionality, accounts)
The system manages intricate workflows spanning AI model orchestration, multi-engine rendering pipelines, quality assurance loops, and audio synchronization - requiring sophisticated state management and real-time monitoring capabilities.

## Essential Features

### Project Creation & Management
- **Functionality**: Create new physics video projects with topic and duration inputs
- **Purpose**: Entry point for the automated pipeline, setting generation parameters
- **Trigger**: User clicks "New Project" and fills topic/duration form
- **Progression**: Form input → validation → project initialization → pipeline queue
- **Success criteria**: Project appears in dashboard with "Initializing" status

### Pipeline Status Dashboard
- **Functionality**: Real-time monitoring of all 11 pipeline stages across active projects
- **Purpose**: Visibility into complex multi-stage processes for debugging and optimization
- **Trigger**: Navigation to dashboard or automatic updates via WebSocket
- **Progression**: Project list → stage breakdown → detailed logs → performance metrics
- **Success criteria**: Clear visual representation of pipeline progress with actionable error states

### Script & Shot Management
- **Functionality**: Review and edit AI-generated scripts, shot lists, and timing beats
- **Purpose**: Human oversight and refinement of automated content generation
- **Trigger**: Pipeline reaches script generation stage or manual navigation
- **Progression**: Generated script display → editing interface → approval → next stage trigger
- **Success criteria**: Scripts can be modified and changes propagate to rendering pipeline

### Render Preview & QC Review
- **Functionality**: Preview rendered shots with self-review metrics and LLaVA feedback
- **Purpose**: Visual quality control before final assembly
- **Trigger**: Shot completes initial render or QC analysis
- **Progression**: Shot thumbnail → full preview → metrics display → approve/reject decision
- **Success criteria**: Clear pass/fail indicators with specific improvement suggestions

### Voice Alignment Interface
- **Functionality**: Upload final voiceover, review forced alignment, and trigger retiming
- **Purpose**: Synchronize human narration with generated visuals
- **Trigger**: User uploads audio file after initial pipeline completion
- **Progression**: Audio upload → transcription/alignment → timing visualization → retiming approval
- **Success criteria**: Accurate word-level alignment with visual beat markers

### System Resource Monitor
- **Functionality**: Track GPU/CPU usage, memory consumption, and model loading status
- **Purpose**: Optimize performance on local hardware constraints (i9-9900KS + RTX 2080 Ti)
- **Trigger**: Continuous monitoring during active pipeline operations
- **Progression**: Resource polling → threshold alerts → optimization suggestions
- **Success criteria**: Prevents system overload and suggests optimal batching strategies

## Edge Case Handling

- **Pipeline Failures**: Automatic retry with exponential backoff, detailed error logging with suggested manual interventions
- **Resource Exhaustion**: Graceful degradation with quality reduction options and batch size adjustments
- **Model Loading Issues**: Fallback to lower quantization levels with performance impact warnings
- **Corrupted Renders**: Automatic shot regeneration with different random seeds
- **Voice Alignment Failures**: Manual timing adjustment interface with visual waveform editor
- **Network Interruptions**: Full offline operation with local model serving via llama.cpp

## Design Direction

The interface should evoke the precision and sophistication of professional broadcast production tools while maintaining the accessibility needed for independent creators. Clean, technical aesthetic with emphasis on data visualization and workflow clarity over decorative elements.

## Color Selection

**Triadic** (three equally spaced colors) - Using deep technical blues, warm accent oranges, and neutral grays to create a professional broadcast environment that emphasizes data clarity and workflow progression.

- **Primary Color**: Deep Technical Blue `oklch(0.35 0.15 230)` - Communicates reliability and technical precision
- **Secondary Colors**: 
  - Neutral Gray `oklch(0.25 0.02 230)` - Supporting backgrounds and secondary text
  - Cool White `oklch(0.95 0.02 230)` - Primary content areas and active states
- **Accent Color**: Warm Orange `oklch(0.65 0.18 45)` - Progress indicators, success states, and call-to-action elements
- **Foreground/Background Pairings**:
  - Background (Cool White): Dark Gray text `oklch(0.25 0.02 230)` - Ratio 15.2:1 ✓
  - Card (Neutral Gray): Cool White text `oklch(0.95 0.02 230)` - Ratio 15.8:1 ✓
  - Primary (Technical Blue): Cool White text `oklch(0.95 0.02 230)` - Ratio 9.1:1 ✓
  - Secondary (Dark Gray): Cool White text `oklch(0.95 0.02 230)` - Ratio 15.8:1 ✓
  - Accent (Warm Orange): Cool White text `oklch(0.95 0.02 230)` - Ratio 4.9:1 ✓

## Font Selection

Typography should convey technical precision and professional broadcast quality, using monospace elements for code/data and clean sans-serif for interface elements.

- **Typographic Hierarchy**:
  - H1 (Project Titles): Inter Bold/32px/tight letter spacing
  - H2 (Pipeline Stages): Inter Semibold/24px/normal spacing  
  - H3 (Shot Titles): Inter Medium/20px/normal spacing
  - Body Text: Inter Regular/16px/relaxed line height
  - Code/Data: JetBrains Mono Regular/14px/fixed spacing
  - Labels: Inter Medium/14px/wide letter spacing/uppercase

## Animations

Animations should reinforce the systematic, precise nature of the production pipeline with smooth state transitions and progress indicators that feel both technical and organic.

- **Purposeful Meaning**: Motion emphasizes workflow progression and system status changes, using eased transitions that mirror the careful orchestration of the rendering pipeline
- **Hierarchy of Movement**: Pipeline stage transitions receive primary animation focus, followed by data updates and user interactions

## Component Selection

- **Components**: 
  - Progress components for multi-stage pipeline visualization
  - Cards for project/shot organization with status indicators
  - Tables for detailed metrics and logs with sorting/filtering
  - Dialogs for project creation and configuration
  - Tabs for organizing complex multi-view interfaces
  - Badges for status indicators and tags
  - Tooltips for technical explanations and metrics

- **Customizations**:
  - Custom pipeline progress component combining linear progress with stage markers
  - Specialized render preview component with scrub controls and metrics overlay
  - Real-time resource monitor with animated charts
  - Audio waveform visualization component for voice alignment

- **States**: 
  - Buttons emphasize pipeline actions (start, pause, retry) with loading states
  - Progress indicators show detailed completion percentages and error states
  - Cards have distinct visual states for different pipeline stages

- **Icon Selection**: 
  - Phosphor icons for technical actions (Play, Pause, ArrowsClockwise, Monitor, Microphone)
  - Custom pipeline stage icons for specialized processes

- **Spacing**: 
  - Consistent 16px base spacing with 8px micro-spacing for dense data displays
  - 24px section spacing to separate major workflow areas
  - 32px for primary content separation

- **Mobile**: 
  - Responsive dashboard with collapsible sidebars
  - Touch-optimized controls for mobile monitoring
  - Priority-based information hierarchy for smaller screens