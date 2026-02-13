/**
 * request.ts — axios instance for new views (raw response, no data unwrap)
 *
 * Unlike api/index.ts which strips response.data via interceptor,
 * this instance returns the full axios response so callers can
 * use res.data?.data pattern consistently.
 */
import axios from 'axios'
import storage from '@/utils/storage'

const request = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 — 注入 token
request.interceptors.request.use(
  (config) => {
    const token = storage.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 — 401 时不自动跳转（由调用方决定）
request.interceptors.response.use(
  (response) => response,
  (error) => {
    // 不自动跳转登录页, 由各页面自行处理 401
    return Promise.reject(error)
  }
)

export default request
