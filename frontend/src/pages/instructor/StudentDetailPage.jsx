import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import AppLayout from '../../layouts/AppLayout'
import { Spinner, ErrorMessage, ProgressBar, Icon } from '../../components/UI'
import api from '../../services/api'

export default function StudentDetailPage() {
  const { courseId, studentId } = useParams()
  const cid = Number(courseId)
  const sid = Number(studentId)

  const { data, isLoading, error } = useQuery({
    queryKey: ['instructor-student-progress', cid, sid],
    queryFn: () => api.get(`/instructor/courses/${cid}/students/${sid}/progress`).then(r => r.data),
  })

  const { data: lessons } = useQuery({
    queryKey: ['instructor-lessons', cid],
    queryFn: () => api.get(`/instructor/courses/${cid}/lessons`).then(r => r.data),
  })

  const progressMap = {}
  data?.lesson_progress?.forEach(lp => { progressMap[lp.lesson_id] = lp })

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title">Student Progress Detail</h1>
        <Link to={`/instructor/courses/${cid}/progress`} className="btn btn-secondary btn-sm">← Back</Link>
      </div>

      {isLoading && <div className="loading-screen"><Spinner /></div>}
      {error && <ErrorMessage message="Failed to load" />}

      {data && (
        <div className="card" style={{ maxWidth: 640 }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '.5rem' }}>
              <strong>Overall Progress</strong>
              <span>{data.progress_percentage}%</span>
            </div>
            <ProgressBar value={data.progress_percentage} />
            <p style={{ fontSize: '.85rem', color: 'var(--gray-600)', marginTop: '.5rem' }}>
              {data.completed_lessons} of {data.total_published_lessons} lessons completed
            </p>
          </div>

          <div className="lesson-list">
            {lessons?.filter(l => l.is_published).map(lesson => {
              const lp = progressMap[lesson.id]
              const status = lp?.status || 'not_started'
              return (
                <div key={lesson.id} className="lesson-item" style={{ cursor: 'default' }}>
                  <span className="lesson-check">
                    {status === 'completed'
                      ? <Icon name="check_circle" size={18} color="var(--success)" />
                      : status === 'in_progress'
                        ? <Icon name="play_circle" size={18} color="var(--primary)" />
                        : <Icon name="circle" size={18} color="var(--gray-400)" />}
                  </span>
                  <span className="lesson-title">{lesson.title}</span>
                  <span style={{ fontSize: '.8rem', color: 'var(--gray-400)' }}>{status.replace('_', ' ')}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </AppLayout>
  )
}
