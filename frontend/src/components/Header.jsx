import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Icon } from '../components/UI'

function initials(name = '') {
  return name.trim().split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase()
}

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = async () => {
    setOpen(false)
    await logout()
    navigate('/login')
  }

  return (
    <header className="header">
      <Link to="/" className="header-brand">
        <Icon name="graduation" size={22} color="var(--primary)" style={{ marginRight: '.4rem' }} />
        LMS
      </Link>

      <nav className="header-nav">
        {user?.role === 'instructor' && (
          <>
            <Link to="/instructor/dashboard">Dashboard</Link>
            <Link to="/catalog">Catalog</Link>
          </>
        )}
        {user?.role === 'student' && (
          <>
            <Link to="/student/dashboard">My Learning</Link>
            <Link to="/catalog">Browse Courses</Link>
          </>
        )}

        {user && (
          <div ref={ref} style={{ position: 'relative' }}>
            <button
              onClick={() => setOpen(v => !v)}
              aria-label="User menu"
              style={{
                display: 'flex', alignItems: 'center', gap: '.5rem',
                background: 'none', border: 'none', cursor: 'pointer', padding: '0',
              }}
            >
              <span style={{
                width: 34, height: 34, borderRadius: '50%',
                background: 'var(--primary)', color: '#fff',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '.8rem', fontWeight: 700, flexShrink: 0,
              }}>
                {initials(user.full_name)}
              </span>
              <span style={{ fontSize: '.85rem', color: 'var(--gray-700)', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.full_name}
              </span>
              <span style={{ fontSize: '.7rem', color: 'var(--gray-400)' }}>{open ? '▲' : '▼'}</span>
            </button>

            {open && (
              <div style={{
                position: 'absolute', right: 0, top: 'calc(100% + .5rem)',
                background: '#fff', border: '1px solid var(--gray-200)',
                borderRadius: 8, boxShadow: '0 4px 16px rgba(0,0,0,.1)',
                minWidth: 220, zIndex: 100, overflow: 'hidden',
              }}>
                {/* User info block */}
                <div style={{ padding: '1rem', borderBottom: '1px solid var(--gray-100)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
                    <span style={{
                      width: 42, height: 42, borderRadius: '50%',
                      background: 'var(--primary)', color: '#fff',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '1rem', fontWeight: 700, flexShrink: 0,
                    }}>
                      {initials(user.full_name)}
                    </span>
                    <div style={{ overflow: 'hidden' }}>
                      <div style={{ fontWeight: 600, fontSize: '.9rem', color: 'var(--gray-800)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {user.full_name}
                      </div>
                      <div style={{ fontSize: '.78rem', color: 'var(--gray-400)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {user.email}
                      </div>
                      <span style={{
                        display: 'inline-block', marginTop: '.25rem',
                        fontSize: '.7rem', fontWeight: 600, textTransform: 'uppercase',
                        letterSpacing: '.05em', padding: '1px 6px', borderRadius: 4,
                        background: user.role === 'instructor' ? '#dbeafe' : '#dcfce7',
                        color: user.role === 'instructor' ? '#1d4ed8' : '#15803d',
                      }}>
                        {user.role}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div style={{ padding: '.5rem' }}>
                  <button
                    onClick={handleLogout}
                    style={{
                      width: '100%', textAlign: 'left', padding: '.6rem .75rem',
                      background: 'none', border: 'none', cursor: 'pointer',
                      borderRadius: 6, fontSize: '.875rem', color: '#ef4444',
                      display: 'flex', alignItems: 'center', gap: '.5rem',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = '#fef2f2'}
                    onMouseLeave={e => e.currentTarget.style.background = 'none'}
                  >
                    <Icon name="log_out" size={16} /> Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </nav>
    </header>
  )
}
