import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { ErrorMessage, Icon } from '../../components/UI'

function strengthLabel(pw) {
  if (pw.length === 0) return null
  let score = 0
  if (pw.length >= 8) score++
  if (/[A-Z]/.test(pw)) score++
  if (/[0-9]/.test(pw)) score++
  if (/[^A-Za-z0-9]/.test(pw)) score++
  if (score <= 1) return { label: 'Weak', color: '#ef4444', width: '25%' }
  if (score === 2) return { label: 'Fair', color: '#f97316', width: '50%' }
  if (score === 3) return { label: 'Good', color: '#eab308', width: '75%' }
  return { label: 'Strong', color: '#22c55e', width: '100%' }
}

export default function RegisterPage() {
  const { register, login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' })
  const [showPw, setShowPw] = useState(false)
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [loading, setLoading] = useState(false)

  const strength = strengthLabel(form.password)

  const set = (field) => (e) => {
    setForm(f => ({ ...f, [field]: e.target.value }))
    if (errors[field]) setErrors(e => ({ ...e, [field]: '' }))
  }

  const validate = () => {
    const e = {}
    if (!form.full_name.trim()) e.full_name = 'Full name is required'
    else if (form.full_name.trim().length > 200) e.full_name = 'Name must be 200 characters or fewer'
    if (!form.email.trim()) e.email = 'Email is required'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email address'
    if (form.password.length < 8) e.password = 'Password must be at least 8 characters'
    if (form.password !== form.confirm) e.confirm = 'Passwords do not match'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setErrors({})
    setServerError('')
    setLoading(true)
    try {
      await register(form.full_name.trim(), form.email.trim(), form.password)
      await login(form.email.trim(), form.password)
      navigate('/')
    } catch (err) {
      setServerError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Create Account</h1>
        <p style={{ color: 'var(--gray-400)', fontSize: '.9rem', marginBottom: '1.5rem', textAlign: 'center' }}>
          Join as a student — instructors are added by admins.
        </p>

        <ErrorMessage message={serverError} />

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="full_name">Full Name</label>
            <input
              id="full_name" type="text" autoComplete="name"
              value={form.full_name} onChange={set('full_name')}
              placeholder="Jane Smith"
              style={errors.full_name ? { borderColor: '#ef4444' } : {}}
            />
            {errors.full_name && <span className="form-error">{errors.full_name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email" type="email" autoComplete="email"
              value={form.email} onChange={set('email')}
              placeholder="jane@example.com"
              style={errors.email ? { borderColor: '#ef4444' } : {}}
            />
            {errors.email && <span className="form-error">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                id="password" type={showPw ? 'text' : 'password'} autoComplete="new-password"
                value={form.password} onChange={set('password')}
                placeholder="Min. 8 characters"
                style={{ paddingRight: '3rem', ...(errors.password ? { borderColor: '#ef4444' } : {}) }}
              />
              <button type="button" onClick={() => setShowPw(v => !v)}
                style={{ position: 'absolute', right: '.5rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--gray-400)' }}
                aria-label={showPw ? 'Hide password' : 'Show password'}>
                {showPw ? <Icon name="eye_off" size={18} color="var(--gray-400)" /> : <Icon name="eye" size={18} color="var(--gray-400)" />}
              </button>
            </div>
            {form.password.length > 0 && strength && (
              <div style={{ marginTop: '.4rem' }}>
                <div style={{ height: 4, background: 'var(--gray-200)', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: strength.width, background: strength.color, transition: 'width .3s' }} />
                </div>
                <span style={{ fontSize: '.75rem', color: strength.color }}>{strength.label}</span>
              </div>
            )}
            {errors.password && <span className="form-error">{errors.password}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="confirm">Confirm Password</label>
            <input
              id="confirm" type={showPw ? 'text' : 'password'} autoComplete="new-password"
              value={form.confirm} onChange={set('confirm')}
              placeholder="Repeat password"
              style={errors.confirm ? { borderColor: '#ef4444' } : {}}
            />
            {errors.confirm && <span className="form-error">{errors.confirm}</span>}
          </div>

          <button className="btn btn-primary" style={{ width: '100%', marginTop: '.5rem' }} disabled={loading}>
            {loading ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '.9rem' }}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
