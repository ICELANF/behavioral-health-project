/**
 * Agent Store - Agent状态管理
 * 管理Agent建议、审核、反馈
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api/request'

/**
 * Agent建议
 */
export interface AgentSuggestion {
  id: string
  type: 'action' | 'task' | 'alert' | 'content' | 'resource'
  priority: number
  text: string
  rationale?: string
  evidence?: string[]
  action_url?: string
  expires_at?: string
}

/**
 * Agent输出
 */
export interface AgentOutput {
  task_id: string
  agent_id: string
  agent_type: string
  output_type: string
  confidence: number
  suggestions: AgentSuggestion[]
  risk_flags: string[]
  need_human_review: boolean
  review_reason?: string
  metadata: {
    processing_time_ms: number
    model_version: string
  }
  created_at: string
}

/**
 * 待审核项
 */
export interface PendingReview {
  execution_id: string
  task_id: string
  agent_id: string
  status: string
  input_snapshot: any
  output_snapshot: AgentOutput
  started_at: string
}

/**
 * Agent注册信息
 */
export interface AgentInfo {
  agent_id: string
  agent_type: string
  name: string
  description: string
  version: string
  status: string
}

export const useAgentStore = defineStore('agent', () => {
  // 状态
  const agents = ref<AgentInfo[]>([])
  const pendingReviews = ref<PendingReview[]>([])
  const currentOutput = ref<AgentOutput | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const pendingCount = computed(() => pendingReviews.value.length)
  const hasUrgentAlerts = computed(() =>
    pendingReviews.value.some(r =>
      r.output_snapshot.risk_flags.length > 0 ||
      r.output_snapshot.suggestions.some(s => s.priority >= 9)
    )
  )

  /**
   * 加载Agent列表
   */
  const loadAgents = async (): Promise<void> => {
    try {
      const res = await request.get('v1/agent/list')
      const data = res.data as { success: boolean; data: AgentInfo[] }
      if (data.success) {
        agents.value = data.data
      }
    } catch (err) {
      error.value = String(err)
    }
  }

  /**
   * 运行Agent任务
   */
  const runAgent = async (params: {
    agent_type: string
    user_id: string
    context: any
    expected_output: string
    priority?: string
    coach_id?: string
  }): Promise<AgentOutput | null> => {
    loading.value = true
    error.value = null

    try {
      const res = await request.post('v1/agent/run', params)
      const data = res.data as { success: boolean; data: AgentOutput }
      if (data.success) {
        currentOutput.value = data.data
        return data.data
      }
      return null
    } catch (err) {
      error.value = String(err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载待审核任务
   */
  const loadPendingReviews = async (): Promise<void> => {
    try {
      const res = await request.get('v1/agent/pending-reviews')
      const data = res.data as { success: boolean; data: PendingReview[] }
      if (data.success) {
        pendingReviews.value = data.data
      }
    } catch (err) {
      error.value = String(err)
    }
  }

  /**
   * 提交反馈
   */
  const submitFeedback = async (params: {
    task_id: string
    reviewer_id: string
    reviewer_role: string
    feedback_type: 'accept' | 'reject' | 'modify' | 'rate'
    rating?: number
    comment?: string
    modifications?: { original: any; modified: any }
  }): Promise<boolean> => {
    try {
      const res = await request.post('v1/agent/feedback', params)
      const data = res.data as { success: boolean }
      if (data.success) {
        // 移除已审核的项
        pendingReviews.value = pendingReviews.value.filter(r => r.task_id !== params.task_id)
        return true
      }
      return false
    } catch (err) {
      error.value = String(err)
      return false
    }
  }

  /**
   * 获取Agent统计
   */
  const getAgentStats = async (agentId: string): Promise<any> => {
    try {
      const res = await request.get(`v1/agent/stats/${agentId}`)
      const data = res.data as { success: boolean; data: any }
      if (data.success) {
        return data.data
      }
      return null
    } catch (err) {
      error.value = String(err)
      return null
    }
  }

  /**
   * 获取执行历史
   */
  const getHistory = async (params?: {
    agent_id?: string
    user_id?: string
    status?: string
    limit?: number
  }): Promise<any[]> => {
    try {
      const query = new URLSearchParams()
      if (params?.agent_id) query.set('agent_id', params.agent_id)
      if (params?.user_id) query.set('user_id', params.user_id)
      if (params?.status) query.set('status', params.status)
      if (params?.limit) query.set('limit', String(params.limit))

      const res = await request.get(`v1/agent/history?${query.toString()}`)
      const data = res.data as { success: boolean; data: any[] }
      if (data.success) {
        return data.data
      }
      return []
    } catch (err) {
      error.value = String(err)
      return []
    }
  }

  return {
    // 状态
    agents,
    pendingReviews,
    currentOutput,
    loading,
    error,

    // 计算属性
    pendingCount,
    hasUrgentAlerts,

    // 方法
    loadAgents,
    runAgent,
    loadPendingReviews,
    submitFeedback,
    getAgentStats,
    getHistory
  }
})
