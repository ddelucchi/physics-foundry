export type DataProvenance = 'demo' | 'fixture' | 'live'

export interface ProvenanceDescriptor {
  kind: DataProvenance
  label: string
  description: string
}

export const DATA_PROVENANCE: Record<DataProvenance, ProvenanceDescriptor> = {
  demo: {
    kind: 'demo',
    label: 'Demo data',
    description: 'Synthetic values used to exercise the interface; not measured system output.',
  },
  fixture: {
    kind: 'fixture',
    label: 'Fixture data',
    description: 'Deterministic test values used to verify orchestration semantics.',
  },
  live: {
    kind: 'live',
    label: 'Live data',
    description: 'Values received from an actual service, worker, renderer, or measurement path.',
  },
}

export const isMeasuredProvenance = (kind: DataProvenance): boolean => kind === 'live'
