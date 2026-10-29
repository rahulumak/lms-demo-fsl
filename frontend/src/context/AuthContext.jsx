import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { setAccessToken, clearAccessToken, setSessionExpiredHandler } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined) // undefined = loading
  const navigate = useNavigate()

  const fetchMe = useCallback(async () => {
    try {
      const r = await api.get('/auth/me')
      setUser(r.data)
    } catch {
      setUser(null)
    }
  }, [])

  // Register handler so api.js can force logout on session expiry
  useEffect(() => {
    setSessionExpiredHandler(() => {
      setUser(null)
      navigate('/login', { replace: true, state: { message: 'Your session has expired. Please sign in again.' } })
    })
  }, [navigate])

  // On mount try to restore session via refresh cookie
  useEffect(() => {
    api.post('/auth/refresh')
      .then((r) => { setAccessToken(r.data.access_token); return fetchMe() })
      .catch(() => setUser(null))
  }, [fetchMe])

  const login = async (email, password) => {
    const r = await api.post('/auth/login', { email, password })
    setAccessToken(r.data.access_token)
    await fetchMe()
  }

  const logout = async () => {
    try { await api.post('/auth/logout') } catch {}
    clearAccessToken()
    setUser(null)
  }

  const register = async (full_name, email, password) => {
    await api.post('/auth/register', { full_name, email, password })
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
