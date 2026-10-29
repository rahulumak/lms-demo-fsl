import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Spinner } from '../components/UI'

export default function RootRedirect() {
  const { user } = useAuth()
  if (user === undefined) return <div className="loading-screen"><Spinner /></div>
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'instructor') return <Navigate to="/instructor/dashboard" replace />
  return <Navigate to="/student/dashboard" replace />
}
