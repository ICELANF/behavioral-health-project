/**
 * HTTP 客户端 — Axios + JWT 拦截器
 *
 * 自动: 请求附加 Bearer Token → 401 自动刷新 → 刷新失败跳登录
 */
import axios from 'axios'
import { useUserStore } from '../../stores/user'
import router from '../../router'

const http = axios.create({
  baseURL: '/api/v3',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── 请求拦截: 附加 Token ──
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('h5_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── 响应拦截: 401 自动刷新 ──
let isRefreshing = false
let pendingRequests = []

http.interceptors.response.use(
  (res) => res.data,  // 直接返回 data (剥掉 axios wrapper)
  async (error) => {
    const originalReq = error.config

    if (error.response?.status === 401 && !originalReq._retry) {
      originalReq._retry = true

      if (!isRefreshing) {
        isRefreshing = true
        try {
          const refreshToken = localStorage.getItem('refresh_token')
          if (!refreshToken) throw new Error('no refresh token')

          const { data } = await axios.post('/api/v3/auth/refresh', {
            refresh_token: refreshToken,
          })
          const tokens = data.data
          localStorage.setItem('h5_token', tokens.access_token)
          localStorage.setItem('refresh_token', tokens.refresh_token)

          // 重放队列
          pendingRequests.forEach((cb) => cb(tokens.access_token))
          pendingRequests = []

          originalReq.headers.Authorization = `Bearer ${tokens.access_token}`
          return http(originalReq)
        } catch {
          // 刷新失败 → 登出
          const store = useUserStore()
          store.logout()
          router.push('/login')
          return Promise.reject(error)
        } finally {
          isRefreshing = false
        }
      }

      // 已经在刷新中 → 排队
      return new Promise((resolve) => {
        pendingRequests.push((newToken) => {
          originalReq.headers.Authorization = `Bearer ${newToken}`
          resolve(http(originalReq))
        })
      })
    }

    return Promise.reject(error)
  }
)

export default http
