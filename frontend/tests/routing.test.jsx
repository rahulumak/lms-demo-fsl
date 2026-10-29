import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '../src/components/ProtectedRoute'

vi.mock('../src/context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '../src/context/AuthContext'

function wrap(initialPath, role) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route path="/student/dashboard" element={<div>Student Dashboard</div>} />
        <Route path="/instructor/dashboard" element={<div>Instructor Dashboard</div>} />
        <Route path="/protected" element={
          <ProtectedRoute role={role}><div>Protected Content</div></ProtectedRoute>
        } />
      </Routes>
    </MemoryRouter>
  )
}

describe('ProtectedRoute', () => {
  it('redirects unauthenticated user to login', () => {
    useAuth.mockReturnValue({ user: null })
    wrap('/protected')
    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })

  it('shows loading when user is undefined', () => {
    useAuth.mockReturnValue({ user: undefined })
    wrap('/protected')
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders content for correct role', () => {
    useAuth.mockReturnValue({ user: { role: 'instructor' } })
    wrap('/protected', 'instructor')
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('redirects student trying to access instructor route', () => {
    useAuth.mockReturnValue({ user: { role: 'student' } })
    wrap('/protected', 'instructor')
    expect(screen.getByText('Student Dashboard')).toBeInTheDocument()
  })
})
