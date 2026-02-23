/**
 * BehaviorOS — 行为处方 API (修复版)
 *
 * 修复:
 *   1. 使用共享 http 实例 (统一 token/拦截器/错误处理)
 *   2. Token key 与 http.ts 一致 (bos_access_token)
 *   3. 移除独立 axios.create()
 */

import http from '@/api/http'
import type {
  ComputeRxRequest, ComputeRxResponse,
  RxPrescriptionDTO, RxListResponse,
  StrategyTemplateResponse,
  HandoffRequest, HandoffResponse, HandoffListResponse,
  CollaborateRequest, CollaborateResponse,
  AgentStatusResponse,
} from '../types/rx'

// 缓存 (不变)
interface CacheEntry<T> { data: T; expiry: number }
const cache = new Map<string, CacheEntry<any>>()
const CACHE_TTL = 5 * 60 * 1000

function getCached<T>(key: string): T | null {
  const entry = cache.get(key)
  if (entry && Date.now() < entry.expiry) return entry.data as T
  cache.delete(key)
  return null
}
function setCache<T>(key: string, data: T, ttl = CACHE_TTL): void {
  cache.set(key, { data, expiry: Date.now() + ttl })
}
export function clearRxCache(): void { cache.clear() }

// ── API 方法 (改用 http 实例, 路径前缀 /rx) ──

export async function computeRx(req: ComputeRxRequest): Promise<ComputeRxResponse> {
  const { data } = await http.post<ComputeRxResponse>('/v1/rx/compute', req)
  if (data.prescription?.rx_id) setCache(`rx:${data.prescription.rx_id}`, data.prescription)
  return data
}

export async function getRx(rxId: string): Promise<RxPrescriptionDTO> {
  const cached = getCached<RxPrescriptionDTO>(`rx:${rxId}`)
  if (cached) return cached
  const { data } = await http.get<RxPrescriptionDTO>(`/v1/rx/${rxId}`)
  setCache(`rx:${rxId}`, data)
  return data
}

export async function getUserRxHistory(userId: string, page = 1, pageSize = 20): Promise<RxListResponse> {
  const { data } = await http.get<RxListResponse>(`/v1/rx/user/${userId}`, { params: { page, page_size: pageSize } })
  return data
}

export async function getStrategies(stage?: number): Promise<StrategyTemplateResponse> {
  const key = `strategies:${stage ?? 'all'}`
  const cached = getCached<StrategyTemplateResponse>(key)
  if (cached) return cached
  const { data } = await http.get<StrategyTemplateResponse>('/v1/rx/strategies', { params: stage !== undefined ? { stage } : {} })
  setCache(key, data, 15 * 60 * 1000)
  return data
}

export async function initiateHandoff(req: HandoffRequest): Promise<HandoffResponse> {
  const { data } = await http.post<HandoffResponse>('/v1/rx/handoff', req)
  return data
}

export async function getHandoffLog(userId: string, limit = 50): Promise<HandoffListResponse> {
  const { data } = await http.get<HandoffListResponse>(`/v1/rx/handoff/${userId}`, { params: { limit } })
  return data
}

export async function collaborate(req: CollaborateRequest): Promise<CollaborateResponse> {
  const { data } = await http.post<CollaborateResponse>('/v1/rx/collaborate', req)
  return data
}

export async function getAgentStatus(): Promise<AgentStatusResponse> {
  const key = 'agents:status'
  const cached = getCached<AgentStatusResponse>(key)
  if (cached) return cached
  const { data } = await http.get<AgentStatusResponse>('/v1/rx/agents/status')
  setCache(key, data, 30 * 1000)
  return data
}

export const rxApi = {
  computeRx, getRx, getUserRxHistory, getStrategies,
  initiateHandoff, getHandoffLog, collaborate, getAgentStatus,
  clearCache: clearRxCache,
}
export default rxApi
