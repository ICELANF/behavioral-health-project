/**
 * 评估 API（学员视角）
 * 对应后端: /api/v1/assessment-assignments/* + /api/v1/assessments/*
 *
 * 区别于 coach.ts 中的 assignmentApi（教练视角）
 * 此处为学员自己的评估作答流程
 */
import http from './request'

// ─── 类型定义 ─────────────────────────────────────────────────

export type AssignmentStatus = 'assigned' | 'in_progress' | 'submitted' | 'reviewed'
export type QuestionType     = 'single' | 'multiple' | 'scale' | 'text' | 'boolean'
export type AssessmentType   = 'baps' | 'survey' | 'health_check' | 'phq9' | 'gad7' | 'custom'

export interface MyAssignment {
  id: number
  assessment_id: number
  assessment_title: string
  assessment_type: AssessmentType
  description?: string
  status: AssignmentStatus
  assigned_at: string
  due_date?: string
  submitted_at?: string
  reviewed_at?: string
  assigned_by?: string        // 教练姓名
  question_count?: number
  estimated_minutes?: number
}

export interface AssessmentQuestion {
  id: number
  text: string
  type: QuestionType
  options?: { key: string; text: string; score?: number }[]
  scale_min?: number          // scale 题最小值
  scale_max?: number          // scale 题最大值
  scale_step?: number
  scale_labels?: { min: string; max: string }
  required: boolean
  order: number
  hint?: string               // 作答提示
}

export interface AssessmentDef {
  id: number
  title: string
  description?: string
  type: AssessmentType
  questions: AssessmentQuestion[]
  time_limit?: number         // 分钟，0 = 无限制
  instructions?: string
  pass_score?: number
}

export interface QuestionResponse {
  question_id: number
  answer: string | string[] | number
}

export interface AssessmentSubmitInput {
  assignment_id: number
  responses: QuestionResponse[]
  time_spent_seconds?: number
}

export interface AssessmentDimension {
  name: string
  score: number
  max_score: number
  level?: string              // high | moderate | low
  description?: string
}

export interface AssessmentResult {
  assignment_id: number
  assessment_title: string
  assessment_type: AssessmentType
  total_score?: number
  max_score?: number
  category?: string           // 结果分类: high_risk | moderate_risk | low_risk | normal
  category_label?: string     // 中文分类名
  interpretation?: string     // 结果解读
  recommendations?: string[]  // 建议列表
  dimensions?: AssessmentDimension[]
  submitted_at: string
  reviewed_at?: string
  coach_note?: string
}

// ─── API 方法 ─────────────────────────────────────────────────

export const myAssessmentApi = {
  /** 我的评估任务列表 */
  myList(params?: { status?: AssignmentStatus; page?: number; page_size?: number }) {
    return http.get<{ items: MyAssignment[]; total: number }>(
      '/v1/assessment-assignments/my',
      params
    )
  },

  /** 单个评估任务详情 */
  detail(assignmentId: number) {
    return http.get<MyAssignment>(`/v1/assessment-assignments/${assignmentId}`)
  },

  /** 获取评估定义（含题目）*/
  getAssessment(assessmentId: number) {
    return http.get<AssessmentDef>(`/v1/assessments/${assessmentId}`)
  },

  /** 开始作答（更新状态为 in_progress）*/
  start(assignmentId: number) {
    return http.post(`/v1/assessment-assignments/${assignmentId}/start`)
  },

  /** 提交评估答案 */
  submit(data: AssessmentSubmitInput) {
    return http.post<{ result_id: number }>(
      `/v1/assessment-assignments/${data.assignment_id}/submit`,
      { responses: data.responses, time_spent_seconds: data.time_spent_seconds }
    )
  },

  /** 获取评估结果 */
  result(assignmentId: number) {
    return http.get<AssessmentResult>(
      `/v1/assessment-assignments/${assignmentId}/result`
    )
  },
}
