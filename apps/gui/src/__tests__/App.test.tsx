import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import App from '../App'

vi.mock('@github/spark/hooks', () => ({
  useKV: vi.fn((_key: string, defaultValue: unknown) => [defaultValue, vi.fn()]),
}))

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the Physics Foundry identity and provenance boundary', () => {
    render(<App />)

    expect(screen.getByText('Physics Foundry')).toBeInTheDocument()
    expect(screen.getByText('Mixed provenance prototype')).toBeInTheDocument()
    expect(
      screen.getByText(/Pipeline and system panels read backend state/i),
    ).toBeInTheDocument()
  })

  it('renders the new request action', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: 'New Request' })).toBeInTheDocument()
  })

  it('opens bounded request creation', async () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'New Request' }))

    await waitFor(() => {
      expect(screen.getByText('Create Physics Request')).toBeInTheDocument()
      expect(screen.getByText('local request record')).toBeInTheDocument()
    })
  })

  it('exposes backend and explicitly labeled review surfaces', () => {
    render(<App />)

    expect(screen.getByRole('tab', { name: 'Requests' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Pipeline' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Code Review' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Audio Review' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'QA Demo' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Frame Review' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'System' })).toBeInTheDocument()
  })
})
