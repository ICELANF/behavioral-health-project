/**
 * BehaviorOS — 行为处方 API 服务层
 * ====================================
 * 对接后端 8 个 REST 端点, 含错误处理、缓存和类型安全
 *
 * 端点映射:
 *   POST   /api/v1/rx/compute          → computeRx()
 *   GET    /api/v1/rx/{rx_id}          → getRx()
 *   GET    /api/v1/rx/user/{user_id}   → getUserRxHistory()
 *   GET    /api/v1/rx/strategies       → getStrategies()
 *   POST   /api/v1/rx/handoff          → initiateHandoff()
 *   GET    /api/v1/rx/handoff/{uid}    → getHandoffLog()
 *   POST   /api/v1/rx/collaborate      → collaborate()
 *   GET    /api/v1/rx/agents/status    → getAgentStatus()
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
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

// 请求拦截: 注入 token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('bos_access_token')  // FIX-12: 对齐 TOKEN_KEY
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截: 统一错误处理
http.interceptors.response.use(
  (res) => res,
  (err: AxiosError<{ detail?: string }>) => {
    const status = err.response?.status
    const detail = err.response?.data?.detail || err.message

    if (status === 401) {
      // token 过期, 触发重登录
      window.dispatchEvent(new CustomEvent('auth:expired'))
    } else if (status === 403) {
      console.warn('[RxAPI] 权限不足:', detail)
    } else if (status === 422) {
      console.error('[RxAPI] 参数校验失败:', detail)
    }

    return Promise.reject({
      status,
      message: detail,
      raw: err,
    })
  }
)

// =====================================================================
// 简单内存缓存
// =====================================================================

interface CacheEntry<T> {
  data: T
  expiry: number
}

const cache = new Map<string, CacheEntry<any>>()
const CACHE_TTL = 5 * 60 * 1000 // 5 分钟

function getCached<T>(key: string): T | null {
  const entry = cache.get(key)
  if (entry && Date.now() < entry.expiry) {
    return entry.data as T
  }
  cache.delete(key)
  return null
}

function setCache<T>(key: string, data: T, ttl = CACHE_TTL): void {
  cache.set(key, { data, expiry: Date.now() + ttl })
}

export function clearRxCache(): void {
  cache.clear()
}

// =====================================================================
// API 方法
// =====================================================================

/**
 * 1. 计算行为处方
 * POST /compute
 */
export async function computeRx(request: ComputeRxRequest): Promise<ComputeRxResponse> {
  const { data } = await http.post<ComputeRxResponse>('/compute', request)
  // 缓存结果
  if (data.prescription?.rx_id) {
    setCache(`rx:${data.prescription.rx_id}`, data.prescription)
  }
  return data
}

/**
 * 2. 获取处方详情
 * GET /{rx_id}
 */
export async function getRx(rxId: string): Promise<RxPrescriptionDTO> {
  const cached = getCached<RxPrescriptionDTO>(`rx:${rxId}`)
  if (cached) return cached

  const { data } = await http.get<RxPrescriptionDTO>(`/${rxId}`)
  setCache(`rx:${rxId}`, data)
  return data
}

/**
 * 3. 获取用户处方历史
 * GET /user/{user_id}?page=&page_size=
 */
export async function getUserRxHistory(
  userId: string,
  page = 1,
  pageSize = 20
): Promise<RxListResponse> {
  const { data } = await http.get<RxListResponse>(`/user/${userId}`, {
    params: { page, page_size: pageSize },
  })
  return data
}

/**
 * 4. 获取策略模板列表
 * GET /strategies?stage=
 */
export async function getStrategies(stage?: number): Promise<StrategyTemplateResponse> {
  const cacheKey = `strategies:${stage ?? 'all'}`
  const cached = getCached<StrategyTemplateResponse>(cacheKey)
  if (cached) return cached

  const { data } = await http.get<StrategyTemplateResponse>('/strategies', {
    params: stage !== undefined ? { stage } : {},
  })
  setCache(cacheKey, data, 15 * 60 * 1000) // 策略模板缓存 15 分钟
  return data
}

/**
 * 5. 发起 Agent 交接
 * POST /handoff
 */
export async function initiateHandoff(request: HandoffRequest): Promise<HandoffResponse> {
  const { data } = await http.post<HandoffResponse>('/handoff', request)
  return data
}

/**
 * 6. 获取交接日志
 * GET /handoff/{user_id}?limit=
 */
export async function getHandoffLog(
  userId: string,
  limit = 50
): Promise<HandoffListResponse> {
  const { data } = await http.get<HandoffListResponse>(`/handoff/${userId}`, {
    params: { limit },
  })
  return data
}

/**
 * 7. 协作编排执行
 * POST /collaborate
 */
export async function collaborate(request: CollaborateRequest): Promise<CollaborateResponse> {
  const { data } = await http.post<CollaborateResponse>('/collaborate', request)
  return data
}

/**
 * 8. Agent 注册状态
 * GET /agents/status
 */
export async function getAgentStatus(): Promise<AgentStatusResponse> {
  const cacheKey = 'agents:status'
  const cached = getCached<AgentStatusResponse>(cacheKey)
  if (cached) return cached

  const { data } = await http.get<AgentStatusResponse>('/agents/status')
  setCache(cacheKey, data, 30 * 1000) // 30 秒缓存
  return data
}

// =====================================================================
// 便捷导出
// =====================================================================

export const rxApi = {
  computeRx,
  getRx,
  getUserRxHistory,
  getStrategies,
  initiateHandoff,
  getHandoffLog,
  collaborate,
  getAgentStatus,
  clearCache: clearRxCache,
}

export default rxApi
