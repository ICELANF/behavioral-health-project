/**
 * 同道者关系 API
 * 对应后端: /api/v1/companions/*
 *
 * 关系语义：
 *   mentor（导师）— 带教我的人（我是 mentee）
 *   mentee（学员）— 我带教的人（我是 mentor）
 * 邀请模型：由 mentor 主动邀请，直接建立关系（无审批流）
 */
import http from './request'

// ─── 类型定义 ─────────────────────────────────────────────────

export type CompanionStatus = 'active' | 'graduated' | 'withdrawn'

export interface MenteeRelation {
  id: number
  mentee_id: number
  mentee_name?: string
  mentee_role?: string
  mentee_level?: number
  status: CompanionStatus
  quality_score?: number
  created_at: string
  graduated_at?: string
}

export interface MentorRelation {
  id: number
  mentor_id: number
  mentor_name?: string
  mentor_role?: string
  mentor_level?: number
  status: CompanionStatus
  created_at: string
}

export interface CompanionStats {
  graduated_count: number
  active_count: number
  avg_quality?: number
  as_mentor_count?: number     // 我作为导师带教的数量
  as_mentee_count?: number     // 我作为学员被带教的数量
  qualified_count?: number     // 符合下次晋级要求的同道者数量
}

export interface MatchSuggestion {
  user_id: number
  username: string
  full_name?: string
  role: string
  role_level: number
  growth_points: number
  match_score?: number         // 0-100 匹配度
  match_reason?: string
  is_companion: boolean        // 已经是同道者
}

export interface CompanionDashboard {
  total_mentees: number
  active_mentees: number
  graduated_mentees: number
  avg_quality: number
  recent_interactions: number
  mentees: MenteeRelation[]
}

// ─── API 方法 ─────────────────────────────────────────────────

export const companionApi = {
  /** 我带教的学员列表 */
  myMentees(params?: { status?: CompanionStatus; page?: number; page_size?: number }) {
    return http.get<MenteeRelation[]>('/v1/companions/my-mentees', params)
  },

  /** 指导我的导师列表 */
  myMentors() {
    return http.get<MentorRelation[]>('/v1/companions/my-mentors')
  },

  /** 统计数据 */
  stats() {
    return http.get<CompanionStats>('/v1/companions/stats')
  },

  /** 同道者仪表盘 */
  dashboard() {
    return http.get<CompanionDashboard>('/v1/companions/dashboard')
  },

  /** 邀请某人成为我的学员 */
  invite(menteeId: number) {
    return http.post('/v1/companions/invite', null, { params: { mentee_id: menteeId } } as any)
  },

  /** 让学员毕业 */
  graduate(relationId: number, qualityScore?: number) {
    return http.put(`/v1/companions/${relationId}/graduate`, { quality_score: qualityScore })
  },

  /** 记录同道互动 */
  recordInteraction(companionId: number, interactionType: string, qualityScore?: number) {
    return http.post(`/v1/companions/${companionId}/interact`, {
      interaction_type: interactionType,
      quality_score: qualityScore
    })
  },

  /** 智能匹配推荐 */
  matchSuggestions() {
    return http.get<MatchSuggestion[]>('/v1/companions/match')
  },
}
