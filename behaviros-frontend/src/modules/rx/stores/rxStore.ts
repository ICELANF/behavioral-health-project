/**
 * BehaviorOS — 行为处方 Pinia Store
 * ====================================
 * 全局状态管理: 处方、Agent状态、交接日志、策略模板
 */

import { defineStore } from 'pinia'
import { ref, computed, shallowRef } from 'vue'
import { rxApi } from '../api/rxApi'
import type {
  RxPrescriptionDTO,
  RxContext,
  ComputeRxRequest,
  ComputeRxResponse,
  AgentStatusResponse,
  AgentStatusEntry,
  HandoffLogEntry,
  StrategyTemplate,
  CollaborateResponse,
  ExpertAgentType,
  RxStrategyType,
  RxIntensity,
} from '../types/rx'

export const useRxStore = defineStore('rx', () => {
  // =====================================================================
  // 状态
  // =====================================================================

  // 当前处方
  const currentRx = ref<RxPrescriptionDTO | null>(null)
  const computeResult = ref<ComputeRxResponse | null>(null)
  const rxHistory = ref<RxPrescriptionDTO[]>([])
  const rxHistoryTotal = ref(0)

  // Agent 状态
  const agentStatus = shallowRef<AgentStatusResponse | null>(null)

  // 交接日志
  const handoffLog = ref<HandoffLogEntry[]>([])

  // 策略模板
  const strategies = ref<StrategyTemplate[]>([])

  // 协作结果
  const lastCollaboration = ref<CollaborateResponse | null>(null)

  // 加载状态
  const loading = ref({
    compute: false,
    rx: false,
    history: false,
    agents: false,
    handoff: false,
    strategies: false,
    collaborate: false,
  })

  // 错误
  const error = ref<{ key: string; message: string } | null>(null)

  // =====================================================================
  // 计算属性
  // =====================================================================

  const activeAgents = computed(() => {
    if (!agentStatus.value) return []
    return agentStatus.value.agents.filter((a) => a.status === 'active')
  })

  const orchestratorReady = computed(() => {
    return agentStatus.value?.orchestrator_status === 'ready'
  })

  const totalPrescriptions = computed(() => {
    if (!agentStatus.value) return 0
    return agentStatus.value.agents.reduce((sum, a) => sum + a.total_prescriptions, 0)
  })

  const avgConfidence = computed(() => {
    if (!agentStatus.value || agentStatus.value.agents.length === 0) return 0
    const agents = agentStatus.value.agents.filter((a) => a.total_prescriptions > 0)
    if (agents.length === 0) return 0
    return agents.reduce((sum, a) => sum + a.avg_confidence, 0) / agents.length
  })

  const pendingHandoffs = computed(() => {
    return handoffLog.value.filter(
      (h) => h.status === 'initiated' || h.status === 'in_progress'
    )
  })

  // =====================================================================
  // Actions
  // =====================================================================

  /** 计算行为处方 */
  async function computePrescription(
    context: RxContext,
    options?: {
      agentType?: ExpertAgentType
      forceStrategy?: RxStrategyType
      overrideIntensity?: RxIntensity
    }
  ): Promise<ComputeRxResponse> {
    loading.value.compute = true
    error.value = null

    try {
      const request: ComputeRxRequest = {
        context,
        agent_type: options?.agentType,
        force_strategy: options?.forceStrategy,
        override_intensity: options?.overrideIntensity,
      }
      const result = await rxApi.computeRx(request)
      computeResult.value = result
      currentRx.value = result.prescription
      return result
    } catch (e: any) {
      error.value = { key: 'compute', message: e.message || '计算处方失败' }
      throw e
    } finally {
      loading.value.compute = false
    }
  }

  /** 获取处方详情 */
  async function fetchRx(rxId: string): Promise<RxPrescriptionDTO> {
    loading.value.rx = true
    try {
      const rx = await rxApi.getRx(rxId)
      currentRx.value = rx
      return rx
    } catch (e: any) {
      error.value = { key: 'rx', message: e.message || '获取处方失败' }
      throw e
    } finally {
      loading.value.rx = false
    }
  }

  /** 获取用户处方历史 */
  async function fetchHistory(userId: string, page = 1, pageSize = 20) {
    loading.value.history = true
    try {
      const result = await rxApi.getUserRxHistory(userId, page, pageSize)
      rxHistory.value = result.prescriptions
      rxHistoryTotal.value = result.total
    } catch (e: any) {
      error.value = { key: 'history', message: e.message || '获取历史失败' }
    } finally {
      loading.value.history = false
    }
  }

  /** 获取 Agent 状态 */
  async function fetchAgentStatus() {
    loading.value.agents = true
    try {
      agentStatus.value = await rxApi.getAgentStatus()
    } catch (e: any) {
      error.value = { key: 'agents', message: e.message || '获取Agent状态失败' }
    } finally {
      loading.value.agents = false
    }
  }

  /** 获取交接日志 */
  async function fetchHandoffLog(userId: string) {
    loading.value.handoff = true
    try {
      const result = await rxApi.getHandoffLog(userId)
      handoffLog.value = result.handoffs
    } catch (e: any) {
      error.value = { key: 'handoff', message: e.message || '获取交接日志失败' }
    } finally {
      loading.value.handoff = false
    }
  }

  /** 获取策略模板 */
  async function fetchStrategies(stage?: number) {
    loading.value.strategies = true
    try {
      const result = await rxApi.getStrategies(stage)
      strategies.value = result.strategies
    } catch (e: any) {
      error.value = { key: 'strategies', message: e.message || '获取策略失败' }
    } finally {
      loading.value.strategies = false
    }
  }

  /** 执行协作编排 */
  async function executeCollaboration(
    userId: string,
    userInput: Record<string, any>,
    currentAgent?: ExpertAgentType
  ): Promise<CollaborateResponse> {
    loading.value.collaborate = true
    error.value = null
    try {
      const result = await rxApi.collaborate({
        user_id: userId,
        user_input: userInput,
        current_agent: currentAgent,
      })
      lastCollaboration.value = result
      if (result.combined_prescription) {
        currentRx.value = result.combined_prescription
      }
      return result
    } catch (e: any) {
      error.value = { key: 'collaborate', message: e.message || '协作编排失败' }
      throw e
    } finally {
      loading.value.collaborate = false
    }
  }

  /** 清除当前状态 */
  function resetCurrent() {
    currentRx.value = null
    computeResult.value = null
    lastCollaboration.value = null
    error.value = null
  }

  return {
    // state
    currentRx,
    computeResult,
    rxHistory,
    rxHistoryTotal,
    agentStatus,
    handoffLog,
    strategies,
    lastCollaboration,
    loading,
    error,
    // computed
    activeAgents,
    orchestratorReady,
    totalPrescriptions,
    avgConfidence,
    pendingHandoffs,
    // actions
    computePrescription,
    fetchRx,
    fetchHistory,
    fetchAgentStatus,
    fetchHandoffLog,
    fetchStrategies,
    executeCollaboration,
    resetCurrent,
  }
})
