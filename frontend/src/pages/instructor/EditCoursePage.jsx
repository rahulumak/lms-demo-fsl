import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import CourseFormPage from './CourseFormPage'
import { Spinner } from '../../components/UI'
import AppLayout from '../../layouts/AppLayout'
import api from '../../services/api'

export default function EditCoursePage() {
  const { courseId } = useParams()
  const { data: course, isLoading } = useQuery({
    queryKey: ['instructor-course', Number(courseId)],
    queryFn: () => api.get(`/instructor/courses/${courseId}`).then(r => r.data),
  })

  if (isLoading) return <AppLayout><div className="loading-screen"><Spinner /></div></AppLayout>

  return <CourseFormPage courseId={Number(courseId)} initial={course} />
}
