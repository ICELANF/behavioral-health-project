/**
 * 响应格式归一化 (Response Normalizers)
 * =============================================
 * 后端实际返回 → 前端 types 期望格式
 *
 * 用法: 在 API 层 (index.ts / auth.ts) 调用, 视图层无需关心字段差异
 *
 * 对照清单:
 * ┌──────────────┬────────────────────────┬────────────────────────┐
 * │ 字段          │ 后端返回                │ 前端期望                │
 * ├──────────────┼────────────────────────┼────────────────────────┤
 * │ User         │ full_name              │ display_name           │
 * │              │ intervention_stage     │ journey_stage           │
 * │ Journey      │ current_stage ("S0")   │ journey_stage ("s0_*") │
 * │              │ stage_stability        │ dual_track_status      │
 * │ Learning     │ {learning_time:{...}}  │ {total_minutes,...}    │
 * │ Challenge    │ enrollment_count       │ enrolled_count         │
 * │ Enrollment   │ completed_pushes       │ checkin_count          │
 * │ MicroAction  │ domain, scheduled_date │ action_type, scheduled_at│
 * │ Content      │ level ("L0"), domain   │ content_level (1), category│
 * │ Pagination   │ data / items           │ items                  │
 * └──────────────┴────────────────────────┴────────────────────────┘
 */

import type { User, JourneyStatus, MicroAction, Challenge, PaginatedResponse } from '@/types'

// =====================================================================
// 阶段映射: 后端 "S0" ↔ 前端 "s0_authorization"
// =====================================================================

const STAGE_SHORT_TO_FULL: Record<string, string> = {
  S0: 's0_authorization',
  S1: 's1_exploration',
  S2: 's2_engagement',
  S3: 's3_practice',
  S4: 's4_mastery',
  S5: 's5_graduation',
}

function normalizeStage(raw: string | undefined | null): string {
  if (!raw) return 's0_authorization'
  // 已经是全称
  if (raw.startsWith('s0_') || raw.startsWith('s1_') || raw.startsWith('s2_') ||
      raw.startsWith('s3_') || raw.startsWith('s4_') || raw.startsWith('s5_')) {
    return raw
  }
  // 短码 "S0" → "s0_authorization"
  return STAGE_SHORT_TO_FULL[raw.toUpperCase()] || raw
}

// =====================================================================
// 内容等级映射: "L0"-"L5" → 1-6
// =====================================================================

function parseLevelToNumber(level: string | number | null | undefined): number {
  if (typeof level === 'number') return level
  if (!level) return 1
  const m = String(level).match(/L?(\d)/i)
  return m ? parseInt(m[1]) + 1 : 1
}

// =====================================================================
// 用户归一化
// =====================================================================

export function normalizeUser(raw: any): User {
  if (!raw) return raw
  return {
    id: raw.id,
    username: raw.username,
    email: raw.email,
    role: raw.role,
    display_name: raw.display_name || raw.full_name || raw.username,
    avatar_url: raw.avatar_url || raw.avatar || undefined,
    phone: raw.phone || undefined,
    agency_mode: raw.agency_mode || undefined,
    journey_stage: normalizeStage(raw.journey_stage || raw.intervention_stage || raw.current_stage),
    trust_score: raw.trust_score,
    agency_score: raw.agency_score,
    is_active: raw.is_active ?? true,
    created_at: raw.created_at || '',
  }
}

// =====================================================================
// 旅程状态归一化
// =====================================================================

export function normalizeJourneyStatus(raw: any): JourneyStatus {
  if (!raw) return raw
  return {
    user_id: raw.user_id,
    journey_stage: normalizeStage(
      raw.journey_stage || raw.current_stage || raw.stage
    ),
    agency_mode: raw.agency_mode || raw.interaction_mode || 'scaffolded',
    trust_score: raw.trust_score ?? 0,
    agency_score: raw.agency_score ?? 0,
    ies_score: raw.ies_score ?? raw.ies ?? undefined,
    points_total: raw.points_total ?? raw.total_points ?? 0,
    dual_track_status: raw.dual_track_status || raw.stage_stability || '',
    days_in_stage: raw.days_in_stage ?? raw.days ?? 0,
    stage_entered_at: raw.stage_entered_at || raw.stage_updated_at || '',
  }
}

// =====================================================================
// 学习统计归一化
// =====================================================================

export interface LearningStatsFlat {
  total_minutes: number
  total_hours: number
  today_minutes: number
  week_minutes: number
  completed_count: number       // total_points 映射
  streak_days: number           // current_streak
  longest_streak: number
  quiz_total: number
  quiz_passed: number
  next_time_milestone: any
  next_points_milestone: any
}

