import { useState, useEffect } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import AppLayout from '../../layouts/AppLayout'
import { Spinner, ErrorMessage, ProgressBar, EmptyState, Icon } from '../../components/UI'
import api from '../../services/api'

function renderContent(text) {
  if (!text) return null
  return text.split('\n').map((line, i) => {
    if (line.startsWith('# ')) return <h1 key={i}>{line.slice(2)}</h1>
    if (line.startsWith('## ')) return <h2 key={i}>{line.slice(3)}</h2>
    if (line.startsWith('### ')) return <h3 key={i}>{line.slice(4)}</h3>
    if (!line.trim()) return <br key={i} />
    return <p key={i}>{line}</p>
  })
}

export default function LearnPage() {
  const { courseId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const cid = Number(courseId)
  const qc = useQueryClient()
  const [completeError, setCompleteError] = useState('')

  const { data: lessons, isLoading: lessonsLoading, error: lessonsError } = useQuery({
    queryKey: ['student-lessons', cid],
    queryFn: () => api.get(`/students/me/courses/${cid}/lessons`).then(r => r.data),
  })

  const { data: progress, isLoading: progressLoading, error: progressError } = useQuery({
    queryKey: ['student-progress', cid],
    queryFn: () => api.get(`/students/me/courses/${cid}/progress`).then(r => r.data),
  })

  const progressMap = {}
  progress?.lesson_progress?.forEach(lp => { progressMap[lp.lesson_id] = lp })

  const lessonIdParam = searchParams.get('lesson')
  const [activeLessonId, setActiveLessonId] = useState(null)

  // Set initial lesson once lessons + progress are both loaded
  useEffect(() => {
    if (!lessons?.length || progressLoading) return
    if (lessonIdParam) {
      const id = Number(lessonIdParam)
      // Validate the lesson actually belongs to this course
      if (lessons.some(l => l.id === id)) {
        setActiveLessonId(id)
        return
      }
    }
    // Resume: first incomplete lesson, or first lesson
    const resume = lessons.find(l => progressMap[l.id]?.status !== 'completed') || lessons[0]
    setActiveLessonId(resume.id)
  }, [lessons, lessonIdParam, progressLoading]) // eslint-disable-line react-hooks/exhaustive-deps

  const activeLesson = lessons?.find(l => l.id === activeLessonId)
  const activeIdx = lessons?.findIndex(l => l.id === activeLessonId) ?? -1

  const startMutation = useMutation({
    mutationFn: (id) => api.post(`/students/me/lessons/${id}/start`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['student-progress', cid] }),
    // start errors are non-critical — don't surface to user
  })

  const completeMutation = useMutation({
    mutationFn: (id) => api.post(`/students/me/lessons/${id}/complete`),
    onSuccess: () => {
      setCompleteError('')
      qc.invalidateQueries({ queryKey: ['student-progress', cid] })
      qc.invalidateQueries({ queryKey: ['student-courses'] })
    },
    onError: (err) => {
      setCompleteError(err.response?.data?.detail || 'Failed to mark lesson complete. Please try again.')
    },
  })

  // Auto-start lesson when selected and not yet started
  useEffect(() => {
    if (!activeLessonId || !progress) return
    if (progressMap[activeLessonId]?.status === 'not_started') {
      startMutation.mutate(activeLessonId)
    }
  }, [activeLessonId, progress]) // eslint-disable-line react-hooks/exhaustive-deps

  const selectLesson = (id) => {
    setActiveLessonId(id)
    setCompleteError('')
    setSearchParams({ lesson: id })
  }

  const isCompleted = (id) => progressMap[id]?.status === 'completed'

  if (lessonsLoading || progressLoading) {
    return <AppLayout><div className="loading-screen"><Spinner /></div></AppLayout>
  }

  if (lessonsError || progressError) {
    return (
      <AppLayout>
        <ErrorMessage message="Failed to load course content. Please refresh the page." />
        <Link to="/student/dashboard" className="btn btn-secondary" style={{ marginTop: '1rem' }}>← Back to Dashboard</Link>
      </AppLayout>
    )
  }

  if (!lessons?.length) {
    return (
      <AppLayout>
        <EmptyState icon="inbox" title="No lessons available" message="This course has no published lessons yet." />
        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
          <Link to="/student/dashboard" className="btn btn-secondary">← Back to Dashboard</Link>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/student/dashboard" style={{ fontSize: '.85rem', color: 'var(--gray-600)' }}>← My Learning</Link>
      </div>

      <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <ProgressBar value={progress?.progress_percentage || 0} />
        </div>
        <span style={{ fontSize: '.9rem', color: 'var(--gray-600)', whiteSpace: 'nowrap' }}>
          {progress?.progress_percentage || 0}% — {progress?.completed_lessons || 0}/{progress?.total_published_lessons || 0} lessons
        </span>
      </div>

      <div className="learn-layout">
        <aside className="learn-sidebar">
          <h3 style={{ fontSize: '.9rem', fontWeight: 600, marginBottom: '.75rem', color: 'var(--gray-600)' }}>LESSONS</h3>
          <div className="lesson-list">
            {lessons.map(lesson => (
              <div key={lesson.id}
                className={`lesson-item ${lesson.id === activeLessonId ? 'active' : ''} ${isCompleted(lesson.id) ? 'completed' : ''}`}
                onClick={() => selectLesson(lesson.id)}
                role="button" tabIndex={0}
                onKeyDown={e => e.key === 'Enter' && selectLesson(lesson.id)}
                aria-current={lesson.id === activeLessonId ? 'true' : undefined}>
                <span className="lesson-check" aria-hidden="true">
                    {isCompleted(lesson.id)
                      ? <Icon name="check_circle" size={18} color="var(--success)" />
                      : <Icon name="circle" size={18} color="var(--gray-400)" />}
                  </span>
                <span className="lesson-title">{lesson.title}</span>
              </div>
            ))}
          </div>
        </aside>

        <div className="learn-content">
          {!activeLesson ? (
            <p style={{ color: 'var(--gray-400)' }}>Select a lesson to begin.</p>
          ) : (
            <>
              <h2 style={{ marginBottom: '1.5rem' }}>{activeLesson.title}</h2>

              {activeLesson.video_url && (
                <div style={{ marginBottom: '1.5rem', aspectRatio: '16/9', background: '#000', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
                  <iframe
                    src={activeLesson.video_url.replace('watch?v=', 'embed/')}
                    style={{ width: '100%', height: '100%', border: 'none' }}
                    allowFullScreen
                    title={activeLesson.title}
                  />
                </div>
              )}

              {activeLesson.content ? (
                <div className="markdown-content" style={{ marginBottom: '2rem' }}>
                  {renderContent(activeLesson.content)}
                </div>
              ) : (
                <p style={{ color: 'var(--gray-400)', marginBottom: '2rem', fontStyle: 'italic' }}>
                  No written content for this lesson.
                </p>
              )}

              {completeError && <ErrorMessage message={completeError} />}

              <div style={{ display: 'flex', gap: '.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                {activeIdx > 0 && (
                  <button className="btn btn-secondary" onClick={() => selectLesson(lessons[activeIdx - 1].id)}>← Previous</button>
                )}
                {!isCompleted(activeLessonId) ? (
                  <button className="btn btn-success"
                    disabled={completeMutation.isPending}
                    onClick={() => completeMutation.mutate(activeLessonId)}>
                    {completeMutation.isPending ? 'Saving…' : <><Icon name="check_circle" size={16} /> Mark Complete</>}
                  </button>
                ) : (
                  <span className="badge badge-completed" style={{ display: 'inline-flex', alignItems: 'center', gap: '.3rem' }}>
                    <Icon name="check_circle" size={14} color="var(--success)" /> Completed
                  </span>
                )}
                {activeIdx < lessons.length - 1 && (
                  <button className="btn btn-primary" onClick={() => selectLesson(lessons[activeIdx + 1].id)}>Next →</button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
