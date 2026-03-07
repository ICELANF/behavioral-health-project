import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`

  const sessionId = localStorage.getItem('session_id')
  if (sessionId) config.headers['X-Session-Id'] = sessionId

  return config
})

http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/behavior/#/prescription'
    }
    return Promise.reject(err)
  }
)

export default http
