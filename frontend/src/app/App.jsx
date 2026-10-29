import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '../context/AuthContext'
import { ProtectedRoute } from '../components/ProtectedRoute'
import ErrorBoundary from '../components/ErrorBoundary'
import RootRedirect from './RootRedirect'

import LoginPage from '../pages/auth/LoginPage'
import RegisterPage from '../pages/auth/RegisterPage'
import InstructorDashboard from '../pages/instructor/InstructorDashboard'
import CourseFormPage from '../pages/instructor/CourseFormPage'
import EditCoursePage from '../pages/instructor/EditCoursePage'
import LessonsPage from '../pages/instructor/LessonsPage'
import CourseProgressPage from '../pages/instructor/CourseProgressPage'
import StudentDetailPage from '../pages/instructor/StudentDetailPage'
import StudentDashboard from '../pages/student/StudentDashboard'
import LearnPage from '../pages/student/LearnPage'
import CatalogPage from '../pages/catalog/CatalogPage'

const qc = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
    mutations: { retry: 0 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <AuthProvider>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<RootRedirect />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/catalog" element={<CatalogPage />} />

              {/* Instructor */}
              <Route path="/instructor/dashboard" element={<ProtectedRoute role="instructor"><InstructorDashboard /></ProtectedRoute>} />
              <Route path="/instructor/courses/new" element={<ProtectedRoute role="instructor"><CourseFormPage /></ProtectedRoute>} />
              <Route path="/instructor/courses/:courseId/edit" element={<ProtectedRoute role="instructor"><EditCoursePage /></ProtectedRoute>} />
              <Route path="/instructor/courses/:courseId/lessons" element={<ProtectedRoute role="instructor"><LessonsPage /></ProtectedRoute>} />
              <Route path="/instructor/courses/:courseId/progress" element={<ProtectedRoute role="instructor"><CourseProgressPage /></ProtectedRoute>} />
              <Route path="/instructor/courses/:courseId/students/:studentId" element={<ProtectedRoute role="instructor"><StudentDetailPage /></ProtectedRoute>} />

              {/* Student */}
              <Route path="/student/dashboard" element={<ProtectedRoute role="student"><StudentDashboard /></ProtectedRoute>} />
              <Route path="/student/courses/:courseId/learn" element={<ProtectedRoute role="student"><LearnPage /></ProtectedRoute>} />
            </Routes>
          </ErrorBoundary>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
