import axios from 'axios'
import storage from '@/utils/storage'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Token 刷新状态（防止并发刷新）
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (error: any) => void
}> = []

function processQueue(error: any, token: string | null = null) {
  failedQueue.forEach(prom => {
    if (token) {
      prom.resolve(token)
    } else {
      prom.reject(error)
    }
  })
  failedQueue = []
}

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证Token
    const token = storage.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 添加用户ID头（兼容旧的MP API）
    const user = storage.getAuthUser()
    if (user?.id) {
      config.headers['X-User-ID'] = String(user.id)
    }
    // FormData: let axios auto-set Content-Type with correct multipart boundary
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 — 401 时自动刷新 Token 并重试
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      // 不对 login/refresh 端点做刷新 (防死循环)
      const url = originalRequest.url || ''
      if (url.includes('/auth/login') || url.includes('/auth/refresh') || url.includes('/auth/register')) {
        return Promise.reject(error)
      }

      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        // 无 refresh_token → 清除认证，按旧逻辑处理
        storage.clearAuth()
        const path = window.location.pathname
        const publicPages = ['/portal', '/login', '/register', '/home/observer', '/behavior-assessment', '/v3/knowledge', '/coach-directory', '/expert-hub', '/chat', '/wechat/callback']
        if (!publicPages.some(p => path.startsWith(p))) {
          window.location.href = '/portal'
        }
        return Promise.reject(error)
      }

      if (isRefreshing) {
        // 已在刷新中 → 排队等待
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          originalRequest._retry = true
          return api(originalRequest)
        }).catch(err => Promise.reject(err))
      }

      isRefreshing = true
      originalRequest._retry = true

      try {
        // 尝试 V1 刷新端点
        const res = await axios.post(
          (import.meta.env.VITE_API_BASE_URL || '') + '/api/v1/auth/refresh',
          { refresh_token: refreshToken },
          { headers: { 'Content-Type': 'application/json' } }
        )
        const data = res.data
        const newToken = data.access_token
        if (newToken) {
          storage.setToken(newToken)
          if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token)
          }
          processQueue(null, newToken)
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return api(originalRequest)
        }
        throw new Error('刷新返回无 token')
      } catch (refreshError) {
        processQueue(refreshError, null)
        // 刷新也失败 → 清除认证
        storage.clearAuth()
        localStorage.removeItem('refresh_token')
        const path = window.location.pathname
        const publicPages = ['/portal', '/login', '/register', '/home/observer', '/behavior-assessment', '/v3/knowledge', '/coach-directory', '/expert-hub', '/chat', '/wechat/callback']
        if (!publicPages.some(p => path.startsWith(p))) {
          window.location.href = '/portal'
        }
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default api
