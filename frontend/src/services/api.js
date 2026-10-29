import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

// In-memory access token
let _accessToken = null
export const setAccessToken = (t) => { _accessToken = t }
export const getAccessToken = () => _accessToken
export const clearAccessToken = () => { _accessToken = null }

// Callback set by AuthContext to handle forced logout (e.g. expired session)
let _onSessionExpired = null
export const setSessionExpiredHandler = (fn) => { _onSessionExpired = fn }

const api = axios.create({
  baseURL: BASE,
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  if (_accessToken) config.headers.Authorization = `Bearer ${_accessToken}`
  return config
})

let _refreshing = null
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config
    // Don't retry refresh or login endpoints to avoid infinite loops
    const isAuthEndpoint = original.url?.includes('/auth/refresh') || original.url?.includes('/auth/login')
    if (error.response?.status === 401 && !original._retry && !isAuthEndpoint) {
      original._retry = true
      if (!_refreshing) {
        _refreshing = api.post('/auth/refresh', {}, { withCredentials: true })
          .then((r) => { setAccessToken(r.data.access_token); return r.data.access_token })
          .catch(() => {
            clearAccessToken()
            // Notify AuthContext the session has expired
            if (_onSessionExpired) _onSessionExpired()
            return null
          })
          .finally(() => { _refreshing = null })
      }
      const token = await _refreshing
      if (token) {
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      }
    }
    return Promise.reject(error)
  }
)

export default api
