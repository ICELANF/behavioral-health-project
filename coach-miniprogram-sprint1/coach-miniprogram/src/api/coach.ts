/**
 * 教练工作台 API
 * 对应后端: /api/v1/coach/* + /api/v1/coach-push/* + /api/v1/assessment-assignments/*
 *
 * 注意：类型与 stores/coach.ts 共享，此处复用 store 导出的类型
 */
import http from './request'
import type { Student, DashboardStats, PushQueueItem } from '@/stores/coach'

export type { Student, DashboardStats, PushQueueItem }

// ─── 扩展类型 ─────────────────────────────────────────────────

export interface StudentDetail extends Student {
  email?: string
  phone?: string
  created_at?: string
  bio?: string
  growth_points?: number
  contribution_points?: number
  influence_points?: number
}

export interface HealthSnapshot {
  latest_glucose?: number
  glucose_trend?: 'up' | 'down' | 'stable'
  sleep_score?: number
  sleep_hours?: number
  active_minutes?: number
  heart_rate?: number
  hrv?: number
  updated_at?: string
}

export interface CoachMessage {
  id: number
  content: string
  message_type: string         // advice | encouragement | reminder | warning
  status: 'pending' | 'approved' | 'delivered' | 'read'
  created_at: string
  student_id: number
}

export interface AssessmentAssignment {
  id: number
  student_id: number
  student_name?: string
  student_role?: string
  assessment_id: number
  assessment_title: string
  assessment_type: string
  status: 'assigned' | 'in_progress' | 'submitted' | 'reviewed'
  submitted_at?: string
  reviewed_at?: string
  assigned_at: string
  coach_note?: string
  score?: number
  responses?: AssessmentResponse[]
}

export interface AssessmentResponse {
  question_id: number
  question_text: string
  answer: string | string[]
  answer_label?: string
}

export interface PushHistoryItem extends PushQueueItem {
  reviewed_at?: string
  reject_reason?: string
}

export interface CoachAnalytics {
  total_students: number
  active_students_7d: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  improvement_rate: number
  avg_response_time_hours?: number
  messages_sent_30d: number
  assessments_reviewed_30d: number
}

export interface LiveSession {
  id: number
  title: string
  scheduled_at: string
  duration_minutes: number
  status: 'scheduled' | 'live' | 'ended'
  participant_count?: number
  student_ids?: number[]
}

// ─── 教练 API ─────────────────────────────────────────────────

export const coachApi = {
  /** 工作台统计数据 */
  dashboard() {
    return http.get<DashboardStats>('/v1/coach/dashboard')
  },

  /** 学员列表（四维风险分组） */
  students(params?: { page?: number; page_size?: number; search?: string }) {
    return http.get<{
      risk_priority: { high_risk: Student[]; medium_risk: Student[]; low_risk: Student[] }
      total: number
    }>('/v1/coach/students', params)
  },

  /** 单个学员详情 */
  studentDetail(studentId: number) {
    return http.get<StudentDetail>(`/v1/coach/students/${studentId}`)
  },

  /** 学员健康快照 */
  studentHealth(studentId: number) {
    return http.get<HealthSnapshot>(`/v1/coach/students/${studentId}/health`)
  },

  /** 发送消息给学员（进审批队列） */
  sendMessage(data: { student_id: number; content: string; message_type?: string }) {
    return http.post<CoachMessage>('/v1/coach/messages', {
      message_type: 'advice',
      auto_approve: false,
      ...data
    })
  },

  /** 消息历史 */
  messages(studentId: number, page = 1) {
    return http.get<{ items: CoachMessage[]; total: number }>(
      '/v1/coach/messages',
      { student_id: studentId, page, page_size: 20 }
    )
  },

  /** 数据分析 */
  analytics() {
    return http.get<CoachAnalytics>('/v1/analytics/coach')
  },

  /** 直播会话列表 */
  liveSessions(status?: string) {
    return http.get<LiveSession[]>('/v1/coach/live', { status })
  },

  /** 创建直播会话 */
  createLive(data: { title: string; scheduled_at: string; duration_minutes: number }) {
    return http.post<LiveSession>('/v1/coach/live', data)
  },
}

// ─── 推送审批 API ─────────────────────────────────────────────

export const pushQueueApi = {
  /** 待审批列表 */
  pending(params?: { page?: number; page_size?: number }) {
    return http.get<{ items: PushQueueItem[]; total: number }>('/v1/coach-push/pending', params)
  },

  /** 历史记录（已审批） */
  history(params?: { page?: number; status?: string }) {
    return http.get<{ items: PushHistoryItem[]; total: number }>('/v1/coach-push/history', params)
  },

  /** 审批通过 */
  approve(id: number) {
    return http.post(`/v1/coach-push/${id}/approve`)
  },

  /** 拒绝 */
  reject(id: number, reason?: string) {
    return http.post(`/v1/coach-push/${id}/reject`, { reason })
  },
}

// ─── 评估管理 API ─────────────────────────────────────────────

export const assignmentApi = {
  /** 评估分配列表（教练视角） */
  list(params?: { status?: string; page?: number; page_size?: number }) {
    return http.get<{ items: AssessmentAssignment[]; total: number }>(
      '/v1/assessment-assignments',
      params
    )
  },

  /** 单个评估详情（含学员作答） */
  detail(id: number) {
    return http.get<AssessmentAssignment>(`/v1/assessment-assignments/${id}`)
  },

  /** 提交审核意见 */
  submitReview(id: number, data: { coach_note: string; score?: number; status: 'reviewed' }) {
    return http.put(`/v1/assessment-assignments/${id}/review`, data)
  },

  /** 分配评估给学员 */
  assign(data: { student_id: number; assessment_id: number; due_date?: string }) {
    return http.post<AssessmentAssignment>('/v1/assessment-assignments', data)
  },
}
