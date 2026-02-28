/**
 * 个人中心 API
 * 对应后端: /api/v1/users/me, /api/v1/auth/change-password,
 *           /api/v1/learning/leaderboard, /api/v1/exam/certifications/*
 */
import http from './request'

// ─── 类型定义 ─────────────────────────────────────────────────

export interface ProfileUpdateInput {
  full_name?: string
  avatar_url?: string
  bio?: string
}

export interface PasswordChangeInput {
  old_password: string
  new_password: string
}

export interface LeaderboardEntry {
  rank: number
  user_id: number
  username: string
  full_name?: string
  role: string
  points: number
  is_me: boolean
}

export interface LeaderboardResp {
  items: LeaderboardEntry[]
  my_rank?: number
  my_points?: number
  total: number
}

export interface CertificationRecord {
  id: number
  level: string          // L1 | L2 | L3 | L4 | L5
  exam_title: string
  passed_at: string
  score: number
  certificate_no?: string
}

export interface PerformanceSummary {
  total_minutes: number
  today_minutes: number
  current_streak: number
  longest_streak: number
  completed_count: number
  growth_points: number
  contribution_points: number
  influence_points: number
  avg_daily_minutes?: number
  this_month_minutes?: number
}

// ─── API 方法 ─────────────────────────────────────────────────

export const profileApi = {
  /** 更新个人资料 */
  updateProfile(data: ProfileUpdateInput) {
    return http.put('/v1/users/me', data)
  },

  /** 修改密码 */
  changePassword(data: PasswordChangeInput) {
    return http.post('/v1/auth/change-password', data)
  },

  /** 积分排行榜 */
  leaderboard(type: 'growth' | 'contribution' | 'influence' = 'growth', page = 1) {
    return http.get<LeaderboardResp>('/v1/learning/leaderboard', { type, page })
  },

  /** 我的认证记录 */
  myCertifications() {
    return http.get<CertificationRecord[]>('/v1/exam/certifications/mine')
  },

  /** 我的绩效数据（等同于 learningApi.myStats 的超集） */
  myPerformance() {
    return http.get<PerformanceSummary>('/v1/users/me/performance')
  },
}
