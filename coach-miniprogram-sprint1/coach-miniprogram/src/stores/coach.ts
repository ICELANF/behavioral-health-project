/**
 * Coach Store — 教练工作台状态管理（L3+ 专用）
 * 包含: 学员列表 / 待处理数量 / 高风险学员 / 仪表盘统计
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import http from '@/api/request'

// ─── 类型定义 ────────────────────────────────────────────────
export type RiskLevel = 'critical' | 'high' | 'moderate' | 'low' | 'none'
export type TTMStage  = 'S0' | 'S1' | 'S2' | 'S3' | 'S4' | 'S5' | 'S6'

export interface Student {
  id: number
  username: string
  full_name: string
  avatar_url?: string
  role: string
  risk_level: RiskLevel
  ttm_stage: TTMStage
  interaction_status: 'active' | 'needs_attention' | 'dormant'
  last_interaction?: string
  // 健康摘要
  latest_glucose?: number
  glucose_trend?: string
  sleep_score?: number
  active_minutes?: number
}

export interface DashboardStats {
  total_students: number
  high_risk_count: number
  medium_risk_count: number
  pending_queue_count: number       // 待审批推送
  pending_assessment_count: number  // 待审核评估
  active_students_7d: number
  improvement_rate: number          // 风险改善率
}

export interface PushQueueItem {
  id: number
  target_user: { id: number; full_name: string; username: string }
  content_type: string
  content: string
  source_type: string
  status: 'pending' | 'approved' | 'rejected' | 'delivered'
  created_at: string
}

// ─── Store ───────────────────────────────────────────────────
export const useCoachStore = defineStore('coach', () => {
  // State
  const dashboardStats     = ref<DashboardStats | null>(null)
  const students           = ref<Student[]>([])
  const highRiskStudents   = ref<Student[]>([])    // 首页高风险卡片
  const pendingQueue       = ref<PushQueueItem[]>([])
  const loading            = ref(false)
  const lastRefresh        = ref<Date | null>(null)

  // Computed
  const pendingQueueCount = computed(() => dashboardStats.value?.pending_queue_count || 0)
  const pendingAssessmentCount = computed(() => dashboardStats.value?.pending_assessment_count || 0)

  /** TabBar 消息红点总数 */
  const badgeCount = computed(() =>
    pendingQueueCount.value + pendingAssessmentCount.value
  )

  // Actions

  /** 初始化工作台（首页进入时调用，并发请求） */
  async function initDashboard() {
    if (loading.value) return
    loading.value = true
    try {
      const [dash, queue] = await Promise.all([
        http.get<DashboardStats>('/v1/coach/dashboard'),
        http.get<{ items: PushQueueItem[]; total: number }>('/v1/coach-push/pending')
      ])
      dashboardStats.value = {
        ...dash,
        pending_queue_count: queue.total
      }
      // 高风险学员（dashboard 接口已包含）
      if ((dash as any).high_risk_students) {
        highRiskStudents.value = (dash as any).high_risk_students.slice(0, 5)
      }
      pendingQueue.value = queue.items || []
      lastRefresh.value = new Date()
    } catch { /* 静默 */ } finally {
      loading.value = false
    }
  }

  /** 加载学员列表（四维分类） */
  async function loadStudents() {
    const data = await http.get<{
      risk_priority: { high_risk: Student[]; medium_risk: Student[]; low_risk: Student[] }
    }>('/v1/coach/students')
    const { risk_priority } = data
    students.value = [
      ...(risk_priority.high_risk   || []),
      ...(risk_priority.medium_risk || []),
      ...(risk_priority.low_risk    || [])
    ]
    highRiskStudents.value = risk_priority.high_risk?.slice(0, 5) || []
  }

  /** 审批通过推送 */
  async function approvePush(id: number) {
    await http.post(`/v1/coach-push/${id}/approve`)
    // 本地移除该条目
    pendingQueue.value = pendingQueue.value.filter(i => i.id !== id)
    if (dashboardStats.value) {
      dashboardStats.value.pending_queue_count = Math.max(0, dashboardStats.value.pending_queue_count - 1)
    }
  }

  /** 拒绝推送 */
  async function rejectPush(id: number, reason?: string) {
    await http.post(`/v1/coach-push/${id}/reject`, { reason })
    pendingQueue.value = pendingQueue.value.filter(i => i.id !== id)
    if (dashboardStats.value) {
      dashboardStats.value.pending_queue_count = Math.max(0, dashboardStats.value.pending_queue_count - 1)
    }
  }

  /** 发送消息给学员 */
  async function sendMessage(studentId: number, content: string, messageType = 'advice') {
    return http.post('/v1/coach/messages', {
      student_id:   studentId,
      content,
      message_type: messageType,
      auto_approve: false
    })
  }

  /** 轮询：学员侧等待教练审核完成通知（后端 TODO Phase2，前端轮询补偿） */
  async function pollReviewStatus(assignmentId: number): Promise<string> {
    const data = await http.get<{ status: string }>(`/v1/assessment-assignments/${assignmentId}`)
    return data.status
  }

  return {
    dashboardStats, students, highRiskStudents, pendingQueue, loading, lastRefresh,
    pendingQueueCount, pendingAssessmentCount, badgeCount,
    initDashboard, loadStudents, approvePush, rejectPush, sendMessage, pollReviewStatus
  }
})
