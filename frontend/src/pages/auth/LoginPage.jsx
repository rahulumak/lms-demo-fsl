import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { ErrorMessage, Icon } from '../../components/UI'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const sessionMessage = location.state?.message || ''

  const [form, setForm] = useState({ email: '', password: '' })
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (field) => (e) => {
    setForm(f => ({ ...f, [field]: e.target.value }))
    if (error) setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.email.trim()) { setError('Email is required'); return }
    if (!form.password) { setError('Password is required'); return }
    setError('')
    setLoading(true)
    try {
      await login(form.email.trim(), form.password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Sign In</h1>

        {sessionMessage && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: '1rem' }}>
            {sessionMessage}
          </div>
        )}

        <ErrorMessage message={error} />

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email" type="email" autoComplete="email"
              value={form.email} onChange={set('email')}
              placeholder="you@example.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                id="password" type={showPw ? 'text' : 'password'} autoComplete="current-password"
                value={form.password} onChange={set('password')}
                placeholder="Your password"
                style={{ paddingRight: '3rem' }}
              />
              <button type="button" onClick={() => setShowPw(v => !v)}
                style={{ position: 'absolute', right: '.5rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--gray-400)' }}
                aria-label={showPw ? 'Hide password' : 'Show password'}>
                {showPw ? <Icon name="eye_off" size={18} color="var(--gray-400)" /> : <Icon name="eye" size={18} color="var(--gray-400)" />}
              </button>
            </div>
          </div>

          <button className="btn btn-primary" style={{ width: '100%', marginTop: '.5rem' }} disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '.9rem' }}>
          No account? <Link to="/register">Create one</Link>
        </p>
      </div>
    </div>
  )
}
