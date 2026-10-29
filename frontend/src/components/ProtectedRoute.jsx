import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute({ children, role }) {
  const { user } = useAuth()
  if (user === undefined) return <div className="loading-screen">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role) {
    return <Navigate to={user.role === 'instructor' ? '/instructor/dashboard' : '/student/dashboard'} replace />
  }
  return children
}
