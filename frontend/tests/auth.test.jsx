import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LoginPage from '../src/pages/auth/LoginPage'
import RegisterPage from '../src/pages/auth/RegisterPage'

const mockLogin = vi.fn()
const mockRegister = vi.fn()
vi.mock('../src/context/AuthContext', () => ({
  useAuth: () => ({ login: mockLogin, register: mockRegister, user: null }),
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function wrap(ui) {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('LoginPage', () => {
  beforeEach(() => { mockLogin.mockReset(); mockNavigate.mockReset() })

  it('renders email and password fields', () => {
    wrap(<LoginPage />)
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
  })

  it('calls login and navigates on success', async () => {
    mockLogin.mockResolvedValue()
    wrap(<LoginPage />)
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('a@b.com', 'pass'))
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('shows error on login failure', async () => {
    mockLogin.mockRejectedValue({ response: { data: { detail: 'Invalid credentials' } } })
    wrap(<LoginPage />)
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument())
  })
})

describe('RegisterPage', () => {
  beforeEach(() => { mockRegister.mockReset(); mockLogin.mockReset(); mockNavigate.mockReset() })

  it('renders registration fields', () => {
    wrap(<RegisterPage />)
    expect(screen.getByLabelText('Full Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
  })

  it('shows validation error for short password', async () => {
    wrap(<RegisterPage />)
    fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'Alice' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'short' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: /register/i }))
    await waitFor(() => expect(screen.getByText(/at least 8/i)).toBeInTheDocument())
  })

  it('shows error when passwords do not match', async () => {
    wrap(<RegisterPage />)
    fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'Alice' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Password1!' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'Different1!' } })
    fireEvent.click(screen.getByRole('button', { name: /register/i }))
    await waitFor(() => expect(screen.getByText(/do not match/i)).toBeInTheDocument())
  })
})
