/**
 * 用户相关类型
 */
export interface User {
  id: number
  username: string
  email: string
  role: 'patient' | 'coach' | 'admin'
  full_name?: string
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

/**
 * 评估相关类型
 */
export interface AssessmentInput {
  user_id: number
  text_content?: string
  glucose_values?: number[]
  hrv_values?: number[]
  activity_data?: ActivityData
  sleep_data?: SleepData
}

export interface ActivityData {
  steps: number
  distance?: number
  calories?: number
}

export interface SleepData {
  duration: number
  quality: number
}

export interface Trigger {
  tag_id: string
  name: string
  category: 'physiological' | 'psychological' | 'behavioral' | 'environmental'
  severity: 'low' | 'moderate' | 'high' | 'critical'
  confidence: number
  source: string
  metadata: Record<string, any>
}

export interface RiskAssessment {
  risk_level: 'R0' | 'R1' | 'R2' | 'R3' | 'R4'
  risk_score: number
  contributing_triggers: Trigger[]
  severity_distribution: {
    critical: number
    high: number
    moderate: number
    low: number
  }
  primary_concern: string
  urgency: 'low' | 'medium' | 'high' | 'critical'
  reasoning: string
}

export interface RoutingDecision {
  primary_agent: string
  secondary_agents: string[]
  priority: number
  response_time: string
  routing_reasoning: string
  recommended_actions: string[]
}

export interface AssessmentResult {
  assessment_id: string
  user_id: number
  triggers: Trigger[]
  risk_assessment: RiskAssessment
  routing_decision: RoutingDecision
  timestamp: string
  context: Record<string, any>
}

/**
 * API响应类型
 */
export interface ApiResponse<T = any> {
  code?: number
  message?: string
  data?: T
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
