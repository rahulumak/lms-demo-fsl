import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import AppLayout from '../../layouts/AppLayout'
import { CourseCard, ProgressBar, Spinner, EmptyState, ErrorMessage } from '../../components/UI'
import api from '../../services/api'

export default function StudentDashboard() {
  const { user } = useAuth()
  const { data: enrollments, isLoading, error } = useQuery({
    queryKey: ['student-courses'],
    queryFn: () => api.get('/students/me/courses').then(r => r.data),
  })

  const inProgress = enrollments?.filter(e => e.enrollment_status === 'active' && e.progress_percentage > 0).length || 0
  const completed = enrollments?.filter(e => e.enrollment_status === 'completed').length || 0

  // Find last accessed for "continue learning"
  const lastAccessed = enrollments
    ?.filter(e => e.last_accessed_at)
    .sort((a, b) => new Date(b.last_accessed_at) - new Date(a.last_accessed_at))[0]

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title">Welcome back, {user?.full_name} 👋</h1>
        <Link to="/catalog" className="btn btn-primary">Browse Courses</Link>
      </div>

      <div className="stats-grid">
        <div className="stat-card"><div className="stat-value">{enrollments?.length || 0}</div><div className="stat-label">Enrolled</div></div>
        <div className="stat-card"><div className="stat-value">{inProgress}</div><div className="stat-label">In Progress</div></div>
        <div className="stat-card"><div className="stat-value">{completed}</div><div className="stat-label">Completed</div></div>
      </div>

      {lastAccessed && (
        <div className="card" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '.8rem', color: 'var(--gray-400)', marginBottom: '.25rem' }}>Continue where you left off</div>
            <strong>{lastAccessed.course_title}</strong>
            <div style={{ marginTop: '.5rem', maxWidth: 240 }}>
              <ProgressBar value={lastAccessed.progress_percentage} />
              <span style={{ fontSize: '.8rem', color: 'var(--gray-600)' }}>{lastAccessed.progress_percentage}% complete</span>
            </div>
          </div>
          <Link to={`/student/courses/${lastAccessed.course_id}/learn`} className="btn btn-primary">Continue Learning →</Link>
        </div>
      )}

      {isLoading && <div className="loading-screen"><Spinner /></div>}
      {error && <ErrorMessage message="Failed to load courses" />}
      {!isLoading && enrollments?.length === 0 && (
        <EmptyState icon="graduation" title="No courses yet" message="Browse the catalog to find your first course."
          action={<Link to="/catalog" className="btn btn-primary" style={{ marginTop: '1rem' }}>Browse Courses</Link>} />
      )}

      <div className="card-grid">
        {enrollments?.map(e => (
          <CourseCard key={e.course_id} course={{ id: e.course_id, title: e.course_title, thumbnail_url: e.course_thumbnail }} footer={
            <>
              <div style={{ flex: 1 }}>
                <ProgressBar value={e.progress_percentage} />
                <span style={{ fontSize: '.8rem', color: 'var(--gray-600)' }}>{e.progress_percentage}%</span>
              </div>
              <Link to={`/student/courses/${e.course_id}/learn`} className="btn btn-primary btn-sm">
                {e.progress_percentage > 0 ? 'Continue' : 'Start'}
              </Link>
            </>
          } />
        ))}
      </div>
    </AppLayout>
  )
}
