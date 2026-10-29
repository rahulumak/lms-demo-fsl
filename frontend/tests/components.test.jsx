import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressBar, StatusBadge, EmptyState } from '../src/components/UI'

describe('ProgressBar', () => {
  it('renders with correct width', () => {
    const { container } = render(<ProgressBar value={60} />)
    const fill = container.querySelector('.progress-bar-fill')
    expect(fill.style.width).toBe('60%')
  })

  it('clamps to 0-100', () => {
    const { container: c1 } = render(<ProgressBar value={-10} />)
    expect(c1.querySelector('.progress-bar-fill').style.width).toBe('0%')
    const { container: c2 } = render(<ProgressBar value={150} />)
    expect(c2.querySelector('.progress-bar-fill').style.width).toBe('100%')
  })
})

describe('StatusBadge', () => {
  it('renders published badge', () => {
    render(<StatusBadge status="published" />)
    expect(screen.getByText('published')).toHaveClass('badge-published')
  })
})

describe('EmptyState', () => {
  it('renders title and message', () => {
    render(<EmptyState title="Nothing here" message="Try again" />)
    expect(screen.getByText('Nothing here')).toBeInTheDocument()
    expect(screen.getByText('Try again')).toBeInTheDocument()
  })
})
