/**
 * 成长路径 & 晋级 API
 * 对应后端: /api/v1/paths/* + /api/v1/promotion/* + /api/v1/companions/*
 */
import http from './request'

// ─── 等级定义（与后端 paths_api._LEVEL_THRESHOLDS 完全对齐）─────

export const LEVEL_THRESHOLDS: Record<string, LevelRequirement> = {
  L1: { growth: 100,  contribution: 0,    influence: 0,   exam: false, companions: 0, companion_min_level: '' },
  L2: { growth: 500,  contribution: 50,   influence: 0,   exam: false, companions: 0, companion_min_level: '' },
  L3: { growth: 800,  contribution: 200,  influence: 50,  exam: true,  companions: 4, companion_min_level: 'L1' },
  L4: { growth: 1500, contribution: 600,  influence: 200, exam: true,  companions: 4, companion_min_level: 'L2' },
  L5: { growth: 3000, contribution: 1500, influence: 600, exam: true,  companions: 4, companion_min_level: 'L3' },
}

export const LEVEL_META: Record<string, LevelMeta> = {
  L0: { role: 'observer',   label: 'L0 观察员', short: '观察员', icon: '👁',  color: '#8c8c8c', bgColor: '#f5f5f5' },
  L1: { role: 'grower',     label: 'L1 成长者', short: '成长者', icon: '🌱', color: '#52c41a', bgColor: '#f6ffed' },
  L2: { role: 'sharer',     label: 'L2 分享者', short: '分享者', icon: '🌿', color: '#1890ff', bgColor: '#e6f7ff' },
  L3: { role: 'coach',      label: 'L3 教练',   short: '教练',   icon: '🏋️', color: '#722ed1', bgColor: '#f9f0ff' },
  L4: { role: 'promoter',   label: 'L4 促进师', short: '促进师', icon: '🌟', color: '#eb2f96', bgColor: '#fff0f6' },
  L5: { role: 'master',     label: 'L5 大师',   short: '大师',   icon: '🏆', color: '#faad14', bgColor: '#fffbe6' },
}

// ─── 类型定义 ─────────────────────────────────────────────────

export interface LevelRequirement {
  growth: number
  contribution: number
  influence: number
  exam: boolean
  companions: number
  companion_min_level: string
}

export interface LevelMeta {
  role: string
  label: string
  short: string
  icon: string
  color: string
  bgColor: string
}

export interface MyProgress {
  current_level: string                // L0-L5
  next_level: string | null
  growth_points: number
  contribution_points: number
  influence_points: number
  companion_count: number              // 符合条件的同道者数量
  companion_qualified: boolean
  exam_passed: boolean                 // 针对下一级别的考试是否通过
  credits_total: number
  can_apply: boolean
  missing_conditions: string[]         // 描述未满足的条件
}

export interface PromotionEligibility {
  can_apply: boolean
  from_level: string
  to_level: string
  conditions: {
    key: string
    label: string
    required: number | boolean | string
    current: number | boolean | string
    met: boolean
  }[]
  blocking_reason?: string
}

export interface PromotionApplication {
  id: number
  from_level: string
  to_level: string
  status: 'pending' | 'approved' | 'rejected' | 'withdrawn'
  reason?: string
  evidence_url?: string
  submitted_at: string
  reviewed_at?: string
  reviewer_name?: string
  reviewer_note?: string
}

export interface CompanionSummary {
  total: number
  qualified: number          // 符合本次晋级要求的同道者数量
  as_mentee: number          // 我作为学员
  as_mentor: number          // 我作为导师
}

// ─── API 方法 ─────────────────────────────────────────────────

export const pathsApi = {
  /** 获取所有等级定义（含当前用户解锁状态）*/
  levels() {
    return http.get<{ levels: Array<LevelMeta & { requirement: LevelRequirement }> }>('/v1/paths/levels')
  },

  /** 我的成长进度详情 */
  myProgress() {
    return http.get<MyProgress>('/v1/paths/my-progress')
  },
}

export const promotionApi = {
  /** 晋级资格预检 */
  checkEligibility() {
    return http.get<PromotionEligibility>('/v1/promotion/eligibility')
  },

  /** 提交晋级申请 */
  apply(data: { reason?: string; evidence_url?: string }) {
    return http.post<PromotionApplication>('/v1/promotion/apply', data)
  },

  /** 我的晋级申请历史 */
  myHistory(page = 1) {
    return http.get<{ items: PromotionApplication[]; total: number }>(
      '/v1/promotion/my', { page, page_size: 20 }
    )
  },

  /** 撤回申请 */
  withdraw(applicationId: number) {
    return http.post(`/v1/promotion/${applicationId}/withdraw`, {})
  },
}

export const companionApi = {
  /** 同道者汇总 */
  mySummary() {
    return http.get<CompanionSummary>('/v1/companions/my/summary')
  },
}
