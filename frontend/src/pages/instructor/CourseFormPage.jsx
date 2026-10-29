import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import AppLayout from '../../layouts/AppLayout'
import { ErrorMessage } from '../../components/UI'
import api from '../../services/api'

export default function CourseFormPage({ courseId, initial }) {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const isEdit = !!courseId
  const [form, setForm] = useState({ title: '', short_description: '', description: '', thumbnail_url: '' })
  const [initialised, setInitialised] = useState(false)

  // Populate form once initial data arrives (fixes blank form for seeded/existing courses)
  if (initial && !initialised) {
    setForm({
      title: initial.title || '',
      short_description: initial.short_description || '',
      description: initial.description || '',
      thumbnail_url: initial.thumbnail_url || '',
    })
    setInitialised(true)
  }
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) { setError('Title is required'); return }
    setError('')
    setLoading(true)
    try {
      const payload = { ...form }
      if (!payload.thumbnail_url) delete payload.thumbnail_url
      if (isEdit) {
        await api.patch(`/instructor/courses/${courseId}`, payload)
      } else {
        const r = await api.post('/instructor/courses', payload)
        qc.invalidateQueries({ queryKey: ['instructor-courses'] })
        navigate(`/instructor/courses/${r.data.id}/edit`)
        return
      }
      qc.invalidateQueries({ queryKey: ['instructor-courses'] })
      qc.invalidateQueries({ queryKey: ['instructor-course', courseId] })
      navigate('/instructor/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Save failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title">{isEdit ? 'Edit Course' : 'New Course'}</h1>
      </div>
      <div className="card" style={{ maxWidth: 640 }}>
        <ErrorMessage message={error} />
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Title *</label>
            <input id="title" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} required />
          </div>
          <div className="form-group">
            <label htmlFor="short_description">Short Description</label>
            <input id="short_description" value={form.short_description}
              onChange={e => setForm(f => ({ ...f, short_description: e.target.value }))} />
          </div>
          <div className="form-group">
            <label htmlFor="description">Full Description</label>
            <textarea id="description" value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          </div>
          <div className="form-group">
            <label htmlFor="thumbnail_url">Thumbnail URL</label>
            <input id="thumbnail_url" type="url" value={form.thumbnail_url}
              onChange={e => setForm(f => ({ ...f, thumbnail_url: e.target.value }))} />
          </div>
          <div style={{ display: 'flex', gap: '.75rem' }}>
            <button className="btn btn-primary" disabled={loading}>{loading ? 'Saving…' : 'Save'}</button>
            <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)}>Cancel</button>
          </div>
        </form>
      </div>
    </AppLayout>
  )
}
