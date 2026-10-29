import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import AppLayout from '../../layouts/AppLayout'
import { CourseCard, Spinner, EmptyState, ErrorMessage } from '../../components/UI'
import api from '../../services/api'

export default function InstructorDashboard() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleteError, setDeleteError] = useState('')

  const { data: courses, isLoading, error } = useQuery({
    queryKey: ['instructor-courses'],
    queryFn: () => api.get('/instructor/courses').then(r => r.data),
  })

  const invalidateCourses = () => qc.invalidateQueries({ queryKey: ['instructor-courses'] })

  const publishMutation = useMutation({
    mutationFn: (id) => api.post(`/instructor/courses/${id}/publish`),
    onSuccess: invalidateCourses,
  })

  const archiveMutation = useMutation({
    mutationFn: (id) => api.post(`/instructor/courses/${id}/archive`),
    onSuccess: invalidateCourses,
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/instructor/courses/${id}`),
    onSuccess: () => { invalidateCourses(); setDeleteTarget(null); setDeleteError('') },
    onError: (err) => setDeleteError(err.response?.data?.detail || 'Failed to delete course. Please try again.'),
  })

  const published = courses?.filter(c => c.status === 'published').length || 0
  const draft = courses?.filter(c => c.status === 'draft').length || 0
  const totalStudents = courses?.reduce((s, c) => s + (c.enrollment_count || 0), 0) || 0

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title">Welcome, {user?.full_name}</h1>
        <Link to="/instructor/courses/new" className="btn btn-primary">+ New Course</Link>
      </div>

      <div className="stats-grid">
        <div className="stat-card"><div className="stat-value">{courses?.length || 0}</div><div className="stat-label">Total Courses</div></div>
        <div className="stat-card"><div className="stat-value">{published}</div><div className="stat-label">Published</div></div>
        <div className="stat-card"><div className="stat-value">{draft}</div><div className="stat-label">Drafts</div></div>
        <div className="stat-card"><div className="stat-value">{totalStudents}</div><div className="stat-label">Enrolled Students</div></div>
      </div>

      {isLoading && <div className="loading-screen"><Spinner /></div>}
      {error && <ErrorMessage message="Failed to load courses" />}
      {!isLoading && courses?.length === 0 && (
        <EmptyState icon="book_open" title="No courses yet"
          message="Create your first course to get started."
          action={<Link to="/instructor/courses/new" className="btn btn-primary" style={{ marginTop: '1rem' }}>Create Course</Link>} />
      )}

      <div className="card-grid">
        {courses?.map(course => (
          <CourseCard key={course.id} course={course} footer={
            <div style={{ display: 'flex', gap: '.4rem', flexWrap: 'wrap', width: '100%' }}>
              <Link to={`/instructor/courses/${course.id}/edit`} className="btn btn-secondary btn-sm">Edit</Link>
              <Link to={`/instructor/courses/${course.id}/lessons`} className="btn btn-ghost btn-sm">Lessons</Link>
              <Link to={`/instructor/courses/${course.id}/progress`} className="btn btn-ghost btn-sm">Progress</Link>
              {course.status === 'draft' && (
                <button
                  className="btn btn-success btn-sm"
                  disabled={publishMutation.isPending && publishMutation.variables === course.id}
                  onClick={() => publishMutation.mutate(course.id)}
                >
                  {publishMutation.isPending && publishMutation.variables === course.id ? 'Publishing…' : 'Publish'}
                </button>
              )}
              {course.status === 'published' && (
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={archiveMutation.isPending && archiveMutation.variables === course.id}
                  onClick={() => archiveMutation.mutate(course.id)}
                >
                  {archiveMutation.isPending && archiveMutation.variables === course.id ? 'Archiving…' : 'Archive'}
                </button>
              )}
              <button
                className="btn btn-danger btn-sm"
                onClick={() => { setDeleteError(''); setDeleteTarget({ id: course.id, title: course.title }) }}
              >
                Delete
              </button>
            </div>
          } />
        ))}
      </div>

      {/* Delete Course Confirm Modal */}
      {deleteTarget && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}>
          <div className="card" style={{ maxWidth: 420, width: '100%' }}>
            <h2 style={{ marginBottom: '.75rem', color: '#ef4444' }}>Delete Course</h2>
            <p style={{ marginBottom: '.5rem' }}>
              Are you sure you want to delete <strong>"{deleteTarget.title}"</strong>?
            </p>
            <p style={{ fontSize: '.85rem', color: 'var(--gray-400)', marginBottom: '1.25rem' }}>
              This will permanently delete the course and all its lessons. This cannot be undone.
            </p>
            {deleteError && <ErrorMessage message={deleteError} />}
            <div style={{ display: 'flex', gap: '.75rem', justifyContent: 'flex-end' }}>
              <button
                className="btn btn-secondary"
                onClick={() => { setDeleteTarget(null); setDeleteError('') }}
                disabled={deleteMutation.isPending}
              >
                Cancel
              </button>
              <button
                className="btn btn-danger"
                onClick={() => deleteMutation.mutate(deleteTarget.id)}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? 'Deleting…' : 'Delete Course'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  )
}
