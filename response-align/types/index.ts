/**
 * BehaviorOS V4.0 — 全局类型定义
 * 镜像后端 core/models.py 和 schemas/
 */

// =====================================================================
// 角色与权限 (Sheet①)
// =====================================================================

export enum UserRole {
  OBSERVER = 'observer',
  GROWER = 'grower',
  SHARER = 'sharer',
  COACH = 'coach',
  PROMOTER = 'promoter',
  MASTER = 'master',
  ADMIN = 'admin',
}

export const ROLE_LEVEL: Record<UserRole, number> = {
  [UserRole.OBSERVER]: 0,
  [UserRole.GROWER]: 1,
  [UserRole.SHARER]: 2,
  [UserRole.COACH]: 3,
  [UserRole.PROMOTER]: 4,
  [UserRole.MASTER]: 5,
  [UserRole.ADMIN]: 6,
}

export const ROLE_LABELS: Record<UserRole, string> = {
  [UserRole.OBSERVER]: '观察员',
  [UserRole.GROWER]: '成长者',
  [UserRole.SHARER]: '分享者',
  [UserRole.COACH]: '教练',
  [UserRole.PROMOTER]: '促进师',
  [UserRole.MASTER]: '大师',
  [UserRole.ADMIN]: '管理员',
}

// =====================================================================
// 旅程阶段 (Sheet②⑧)
// =====================================================================

export enum JourneyStage {
  S0_AUTHORIZATION = 's0_authorization',
  S1_EXPLORATION = 's1_exploration',
  S2_ENGAGEMENT = 's2_engagement',
  S3_PRACTICE = 's3_practice',
  S4_MASTERY = 's4_mastery',
  S5_GRADUATION = 's5_graduation',
}

export const STAGE_LABELS: Record<JourneyStage, string> = {
  [JourneyStage.S0_AUTHORIZATION]: 'S0 授权期',
  [JourneyStage.S1_EXPLORATION]: 'S1 探索期',
  [JourneyStage.S2_ENGAGEMENT]: 'S2 投入期',
  [JourneyStage.S3_PRACTICE]: 'S3 实践期',
  [JourneyStage.S4_MASTERY]: 'S4 精通期',
  [JourneyStage.S5_GRADUATION]: 'S5 毕业期',
}

export const STAGE_COLORS: Record<JourneyStage, string> = {
  [JourneyStage.S0_AUTHORIZATION]: '#94a3b8',
  [JourneyStage.S1_EXPLORATION]: '#7dd3fc',
  [JourneyStage.S2_ENGAGEMENT]: '#6ee7b7',
  [JourneyStage.S3_PRACTICE]: '#60a5fa',
  [JourneyStage.S4_MASTERY]: '#a78bfa',
  [JourneyStage.S5_GRADUATION]: '#fbbf24',
}

// =====================================================================
// 主体性模式 (Sheet②)
// =====================================================================

export enum AgencyMode {
  SCAFFOLDED = 'scaffolded',
  GUIDED = 'guided',
  COLLABORATIVE = 'collaborative',
  AUTONOMOUS = 'autonomous',
}

// =====================================================================
// 用户对象
// =====================================================================

export interface User {
  id: number
  username: string
  email?: string
  role: UserRole
  display_name?: string
  avatar_url?: string
  phone?: string
  agency_mode?: AgencyMode
  journey_stage?: JourneyStage
  trust_score?: number
  agency_score?: number
  is_active: boolean
  created_at: string
}

// =====================================================================
// 认证
// =====================================================================

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  user: User
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  display_name?: string
  phone?: string
  conversion_source?: string
}

// =====================================================================
// API 通用
// =====================================================================

export interface ApiError {
  status: number
  message: string
  detail?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// =====================================================================
// 权限与分段
// =====================================================================

export interface UserPermissions {
  role: UserRole
  features: string[]
  content_levels: number[]
  agent_access: boolean
  max_chat_rounds?: number
  max_challenges?: number
  daily_food_recognition?: number
}

// =====================================================================
// 旅程状态
// =====================================================================

export interface JourneyStatus {
  user_id: number
  journey_stage: JourneyStage
  agency_mode: AgencyMode
  trust_score: number
  agency_score: number
  ies_score?: number
  points_total: number
  dual_track_status: string
  days_in_stage: number
  stage_entered_at: string
}

// =====================================================================
// 积分
// =====================================================================

export interface PointTransaction {
  id: number
  user_id: number
  event_type: string
  points: number
  category: string
  reference_id?: number
  reference_type?: string
  description?: string
  created_at: string
}

// =====================================================================
// 微行动
// =====================================================================

export interface MicroAction {
  id: number
  user_id: number
  title: string
  description?: string
  action_type: string
  status: 'pending' | 'done' | 'attempted' | 'skipped'
  scheduled_at: string
  completed_at?: string
}

// =====================================================================
// 挑战
// =====================================================================

export interface Challenge {
  id: number
  title: string
  description?: string
  duration_days: number
  status: 'draft' | 'active' | 'completed' | 'archived'
  enrolled_count: number
  my_progress?: {
    current_day: number
    checkin_count: number
    completed: boolean
  }
}

// =====================================================================
// 评估
// =====================================================================

export interface AssessmentAssignment {
  id: number
  assessment_type: string
  title: string
  status: 'assigned' | 'in_progress' | 'completed'
  assigned_at: string
  completed_at?: string
}

export interface AssessmentResult {
  id: number
  assessment_type: string
  scores: Record<string, number>
  interpretation?: string
  created_at: string
}
