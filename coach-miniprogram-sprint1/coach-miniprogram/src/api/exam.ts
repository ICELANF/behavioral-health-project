/**
 * 认证考试 API
 * 对应后端: /api/v1/exam/*
 * 与 learning.ts 中的 examApi (随堂测验) 相区分 — 这里是等级晋升认证考试
 */
import http from './request'

// ─── 类型定义 ─────────────────────────────────────────────────

export interface ExamInfo {
  id: number
  title: string
  description?: string
  level_required: string           // 需要的当前等级: L0-L4
  target_level: string             // 通过后目标等级: L1-L5
  pass_score: number               // 及格线 0-100
  time_limit: number               // 分钟
  question_count: number
  status: 'available' | 'locked' | 'passed' | 'cooldown'
  last_score?: number
  pass_date?: string
  cooldown_until?: string          // 冷却期截止时间
  attempt_count?: number           // 已考次数
  rules?: string[]                 // 考试规则
  quiz_id?: number                 // 关联的题库 ID
}

export interface ExamQuestion {
  id: number
  type: 'single' | 'multiple' | 'true_false'
  content: string
  options: { key: string; text: string }[]
  order: number
}

export interface ExamSubmitInput {
  quiz_id: number
  answers: Record<number, string | string[]>
  time_spent_seconds: number
  exam_id?: number
}

export interface ExamSessionResult {
  session_id: number
  exam_id?: number
  score: number
  pass: boolean
  pass_score: number
  points_earned: number
  credits_earned: number
  correct_count: number
  total_count: number
  wrong_ids: number[]
  explanation?: Record<number, string>   // question_id → 解析文本
  promotion_unlocked?: boolean           // 通过后可申请晋级
  time_spent_seconds: number
  completed_at?: string
}

export interface ExamHistoryItem {
  id: number
  exam_id?: number
  exam_title?: string
  score: number
  pass: boolean
  pass_score?: number
  time_spent_seconds?: number
  completed_at: string
}

// ─── API 方法 ─────────────────────────────────────────────────

export const certExamApi = {
  /** 当前用户可参加的认证考试列表 */
  available() {
    return http.get<ExamInfo[]>('/v1/exam/available')
  },

  /** 考试详情（含题库 ID、规则等）*/
  detail(examId: number) {
    return http.get<ExamInfo>(`/v1/exam/${examId}`)
  },

  /** 获取题目列表 */
  getQuestions(quizId: number) {
    return http.get<{ questions: ExamQuestion[]; pass_score: number; time_limit: number }>(
      `/v1/exam/quiz/${quizId}`
    )
  },

  /** 提交答案 → 返回考试结果 */
  submit(data: ExamSubmitInput) {
    return http.post<ExamSessionResult>('/v1/exam/submit', data)
  },

  /** 获取某次会话结果（用于从历史记录查看详情）*/
  sessionResult(sessionId: number) {
    return http.get<ExamSessionResult>(`/v1/exam/sessions/${sessionId}`)
  },

  /** 考试历史 */
  history(page = 1, pageSize = 20) {
    return http.get<{ items: ExamHistoryItem[]; total: number }>(
      '/v1/exam/history', { page, page_size: pageSize }
    )
  }
}
