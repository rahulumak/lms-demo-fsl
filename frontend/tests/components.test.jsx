import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ProgressBar, StatusBadge, EmptyState, ErrorMessage, CourseCard, Icon } from '../src/components/UI'

// ── ProgressBar ───────────────────────────────────────────────────────────────

describe('ProgressBar', () => {
  it('renders with correct width', () => {
    const { container } = render(<ProgressBar value={60} />)
    expect(container.querySelector('.progress-bar-fill').style.width).toBe('60%')
  })

  it('clamps below 0 to 0%', () => {
    const { container } = render(<ProgressBar value={-10} />)
    expect(container.querySelector('.progress-bar-fill').style.width).toBe('0%')
  })

  it('clamps above 100 to 100%', () => {
    const { container } = render(<ProgressBar value={150} />)
    expect(container.querySelector('.progress-bar-fill').style.width).toBe('100%')
  })

  it('renders 0% when value is undefined', () => {
    const { container } = render(<ProgressBar />)
    expect(container.querySelector('.progress-bar-fill').style.width).toBe('0%')
  })

  it('has correct aria attributes', () => {
    const { container } = render(<ProgressBar value={40} />)
    const bar = container.querySelector('.progress-bar-wrap')
    expect(bar).toHaveAttribute('role', 'progressbar')
    expect(bar).toHaveAttribute('aria-valuenow', '40')
    expect(bar).toHaveAttribute('aria-valuemin', '0')
    expect(bar).toHaveAttribute('aria-valuemax', '100')
  })
})

// ── StatusBadge ───────────────────────────────────────────────────────────────

describe('StatusBadge', () => {
  it('renders published badge with correct class', () => {
    render(<StatusBadge status="published" />)
    expect(screen.getByText('published')).toHaveClass('badge-published')
  })

  it('renders draft badge', () => {
    render(<StatusBadge status="draft" />)
    expect(screen.getByText('draft')).toHaveClass('badge-draft')
  })

  it('renders archived badge', () => {
    render(<StatusBadge status="archived" />)
    expect(screen.getByText('archived')).toHaveClass('badge-archived')
  })
})

// ── EmptyState ────────────────────────────────────────────────────────────────

describe('EmptyState', () => {
  it('renders title and message', () => {
    render(<EmptyState title="Nothing here" message="Try again" />)
    expect(screen.getByText('Nothing here')).toBeInTheDocument()
    expect(screen.getByText('Try again')).toBeInTheDocument()
  })

  it('renders without message', () => {
    render(<EmptyState title="Empty" />)
    expect(screen.getByText('Empty')).toBeInTheDocument()
  })

  it('renders action element', () => {
    render(<EmptyState title="Empty" action={<button>Create</button>} />)
    expect(screen.getByRole('button', { name: 'Create' })).toBeInTheDocument()
  })
})

// ── ErrorMessage ──────────────────────────────────────────────────────────────

describe('ErrorMessage', () => {
  it('renders the message text', () => {
    render(<ErrorMessage message="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders nothing when message is empty', () => {
    const { container } = render(<ErrorMessage message="" />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when message is undefined', () => {
    const { container } = render(<ErrorMessage />)
    expect(container.firstChild).toBeNull()
  })
})

// ── Icon ──────────────────────────────────────────────────────────────────────

describe('Icon', () => {
  it('renders a known icon without crashing', () => {
    const { container } = render(<Icon name="check_circle" />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('renders nothing for unknown icon name', () => {
    const { container } = render(<Icon name="nonexistent_icon" />)
    expect(container.querySelector('svg')).toBeNull()
  })

  it('applies custom size', () => {
    const { container } = render(<Icon name="book_open" size={32} />)
    const span = container.firstChild
    expect(span.style.width).toBe('32px')
    expect(span.style.height).toBe('32px')
  })
})

// ── CourseCard ────────────────────────────────────────────────────────────────

describe('CourseCard', () => {
  const baseCourse = {
    id: 1,
    title: 'Test Course',
    short_description: 'A short description',
    status: 'published',
    thumbnail_url: 'https://picsum.photos/seed/test/800/450',
  }

  it('renders course title', () => {
    render(<MemoryRouter><CourseCard course={baseCourse} /></MemoryRouter>)
    expect(screen.getByText('Test Course')).toBeInTheDocument()
  })

  it('renders short description', () => {
    render(<MemoryRouter><CourseCard course={baseCourse} /></MemoryRouter>)
    expect(screen.getByText('A short description')).toBeInTheDocument()
  })

  it('renders thumbnail image when thumbnail_url is set', () => {
    render(<MemoryRouter><CourseCard course={baseCourse} /></MemoryRouter>)
    const img = screen.getByRole('img', { name: 'Test Course' })
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute('src', baseCourse.thumbnail_url)
  })

  it('renders image placeholder icon when thumbnail_url is null', () => {
    const course = { ...baseCourse, thumbnail_url: null }
    const { container } = render(<MemoryRouter><CourseCard course={course} /></MemoryRouter>)
    expect(container.querySelector('img')).toBeNull()
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('renders status badge with correct class', () => {
    render(<MemoryRouter><CourseCard course={baseCourse} /></MemoryRouter>)
    const badge = screen.getByText('published')
    expect(badge).toHaveClass('badge-published')
    expect(badge).toHaveClass('course-card-status-badge')
  })

  it('does not render status badge when status is absent', () => {
    const course = { ...baseCourse, status: undefined }
    render(<MemoryRouter><CourseCard course={course} /></MemoryRouter>)
    expect(screen.queryByText('published')).not.toBeInTheDocument()
  })

  it('renders footer content', () => {
    render(
      <MemoryRouter>
        <CourseCard course={baseCourse} footer={<button>Edit</button>} />
      </MemoryRouter>
    )
    expect(screen.getByRole('button', { name: 'Edit' })).toBeInTheDocument()
  })
})