export function normalizeLearningStats(raw: any): LearningStatsFlat {
  if (!raw) {
    return {
      total_minutes: 0, total_hours: 0, today_minutes: 0, week_minutes: 0,
      completed_count: 0, streak_days: 0, longest_streak: 0,
      quiz_total: 0, quiz_passed: 0, next_time_milestone: null, next_points_milestone: null,
    }
  }

  // 后端返回嵌套: {learning_time: {total_minutes,...}, learning_points: {total_points,...}, streak: {current_streak,...}}
  // 也兼容平铺格式 (如果后端已变更)
  const lt = raw.learning_time || {}
  const lp = raw.learning_points || {}
  const st = raw.streak || {}
  const qs = lp.quiz_stats || {}

  return {
    total_minutes:        lt.total_minutes    ?? raw.total_minutes    ?? 0,
    total_hours:          lt.total_hours      ?? raw.total_hours      ?? 0,
    today_minutes:        lt.today_minutes    ?? raw.today_minutes    ?? 0,
    week_minutes:         lt.week_minutes     ?? raw.week_minutes     ?? 0,
    completed_count:      lp.total_points     ?? raw.total_points     ?? raw.completed_count ?? 0,
    streak_days:          st.current_streak   ?? raw.current_streak   ?? raw.streak_days ?? 0,
    longest_streak:       st.longest_streak   ?? raw.longest_streak   ?? 0,
    quiz_total:           qs.total_quizzes    ?? raw.quiz_total       ?? 0,
    quiz_passed:          qs.passed_quizzes   ?? raw.quiz_passed      ?? 0,
    next_time_milestone:  lt.next_milestone   ?? raw.next_time_milestone  ?? null,
    next_points_milestone: lp.next_milestone  ?? raw.next_points_milestone ?? null,
  }
}

// =====================================================================
// 挑战归一化 — 列表项 (ChallengeTemplate → Challenge)
// =====================================================================

export function normalizeChallenge(raw: any): Challenge {
  return {
    id: raw.id,
    title: raw.title || '',
    description: raw.description || undefined,
    duration_days: raw.duration_days ?? 0,
    status: normalizeChallengeStatus(raw.status),
    enrolled_count: raw.enrolled_count ?? raw.enrollment_count ?? 0,
    my_progress: raw.my_progress || undefined,
  }
}

function normalizeChallengeStatus(s: string | undefined): Challenge['status'] {
  if (!s) return 'draft'
  const map: Record<string, Challenge['status']> = {
    draft: 'draft', active: 'active', published: 'active',
    completed: 'completed', archived: 'archived', closed: 'archived',
  }
  return map[s.toLowerCase()] || 'draft'
}

// =====================================================================
// 挑战报名归一化 — my-enrollments → 带 my_progress 的 Challenge
// =====================================================================

export function normalizeEnrollment(raw: any): Challenge & { enrollment_id: number; challenge_id: number } {
  // raw 来自 /challenges/my-enrollments, 可能嵌套 challenge 对象
  const ch = raw.challenge || {}
  return {
    id: raw.id,                                  // enrollment.id
    enrollment_id: raw.id,                       // 显式保留
    challenge_id: raw.challenge_id || ch.id,     // 关联的 challenge
    title: ch.title || raw.title || '',
    description: ch.description || raw.description || undefined,
    duration_days: ch.duration_days || raw.duration_days || 0,
    status: normalizeChallengeStatus(ch.status || raw.challenge_status || 'active'),
    enrolled_count: ch.enrollment_count || raw.enrolled_count || 0,
    my_progress: {
      current_day: raw.current_day ?? 0,
      checkin_count: raw.completed_pushes ?? raw.checkin_count ?? 0,
      completed: raw.status === 'completed' || raw.completed_at != null,
    },
  }
}

// =====================================================================
// 微行动归一化
// =====================================================================

export function normalizeMicroAction(raw: any): MicroAction {
  return {
    id: raw.id,
    user_id: raw.user_id,
    title: raw.title || '',
    description: raw.description || undefined,
    action_type: raw.action_type || raw.domain || 'general',
    status: raw.status || 'pending',
    scheduled_at: raw.scheduled_at || raw.scheduled_date || '',
    completed_at: raw.completed_at || undefined,
  }
}

// =====================================================================
// 内容项归一化
// =====================================================================

export function normalizeContentItem(raw: any): any {
  return {
    ...raw,
    content_level: parseLevelToNumber(raw.level || raw.content_level),
    category: raw.category || raw.domain || raw.content_type || '通用',
    duration_minutes: raw.duration_minutes ?? undefined,
    completed: raw.completed ?? false,
  }
}

// =====================================================================
// 分页归一化 — 兼容 {items, total} / {data, total} / 纯数组
// =====================================================================

export function normalizePaginated<T>(
  raw: any,
  itemNormalizer?: (item: any) => T
): PaginatedResponse<T> {
  // 如果是纯数组
  if (Array.isArray(raw)) {
    const items = itemNormalizer ? raw.map(itemNormalizer) : raw
    return { items, total: items.length, page: 1, page_size: items.length }
  }

  // 对象形式
  const rawItems = raw.items || raw.data || raw.results || []
  const items = itemNormalizer ? rawItems.map(itemNormalizer) : rawItems

  return {
    items,
    total: raw.total ?? raw.count ?? items.length,
    page: raw.page ?? raw.current_page ?? 1,
    page_size: raw.page_size ?? raw.per_page ?? raw.limit ?? items.length,
  }
}

// =====================================================================
// 积分余额归一化
// =====================================================================

export function normalizeCreditsBalance(raw: any): { total: number; growth: number; contribution: number; influence: number } {
  if (!raw) return { total: 0, growth: 0, contribution: 0, influence: 0 }
  return {
    total: raw.total ?? raw.total_points ?? raw.balance ?? 0,
    growth: raw.growth ?? raw.growth_points ?? 0,
    contribution: raw.contribution ?? raw.contribution_points ?? 0,
    influence: raw.influence ?? raw.influence_points ?? 0,
  }
}

// =====================================================================
// 数组归一化辅助
// =====================================================================

export function normalizeArray<T>(raw: any, normalizer: (item: any) => T): T[] {
  if (!raw) return []
  const arr = Array.isArray(raw) ? raw : (raw.items || raw.data || raw.results || [])
  return arr.map(normalizer)
}
