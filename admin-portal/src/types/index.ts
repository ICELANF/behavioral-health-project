/**
 * 行为健康平台类型定义
 */

// 导出内容管理类型
export * from './content'

// 风险等级类型
export type RiskLevel = 'high' | 'mid' | 'low' | 'normal'

// 系统等级类型（六级体系·四同道者裂变版）
// L0观察员 → L1成长者 → L2分享者 → L3教练 → L4促进师 → L5大师
export type CoachLevel = 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5'

// 六级体系配置（对应《行为健康教练体系完整建设规划》）
export const LEVEL_CONFIG: Record<CoachLevel, {
  name: string           // 短名称
  title: string          // 正式称号
  subtitle: string       // 核心定位
  color: string
  peers_required: number // 同道者要求数量
  promotion_months: string // 晋级周期
}> = {
  L0: { name: '观察员', title: '观察员', subtitle: '行为入口·认知-行为信号的原始数据源', color: '#8c8c8c', peers_required: 0, promotion_months: '1-3个月' },
  L1: { name: '成长者', title: '成长者', subtitle: '行为养成践行者·效果的唯一承载体', color: '#1890ff', peers_required: 4, promotion_months: '3-6个月' },
  L2: { name: '分享者', title: '分享者', subtitle: '同伴支持者·经验传递与陪伴者', color: '#52c41a', peers_required: 4, promotion_months: '6-12个月' },
  L3: { name: '教练', title: '行为健康教练', subtitle: '系统翻译者·行为改变实施者', color: '#faad14', peers_required: 4, promotion_months: '10-12个月' },
  L4: { name: '促进师', title: '行为健康促进师', subtitle: '系统放大器·组织/区域推动者', color: '#722ed1', peers_required: 4, promotion_months: '12-18个月' },
  L5: { name: '大师', title: '行为健康促进大师', subtitle: '学科文明层·理论范式与传承者', color: '#eb2f96', peers_required: 4, promotion_months: '24个月+' },
}

// TTM 阶段类型
export type TTMStage = 'precontemplation' | 'contemplation' | 'preparation' | 'action' | 'maintenance' | 'termination'

// 触发域类型
export type TriggerDomain = 'glucose' | 'diet' | 'exercise' | 'medication' | 'sleep' | 'stress' | 'weight'

// 用户状态类型
export type UserStatus = 'active' | 'inactive' | 'suspended'

// 用户接口
export interface User {
  user_id: string
  name: string
  phone: string
  email?: string
  avatar?: string
  role: 'admin' | 'expert' | 'coach' | 'student'
  status: UserStatus
  created_at: string
  updated_at: string
}

// 教练接口
export interface Coach {
  coach_id: string
  user_id: string
  name: string
  avatar?: string
  phone: string
  email?: string
  level: CoachLevel
  specialty?: string[]
  student_count: number
  case_count: number
  status: UserStatus
  joined_at: string
  last_active: string
  certifications?: Certification[]
}

// 资质证书接口
export interface Certification {
  cert_id: string
  name: string
  issuer: string
  issue_date: string
  expire_date?: string
  cert_url?: string
}

// 学员接口
export interface Student {
  student_id: string
  name: string
  phone: string
  avatar?: string
  gender?: 'male' | 'female'
  age?: number
  coach_id?: string
  coach_name?: string
  risk_level: RiskLevel
  behavior_stage: TTMStage
  primary_condition?: string
  status: UserStatus
  enrolled_at: string
}

// Prompt 模板接口
export interface PromptTemplate {
  prompt_id: string
  name: string
  description?: string
  category: string
  content: string
  variables?: string[]
  ttm_stage?: TTMStage
  trigger_domain?: TriggerDomain
  is_active: boolean
  created_at: string
  updated_at: string
}

// 触发事件接口
export interface TriggerEvent {
  trigger_id: string
  user_id: string
  trigger_domain: TriggerDomain
  trigger_tag: string
  value: number
  risk_level: RiskLevel
  created_at: string
  handled: boolean
  handled_by?: string
  handled_at?: string
}

// 干预记录接口
export interface Intervention {
  intervention_id: string
  session_id: string
  user_id: string
  coach_id?: string
  type: string
  content: string
  trigger_id?: string
  outcome?: string
  created_at: string
}

