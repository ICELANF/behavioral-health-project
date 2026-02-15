/**
 * BehaviorOS — HTTP 客户端
 * 统一的 axios 实例，JWT 自动注入，401 刷新，错误统一处理
 */

import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { ApiError } from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

// =====================================================================
// 创建实例
// =====================================================================

const http: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// =====================================================================
// Token 管理
// =====================================================================

const TOKEN_KEY = 'bos_access_token'
const USER_KEY = 'bos_user'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getStoredUser(): any | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try { return JSON.parse(raw) } catch { return null }
}

export function setStoredUser(user: any): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

// =====================================================================
// 请求拦截器：注入 JWT
// =====================================================================

http.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// =====================================================================
// 响应拦截器：统一错误处理
// =====================================================================

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const status = error.response?.status || 0
    const detail = error.response?.data?.detail || error.message

    const apiError: ApiError = { status, message: detail }

    if (status === 401) {
      removeToken()
      window.dispatchEvent(new CustomEvent('auth:expired'))
    } else if (status === 403) {
      console.warn('[HTTP] 权限不足:', detail)
    } else if (status === 422) {
      console.error('[HTTP] 参数校验失败:', detail)
    } else if (status === 429) {
      console.warn('[HTTP] 请求频率限制:', detail)
    }

    return Promise.reject(apiError)
  }
)

export default http
