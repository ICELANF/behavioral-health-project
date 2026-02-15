/**
 * BehaviorOS — 行为处方 API 服务层 (FIX-12: Token Key 对齐)
 * ====================================
 * 修复: rxApi 独立 axios 实例使用 'access_token' 而非 'bos_access_token'
 *       导致行为处方请求全部无认证发送
 *
 * 方案: 导入共享 http 模块的 getToken(), 统一 Token Key
 * ====================================
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import { getToken } from '@/api/http'   // ← FIX-12: 使用共享 Token 管理
import type {
  ComputeRxRequest,
  ComputeRxResponse,
  RxPrescriptionDTO,
  RxListResponse,
  StrategyTemplateResponse,
  HandoffRequest,
  HandoffResponse,
  HandoffListResponse,
  CollaborateRequest,
  CollaborateResponse,
  AgentStatusResponse,
} from '../types/rx'

// =====================================================================
// 配置
// =====================================================================

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'
const RX_PREFIX = `${API_BASE}/rx`

// =====================================================================
// HTTP 实例
// =====================================================================

const http: AxiosInstance = axios.create({
  baseURL: RX_PREFIX,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截: 注入 token — FIX-12: 使用共享 getToken()
http.interceptors.request.use((config) => {
  const token = getToken()  // ← 之前: localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截: 统一错误处理
http.interceptors.response.use(
  (res) => res,
  (err: AxiosError) => {
    if (err.response?.status === 401) {
      window.dispatchEvent(new Event('auth:expired'))
    }
    return Promise.reject(err)
  }
)
