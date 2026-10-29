import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import AppLayout from '../../layouts/AppLayout'
import { CourseCard, Spinner, ErrorMessage, EmptyState } from '../../components/UI'
import api from '../../services/api'

export default function CatalogPage() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [enrollErrors, setEnrollErrors] = useState({}) // per-course error map

  const { data, isLoading, error } = useQuery({
    queryKey: ['catalog', search],
    queryFn: () => api.get('/courses', { params: { search: search || undefined, limit: 50 } }).then(r => r.data),
  })

  const { data: myEnrollments } = useQuery({
    queryKey: ['student-courses'],
    queryFn: () => api.get('/students/me/courses').then(r => r.data),
    enabled: user?.role === 'student',
  })

  const enrolledIds = new Set(myEnrollments?.map(e => e.course_id) || [])

  const enrollMutation = useMutation({
    mutationFn: (courseId) => api.post(`/courses/${courseId}/enroll`),
    onSuccess: (_, courseId) => {
      setEnrollErrors(prev => ({ ...prev, [courseId]: '' }))
      qc.invalidateQueries({ queryKey: ['student-courses'] })
    },
    onError: (err, courseId) => {
      const msg = err.response?.data?.detail || 'Enrollment failed. Please try again.'
      setEnrollErrors(prev => ({ ...prev, [courseId]: msg }))
    },
  })

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title">Course Catalog</h1>
        <input
          type="search" placeholder="Search courses…" value={search}
          onChange={e => setSearch(e.target.value)}
          aria-label="Search courses"
          style={{ padding: '.5rem .75rem', border: '1px solid var(--gray-200)', borderRadius: 'var(--radius)', fontSize: '.9rem', width: 240 }}
        />
      </div>

      {isLoading && <div className="loading-screen"><Spinner /></div>}
      {error && <ErrorMessage message="Failed to load courses. Please refresh the page." />}
      {!isLoading && !error && data?.items?.length === 0 && (
        <EmptyState icon="search" title="No courses found" message={search ? `No results for "${search}". Try a different search term.` : 'No published courses available yet.'} />
      )}

      <div className="card-grid">
        {data?.items?.map(course => (
          <div key={course.id}>
            {enrollErrors[course.id] && <ErrorMessage message={enrollErrors[course.id]} />}
            <CourseCard course={course} footer={
              <>
                <span style={{ fontSize: '.8rem', color: 'var(--gray-400)' }}>{course.enrollment_count} student{course.enrollment_count !== 1 ? 's' : ''}</span>
                {user?.role === 'student' ? (
                  enrolledIds.has(course.id) ? (
                    <Link to={`/student/courses/${course.id}/learn`} className="btn btn-success btn-sm">Continue →</Link>
                  ) : (
                    <button className="btn btn-primary btn-sm"
                      disabled={enrollMutation.isPending && enrollMutation.variables === course.id}
                      onClick={() => {
                        setEnrollErrors(prev => ({ ...prev, [course.id]: '' }))
                        enrollMutation.mutate(course.id)
                      }}>
                      {enrollMutation.isPending && enrollMutation.variables === course.id ? 'Enrolling…' : 'Enroll'}
                    </button>
                  )
                ) : user?.role === 'instructor' ? (
                  <Link to={`/instructor/courses/${course.id}/lessons`} className="btn btn-ghost btn-sm">Manage</Link>
                ) : (
                  <Link to="/login" className="btn btn-primary btn-sm">Sign in to Enroll</Link>
                )}
              </>
            } />
          </div>
        ))}
      </div>
    </AppLayout>
  )
}
