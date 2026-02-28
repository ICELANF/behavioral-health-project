/**
 * 学习中心 API
 * 对应后端: /api/v1/content/* + /api/v1/learning/* + /api/v1/credits/* + /api/v1/exam/*
 */
import http from './request'

// ─── 内容相关 ─────────────────────────────────────────────────

export interface ContentItem {
  id: number
  title: string
  content_type: string          // article | video | course | audio | card | case_share
  cover_url?: string
  domain?: string
  level?: string                // L0-L5 等级门控
  has_quiz?: boolean
  view_count?: number
  author_name?: string
  duration?: number             // 视频/音频秒数
  word_count?: number           // 图文字数
  status?: string
  progress_percent?: number
  tags?: string[]
  summary?: string
  module?: string               // M1-M4
}

export interface ContentDetail extends ContentItem {
  body?: string                 // 图文正文 Markdown/HTML
  media_url?: string            // 视频/音频 URL
  chapters?: ChapterItem[]      // course 类型
  quiz_id?: number
}

export interface ChapterItem {
  id: number
  title: string
  duration?: number
  media_url?: string
  content_type: string
  order: number
  completed?: boolean
}

export interface ContentListResp {
  items: ContentItem[]
  total: number
  page: number
  page_size: number
}

export interface LearningProgressInput {
  content_id: number
  progress_percent: number
  last_position?: string        // 视频秒数字符串
  time_spent_seconds?: number
  status?: 'in_progress' | 'completed'
}

export interface LearningStats {
  total_minutes: number
  today_minutes: number
  current_streak: number
  longest_streak: number
  total_points: number
  growth_points: number
  contribution_points: number
  influence_points: number
  completed_count: number
  in_progress_count: number
}

export interface PointsRecord {
  id: number
  points: number
  source: string
  description?: string
  created_at: string
}

export interface CreditSummary {
  total: number
  m1: number
  m2: number
  m3: number
  m4: number
  elective: number
  required_total?: number
}

export interface CreditRecord {
  id: number
  module_type: string           // m1 | m2 | m3 | m4 | elective
  credits: number
  source: string
  description: string
  created_at: string
}

// ─── 测验相关 ─────────────────────────────────────────────────

export interface QuizQuestion {
  id: number
  type: 'single' | 'multiple' | 'true_false'
  content: string
  options: { key: string; text: string }[]
  order: number
}

export interface Quiz {
  id: number
  title: string
  questions: QuizQuestion[]
  pass_score: number            // 0-100
  time_limit?: number           // 分钟
}

export interface QuizSubmitInput {
  quiz_id: number
  answers: Record<number, string | string[]>  // question_id → 答案
  time_spent_seconds: number
}

export interface QuizResult {
  session_id: number
  score: number
  pass: boolean
  pass_score: number
  points_earned: number
  credits_earned: number
  correct_count: number
  total_count: number
  wrong_ids: number[]           // 答错的题目 ID
  explanation?: Record<number, string>  // 解析
}

// ─── API 方法 ─────────────────────────────────────────────────

export const contentApi = {
  /** 内容列表（支持分页、类型过滤、领域过滤、模块过滤）*/
  list(params?: {
    page?: number; page_size?: number
    content_type?: string; domain?: string
    module?: string; status?: string
    search?: string; level?: string
  }) {
    return http.get<ContentListResp>('/v1/content', params)
  },

  /** 推荐内容 */
  recommended(limit = 6) {
    return http.get<{ items: ContentItem[] }>('/v1/content/recommended', { limit })
  },

  /** 内容详情 */
  detail(id: number) {
    return http.get<ContentDetail>(`/v1/content/${id}`)
  },

  /** 保存学习进度（视频心跳/完成）*/
  saveProgress(data: LearningProgressInput) {
    return http.post('/v1/content/user/learning-progress', data)
  },

  /** 查询进度 */
  getProgress(contentId: number) {
    return http.get<{ progress_percent: number; last_position?: string }>(
      `/v1/content/user/learning-progress/${contentId}`
    )
  },

  /** 进行中的内容 */
  inProgress() {
    return http.get<ContentItem[]>('/v1/content/user/in-progress')
  },
}

export const learningApi = {
  /** 我的学习统计 */
  myStats() {
    return http.get<LearningStats>('/v1/learning/my-stats')
  },

  /** 积分明细 */
  pointsHistory(page = 1, pageSize = 20) {
    return http.get<{ items: PointsRecord[]; total: number }>('/v1/learning/points-history', {
      page, page_size: pageSize
    })
  },

  /** 完成课程模块（学分+积分联动）*/
  completeModule(moduleId: string, evidenceType = 'attendance', score?: number) {
    return http.post<{ credits_earned: number; points_earned: number }>(
      '/v1/learning/complete',
      { module_id: moduleId, evidence_type: evidenceType, score }
    )
  },

  /** 学习时间记录 */
  timeHistory(params?: { page?: number; page_size?: number }) {
    return http.get('/v1/learning/time-history', params)
  }
}

export const creditsApi = {
  /** 学分汇总 */
  mySummary() {
    return http.get<CreditSummary>('/v1/credits/my')
  },

  /** 学分记录 */
  myRecords(page = 1, pageSize = 20) {
    return http.get<{ items: CreditRecord[]; total: number }>('/v1/credits/records', {
      page, page_size: pageSize
    })
  }
}

export const examApi = {
  /** 获取测验（通过 quiz_id）*/
  getQuiz(quizId: number) {
    return http.get<Quiz>(`/v1/exam/quiz/${quizId}`)
  },

  /** 提交测验答案 */
  submit(data: QuizSubmitInput) {
    return http.post<QuizResult>('/v1/exam/submit', data)
  },

  /** 考试历史 */
  history(page = 1) {
    return http.get('/v1/exam/history', { page })
  }
}
