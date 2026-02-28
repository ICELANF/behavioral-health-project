/**
 * 教练工作台 Store
 * 管理学员列表、Dashboard统计、推送队列
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import http from '@/api/request'

export interface Student {
  id:                  number
  username:            string
  full_name:           string
  avatar_url?:         string
  role:                string
  risk_level?:         string   // critical | high | moderate | low | normal
  last_active_at?:     string
  growth_points:       number
  health_score?:       number
  glucose_latest?:     number
  assigned_at?:        string
}

export interface DashboardStats {
  total_students:      number
  active_students_7d:  number
  high_risk_count:     number
  pending_push_count:  number
  pending_review_count:number
  coach_score?:        number
  coach_level?:        string
}

export interface PushQueueItem {
  id:           number
  student_id:   number
  student_name: string
  content_type: string
  content_title:string
  ai_summary?:  string
  created_at:   string
  priority?:    number
}

export const useCoachStore = defineStore('coach', () => {
  const students           = ref<Student[]>([])
  const highRiskStudents   = ref<Student[]>([])
  const dashboardStats     = ref<DashboardStats | null>(null)
  const pendingQueue       = ref<PushQueueItem[]>([])
  const loading            = ref(false)
  const studentsLoaded     = ref(false)

  // ── Computed ──────────────────────────────────────────
  const totalStudents   = computed(() => dashboardStats.value?.total_students    ?? students.value.length)
  const pendingCount    = computed(() => pendingQueue.value.length)
  const highRiskCount   = computed(() => dashboardStats.value?.high_risk_count   ?? 0)

  // ── Actions ───────────────────────────────────────────
  async function initDashboard() {
    loading.value = true
    try {
      const [dashRes, queueRes] = await Promise.allSettled([
        http.get<any>('/v1/coach/dashboard'),
        http.get<{ items: PushQueueItem[] }>('/v1/coach-push/pending', { page_size: 10 }),
      ])
      if (dashRes.status === 'fulfilled') {
        const res = dashRes.value as any
        const ts = res.today_stats || {}
        const pushCount = queueRes.status === 'fulfilled' ? (queueRes.value.items || []).length : 0
        dashboardStats.value = {
          total_students:      ts.total_students ?? 0,
          active_students_7d:  ts.active_students_7d ?? ts.total_students ?? 0,
          high_risk_count:     ts.alert_students ?? 0,
          pending_push_count:  pushCount,
          pending_review_count:ts.pending_followups ?? 0,
          coach_score:         res.coach?.score,
          coach_level:         res.coach?.level,
        }
      }
      if (queueRes.status === 'fulfilled')  pendingQueue.value  = queueRes.value.items || []
    } finally {
      loading.value = false
    }
  }

  async function loadStudents(params?: { risk_level?: string; search?: string; page?: number }) {
    loading.value = true
    try {
      const res = await http.get<{ items: Student[]; total: number }>(
        '/v1/coach/students',
        { page_size: 50, ...params }
      )
      students.value       = res.items || []
      highRiskStudents.value = students.value.filter(
        s => s.risk_level === 'critical' || s.risk_level === 'high'
      )
      studentsLoaded.value = true
    } catch {
      if (!studentsLoaded.value) students.value = []
    } finally {
      loading.value = false
    }
  }

  async function approvePush(id: number): Promise<boolean> {
    try {
      await http.post(`/v1/coach-push/${id}/approve`, {})
      pendingQueue.value = pendingQueue.value.filter(i => i.id !== id)
      if (dashboardStats.value) dashboardStats.value.pending_push_count--
      return true
    } catch {
      return false
    }
  }

  async function rejectPush(id: number, reason?: string): Promise<boolean> {
    try {
      await http.post(`/v1/coach-push/${id}/reject`, { reason })
      pendingQueue.value = pendingQueue.value.filter(i => i.id !== id)
      if (dashboardStats.value) dashboardStats.value.pending_push_count--
      return true
    } catch {
      return false
    }
  }

  async function sendMessage(data: {
    student_id:   number
    content:      string
    message_type: string
  }): Promise<boolean> {
    try {
      await http.post('/v1/coach/messages', data)
      return true
    } catch {
      return false
    }
  }

  function reset() {
    students.value         = []
    highRiskStudents.value = []
    dashboardStats.value   = null
    pendingQueue.value     = []
    studentsLoaded.value   = false
  }

  return {
    students,
    highRiskStudents,
    dashboardStats,
    pendingQueue,
    loading,
    studentsLoaded,
    totalStudents,
    pendingCount,
    highRiskCount,
    initDashboard,
    loadStudents,
    approvePush,
    rejectPush,
    sendMessage,
    reset,
  }
})
