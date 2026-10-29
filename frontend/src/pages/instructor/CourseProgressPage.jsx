import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import AppLayout from '../../layouts/AppLayout'
import { Spinner, ErrorMessage, ProgressBar, EmptyState } from '../../components/UI'
import api from '../../services/api'

export default function CourseProgressPage() {
  const { courseId } = useParams()
  const cid = Number(courseId)

  const { data: progress, isLoading, error } = useQuery({
    queryKey: ['instructor-progress', cid],
    queryFn: () => api.get(`/instructor/courses/${cid}/progress`).then(r => r.data),
  })

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title">Student Progress</h1>
        <Link to={`/instructor/courses/${cid}/lessons`} className="btn btn-secondary btn-sm">← Back to Lessons</Link>
      </div>

      {isLoading && <div className="loading-screen"><Spinner /></div>}
      {error && <ErrorMessage message="Failed to load progress" />}
      {!isLoading && progress?.length === 0 && (
        <EmptyState icon="users" title="No students enrolled yet" />
      )}

      {progress?.length > 0 && (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Email</th>
                  <th>Progress</th>
                  <th>Lessons</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {progress.map(s => (
                  <tr key={s.student_id}>
                    <td>{s.student_name}</td>
                    <td>{s.student_email}</td>
                    <td style={{ minWidth: 140 }}>
                      <ProgressBar value={s.progress_percentage} />
                      <span style={{ fontSize: '.8rem', color: 'var(--gray-600)' }}>{s.progress_percentage}%</span>
                    </td>
                    <td>{s.completed_lessons}/{s.total_published_lessons}</td>
                    <td><span className={`badge badge-${s.enrollment.status}`}>{s.enrollment.status}</span></td>
                    <td>
                      <Link to={`/instructor/courses/${cid}/students/${s.student_id}`} className="btn btn-ghost btn-sm">Details</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </AppLayout>
  )
}
