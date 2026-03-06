import axios from 'axios'

const BASE_URL = import.meta.env.PROD
  ? ''  // production: same domain, nginx proxies /api/
  : 'http://localhost:8000'

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (config.data instanceof FormData) delete config.headers['Content-Type']
  return config
})

http.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.hash = '#/login'
    }
    return Promise.reject(err)
  }
)

export default http
