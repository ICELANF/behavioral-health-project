/**
 * BehaviorOS — 行为处方 Composables
 * ====================================
 * 可复用组合逻辑: 轮询、格式化、上下文构建
 */

import { ref, onMounted, onUnmounted, computed, watch, type Ref } from 'vue'
import { useRxStore } from '../stores/rxStore'
import type {
  RxContext,
  BigFiveProfile,
  RxPrescriptionDTO,
  ExpertAgentType,
  RxStrategyType,
} from '../types/rx'
import {
  TTM_STAGES,
  INTENSITY_CONFIG,
  STRATEGY_LABELS,
  AGENT_LABELS,
  RxIntensity,
} from '../types/rx'

// =====================================================================
// useAgentPolling — Agent状态轮询
// =====================================================================

export function useAgentPolling(intervalMs = 30000) {
  const store = useRxStore()
  let timer: ReturnType<typeof setInterval> | null = null

  const start = () => {
    store.fetchAgentStatus()
    timer = setInterval(() => store.fetchAgentStatus(), intervalMs)
  }

  const stop = () => {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  onMounted(start)
  onUnmounted(stop)

  return { start, stop }
}

// =====================================================================
// useRxContextBuilder — 构建三维处方上下文
// =====================================================================

export function useRxContextBuilder(userId: Ref<string>) {
  const ttmStage = ref(1)
  const stageReadiness = ref(0.5)
  const stageStability = ref(0.5)

  const personality = ref<BigFiveProfile>({
    O: 50, C: 50, E: 50, A: 50, N: 50,
  })

  const capacityScore = ref(0.5)
  const selfEfficacy = ref(0.5)

  const domainData = ref<Record<string, any>>({})
  const activeBarriers = ref<string[]>([])
  const recentAdherence = ref(0.5)
  const riskLevel = ref<'low' | 'normal' | 'elevated' | 'high' | 'critical'>('normal')

  const context = computed<RxContext>(() => ({
    user_id: userId.value,
    ttm_stage: ttmStage.value,
    stage_readiness: stageReadiness.value,
    stage_stability: stageStability.value,
    personality: { ...personality.value },
    capacity_score: capacityScore.value,
    self_efficacy: selfEfficacy.value,
    domain_data: { ...domainData.value },
    active_barriers: [...activeBarriers.value],
    recent_adherence: recentAdherence.value,
    risk_level: riskLevel.value,
  }))

  // 快捷方法: 从用户评估数据填充
  function loadFromAssessment(assessment: Record<string, any>) {
    if (assessment.ttm_stage !== undefined) ttmStage.value = assessment.ttm_stage
    if (assessment.stage_readiness !== undefined) stageReadiness.value = assessment.stage_readiness
    if (assessment.big_five) {
      personality.value = { ...personality.value, ...assessment.big_five }
    }
    if (assessment.capacity_score !== undefined) capacityScore.value = assessment.capacity_score
    if (assessment.self_efficacy !== undefined) selfEfficacy.value = assessment.self_efficacy
    if (assessment.barriers) activeBarriers.value = assessment.barriers
    if (assessment.adherence_rate !== undefined) recentAdherence.value = assessment.adherence_rate
    if (assessment.risk_level) riskLevel.value = assessment.risk_level
  }

  // 快捷方法: 重置为默认
  function reset() {
    ttmStage.value = 1
    stageReadiness.value = 0.5
    stageStability.value = 0.5
    personality.value = { O: 50, C: 50, E: 50, A: 50, N: 50 }
    capacityScore.value = 0.5
    selfEfficacy.value = 0.5
    domainData.value = {}
    activeBarriers.value = []
    recentAdherence.value = 0.5
    riskLevel.value = 'normal'
  }

  return {
    // reactive refs
    ttmStage,
    stageReadiness,
    stageStability,
    personality,
    capacityScore,
    selfEfficacy,
    domainData,
    activeBarriers,
    recentAdherence,
    riskLevel,
    // computed
    context,
    // methods
    loadFromAssessment,
    reset,
  }
}

// =====================================================================
// useRxFormatter — 处方数据格式化工具
// =====================================================================

export function useRxFormatter() {
  function formatTTMStage(stage: number) {
    return TTM_STAGES[stage] || TTM_STAGES[0]
  }

  function formatIntensity(intensity: RxIntensity | string) {
    return INTENSITY_CONFIG[intensity as RxIntensity] || INTENSITY_CONFIG[RxIntensity.MODERATE]
  }

  function formatStrategy(strategy: RxStrategyType | string) {
    return STRATEGY_LABELS[strategy as RxStrategyType] || strategy
  }

  function formatAgent(agent: ExpertAgentType | string) {
    return AGENT_LABELS[agent as ExpertAgentType] || { name: agent, icon: '🤖', color: '#999' }
  }

  function formatConfidence(score: number): { label: string; color: string } {
    if (score >= 0.9) return { label: '极高', color: '#52c41a' }
    if (score >= 0.75) return { label: '高', color: '#73d13d' }
    if (score >= 0.6) return { label: '中', color: '#faad14' }
    if (score >= 0.4) return { label: '低', color: '#fa8c16' }
    return { label: '极低', color: '#f5222d' }
  }

  function formatRiskLevel(level: string): { label: string; color: string } {
    const map: Record<string, { label: string; color: string }> = {
      low: { label: '低风险', color: '#52c41a' },
      normal: { label: '正常', color: '#1890ff' },
      elevated: { label: '偏高', color: '#faad14' },
      high: { label: '高风险', color: '#fa541c' },
      critical: { label: '危急', color: '#f5222d' },
    }
    return map[level] || map.normal
  }

  function formatDuration(minutes: number): string {
    if (minutes < 60) return `${minutes}分钟`
    const h = Math.floor(minutes / 60)
    const m = minutes % 60
    return m > 0 ? `${h}小时${m}分钟` : `${h}小时`
  }

  function formatDate(dateStr: string): string {
    const d = new Date(dateStr)
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return {
    formatTTMStage,
    formatIntensity,
    formatStrategy,
    formatAgent,
    formatConfidence,
    formatRiskLevel,
    formatDuration,
    formatDate,
  }
}

// =====================================================================
// useRxHistory — 带分页的处方历史
// =====================================================================

export function useRxHistory(userId: Ref<string>) {
  const store = useRxStore()
  const page = ref(1)
  const pageSize = ref(20)

  async function load() {
    await store.fetchHistory(userId.value, page.value, pageSize.value)
  }

  function nextPage() {
    if (page.value * pageSize.value < store.rxHistoryTotal) {
      page.value++
      load()
    }
  }

  function prevPage() {
    if (page.value > 1) {
      page.value--
      load()
    }
  }

  watch(userId, () => {
    page.value = 1
    load()
  })

  onMounted(load)

  return {
    history: computed(() => store.rxHistory),
    total: computed(() => store.rxHistoryTotal),
    page,
    pageSize,
    loading: computed(() => store.loading.history),
    load,
    nextPage,
    prevPage,
  }
}