// 考试接口
export interface Exam {
  exam_id: string
  title: string
  description?: string
  level: CoachLevel
  duration_minutes: number
  pass_score: number
  total_score: number
  question_count: number
  status: 'draft' | 'published' | 'ongoing' | 'ended'
  start_time?: string
  end_time?: string
  created_at: string
}

// 题目接口
export interface Question {
  question_id: string
  type: 'single' | 'multiple' | 'judge' | 'essay'
  content: string
  options?: QuestionOption[]
  correct_answer: string | string[]
  explanation?: string
  difficulty: number
  score: number
  tags?: string[]
  level?: CoachLevel
  created_at: string
}

// 题目选项接口
export interface QuestionOption {
  key: string
  content: string
}

// 考试结果接口
export interface ExamResult {
  result_id: string
  exam_id: string
  user_id: string
  user_name: string
  score: number
  total_score: number
  pass_score: number
  passed: boolean
  answers: Record<string, string | string[]>
  started_at: string
  submitted_at: string
  duration_seconds: number
}

// 直播接口
export interface LiveSession {
  live_id: string
  title: string
  description?: string
  instructor_id: string
  instructor_name: string
  level: CoachLevel
  cover_url?: string
  scheduled_at: string
  duration_minutes: number
  status: 'scheduled' | 'live' | 'ended' | 'cancelled'
  viewer_count?: number
  replay_url?: string
  created_at: string
}

// 晋级申请接口
export interface PromotionApplication {
  application_id: string
  coach_id: string
  coach_name: string
  current_level: CoachLevel
  target_level: CoachLevel
  applied_at: string
  status: 'pending' | 'approved' | 'rejected'
  requirements_met: {
    courses_completed: boolean
    exams_passed: boolean
    cases_count: boolean
    mentoring_hours: boolean
  }
  materials?: string[]
  reviewer_id?: string
  reviewer_name?: string
  reviewed_at?: string
  review_comment?: string
}

// 课程接口
export interface Course {
  course_id: string
  title: string
  description?: string
  cover_url?: string
  level: CoachLevel
  category: string
  duration_minutes: number
  chapter_count: number
  status: 'draft' | 'published' | 'archived'
  created_at: string
  updated_at: string
}

// 章节接口
export interface Chapter {
  chapter_id: string
  course_id: string
  title: string
  description?: string
  order: number
  duration_minutes: number
  video_url?: string
  content?: string
}

// 分页响应接口
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// API 响应接口
export interface ApiResponse<T = any> {
  code: number
  message: string
  data?: T
}

// 统计数据接口
export interface DashboardStats {
  total_users: number
  total_coaches: number
  total_students: number
  active_sessions: number
  risk_distribution: Record<RiskLevel, number>
  level_distribution: Record<CoachLevel, number>
  stage_distribution: Record<TTMStage, number>
}

// 干预任务接口
export interface InterventionTask {
  task_id: string
  title: string
  description: string
  type: 'education' | 'action' | 'monitoring' | 'communication'
  category: 'behavior_experiment' | 'activation' | 'self_monitoring' | 'skill_training'
  priority: number
  duration_minutes?: number
  resources?: string[]
  behavior_stage?: TTMStage[]
}

// 教练动作接口
export interface CoachAction {
  action_id: string
  title: string
  description: string
  category: 'education' | 'guidance' | 'coaching' | 'support'
  script?: string
  tips?: string[]
  required_level: CoachLevel
  behavior_stage?: TTMStage[]
}

// 干预包接口
export interface InterventionPack {
  pack_id: string
  name: string
  description: string
  trigger_tags: string[]
  applicable_stages: TTMStage[]
  behavior_stage: TTMStage
  risk_levels: RiskLevel[]
  trigger_domain: TriggerDomain
  coach_level_min: CoachLevel
  tasks: InterventionTask[]
  coach_actions: CoachAction[]
  priority: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 触发标签定义
export interface TriggerTag {
  tag: string
  label: string
  domain: TriggerDomain
  threshold?: {
    low?: number
    mid?: number
    high?: number
  }
}
