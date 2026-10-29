import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import AppLayout from '../../layouts/AppLayout'
import { Spinner, ErrorMessage, EmptyState, StatusBadge, Icon } from '../../components/UI'
import api from '../../services/api'

function LessonModal({ courseId, lesson, onClose }) {
  const qc = useQueryClient()
  const isEdit = !!lesson
  const [form, setForm] = useState(lesson || { title: '', content: '', video_url: '', duration_minutes: '', is_published: false })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) { setError('Title is required'); return }
    setError('')
    setLoading(true)
    try {
      const payload = {
        title: form.title,
        content: form.content || null,
        video_url: form.video_url || null,
        duration_minutes: form.duration_minutes ? Number(form.duration_minutes) : null,
        is_published: form.is_published,
      }
      if (isEdit) {
        await api.patch(`/instructor/courses/${courseId}/lessons/${lesson.id}`, payload)
      } else {
        await api.post(`/instructor/courses/${courseId}/lessons`, payload)
      }
      qc.invalidateQueries({ queryKey: ['instructor-lessons', courseId] })
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Save failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}>
      <div className="card" style={{ width: '100%', maxWidth: 560, maxHeight: '90vh', overflowY: 'auto' }}>
        <h2 style={{ marginBottom: '1rem' }}>{isEdit ? 'Edit Lesson' : 'Add Lesson'}</h2>
        <ErrorMessage message={error} />
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="l-title">Title *</label>
            <input id="l-title" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
          </div>
          <div className="form-group">
            <label htmlFor="l-content">Content (Markdown)</label>
            <textarea id="l-content" style={{ minHeight: 140 }} value={form.content}
              onChange={e => setForm(f => ({ ...f, content: e.target.value }))} />
          </div>
          <div className="form-group">
            <label htmlFor="l-video">Video URL (YouTube/Vimeo)</label>
            <input id="l-video" type="url" value={form.video_url}
              onChange={e => setForm(f => ({ ...f, video_url: e.target.value }))} />
          </div>
          <div className="form-group">
            <label htmlFor="l-dur">Duration (minutes)</label>
            <input id="l-dur" type="number" min="0" value={form.duration_minutes}
              onChange={e => setForm(f => ({ ...f, duration_minutes: e.target.value }))} />
          </div>
          <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '.5rem' }}>
            <input id="l-pub" type="checkbox" checked={form.is_published}
              onChange={e => setForm(f => ({ ...f, is_published: e.target.checked }))} style={{ width: 'auto' }} />
            <label htmlFor="l-pub" style={{ margin: 0 }}>Published</label>
          </div>
          <div style={{ display: 'flex', gap: '.75rem' }}>
            <button className="btn btn-primary" disabled={loading}>{loading ? 'Saving…' : 'Save'}</button>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function LessonsPage() {
  const { courseId } = useParams()
  const cid = Number(courseId)
  const qc = useQueryClient()
  const [modal, setModal] = useState(null)
  const [deleteId, setDeleteId] = useState(null)
  const [actionError, setActionError] = useState('')

  const { data: lessons, isLoading, error } = useQuery({
    queryKey: ['instructor-lessons', cid],
    queryFn: () => api.get(`/instructor/courses/${cid}/lessons`).then(r => r.data),
  })

  const { data: course } = useQuery({
    queryKey: ['instructor-course', cid],
    queryFn: () => api.get(`/instructor/courses/${cid}`).then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/instructor/courses/${cid}/lessons/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['instructor-lessons', cid] }); setDeleteId(null); setActionError('') },
    onError: (err) => setActionError(err.response?.data?.detail || 'Failed to delete lesson. Please try again.'),
  })

  const publishCourseMutation = useMutation({
    mutationFn: () => api.post(`/instructor/courses/${cid}/publish`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['instructor-course', cid] })
      qc.invalidateQueries({ queryKey: ['instructor-courses'] })
      setActionError('')
    },
    onError: (err) => setActionError(err.response?.data?.detail || 'Failed to publish course. Please try again.'),
  })

  const archiveMutation = useMutation({
    mutationFn: () => api.post(`/instructor/courses/${cid}/archive`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['instructor-course', cid] })
      qc.invalidateQueries({ queryKey: ['instructor-courses'] })
      setActionError('')
    },
    onError: (err) => setActionError(err.response?.data?.detail || 'Failed to archive course. Please try again.'),
  })

  return (
    <AppLayout>
      <div className="page-header">
        <div>
          <h1 className="page-title">{course?.title || 'Lessons'}</h1>
          {course && <StatusBadge status={course.status} />}
        </div>
        <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap' }}>
          <Link to={`/instructor/courses/${cid}/edit`} className="btn btn-secondary btn-sm">Edit Course</Link>
          <Link to={`/instructor/courses/${cid}/progress`} className="btn btn-secondary btn-sm">Progress</Link>
          {course?.status === 'draft' && (
            <button className="btn btn-success btn-sm" onClick={() => publishCourseMutation.mutate()}>Publish</button>
          )}
          {course?.status === 'published' && (
            <button className="btn btn-secondary btn-sm" onClick={() => archiveMutation.mutate()}>Archive</button>
          )}
          <button className="btn btn-primary btn-sm" onClick={() => setModal('add')}>+ Add Lesson</button>
        </div>
      </div>

      {isLoading && <div className="loading-screen"><Spinner /></div>}
      {error && <ErrorMessage message="Failed to load lessons. Please refresh the page." />}
      {actionError && <ErrorMessage message={actionError} />}
      {!isLoading && lessons?.length === 0 && (
        <EmptyState icon="file_text" title="No lessons yet" message="Add your first lesson."
          action={<button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => setModal('add')}>Add Lesson</button>} />
      )}

      <div className="lesson-list">
        {lessons?.map((lesson, idx) => (
          <div key={lesson.id} className="lesson-item" style={{ cursor: 'default' }}>
            <span className="lesson-check">
              {lesson.is_published
                ? <Icon name="check_circle" size={18} color="var(--success)" />
                : <Icon name="file_text" size={18} color="var(--gray-400)" />}
            </span>
            <span style={{ color: 'var(--gray-400)', fontSize: '.8rem', minWidth: '1.5rem' }}>{lesson.position}</span>
            <span className="lesson-title">{lesson.title}</span>
            {lesson.duration_minutes && <span style={{ fontSize: '.8rem', color: 'var(--gray-400)' }}>{lesson.duration_minutes}m</span>}
            <div style={{ display: 'flex', gap: '.4rem' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setModal(lesson)}>Edit</button>
              <button className="btn btn-danger btn-sm" onClick={() => setDeleteId(lesson.id)}>Delete</button>
            </div>
          </div>
        ))}
      </div>

      {modal && (
        <LessonModal courseId={cid} lesson={modal === 'add' ? null : modal} onClose={() => setModal(null)} />
      )}

      {deleteId && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}>
          <div className="card" style={{ maxWidth: 360, textAlign: 'center' }}>
            <p style={{ marginBottom: '1rem' }}>Delete this lesson? This cannot be undone.</p>
            <div style={{ display: 'flex', gap: '.75rem', justifyContent: 'center' }}>
              <button className="btn btn-danger" onClick={() => deleteMutation.mutate(deleteId)}>Delete</button>
              <button className="btn btn-secondary" onClick={() => setDeleteId(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  )
}
