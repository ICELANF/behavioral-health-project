/**
 * 内容管理扩展类型定义
 *
 * 扩展现有 Course 体系，支持：
 * - 多来源内容（平台、专家、教练、用户分享）
 * - UGC审核流程
 * - 更多内容类型（文章、卡片、案例分享）
 */

import type { CoachLevel, TTMStage, TriggerDomain } from './index'

// ==================== 内容来源与类型 ====================

/** 内容来源 */
export type ContentSource =
  | 'platform'      // 平台官方
  | 'expert'        // 专家/大师 (L4)
  | 'coach'         // 教练 (L2-L3)
  | 'sharer'        // 分享者 (用户UGC)
  | 'ai_generated'  // AI辅助生成
  | 'external'      // 外部合作方

/** 扩展内容类型（兼容原有 course） */
export type ContentType =
  | 'course'        // 系统课程（章节式，已有）
  | 'video'         // 单个视频
  | 'article'       // 图文文章
  | 'audio'         // 音频（正念等）
  | 'card'          // 练习卡片
  | 'live'          // 直播（已有 LiveSession）
  | 'case_share'    // 案例分享
  | 'tool'          // 工具/量表

/** 内容状态（扩展原有） */
export type ContentStatus =
  | 'draft'         // 草稿
  | 'pending'       // 待审核（新增）
  | 'revision'      // 待修改（新增）
  | 'published'     // 已发布
  | 'offline'       // 已下架
  | 'archived'      // 已归档

/** 可见范围 */
export type ContentVisibility =
  | 'public'        // 公开
  | 'registered'    // 注册用户
  | 'level_required'// 等级限制
  | 'paid'          // 付费内容
  | 'activity'      // 活动专属

// ==================== 扩展课程接口 ====================

/** 扩展课程接口（兼容原 Course） */
export interface CourseExtended {
  // 原有字段
  course_id: string
  title: string
  description?: string
  cover_url?: string
  level: CoachLevel
  category: CourseCategory
  duration_minutes: number
  chapter_count: number
  status: ContentStatus
  created_at: string
  updated_at: string

  // 新增字段
  source: ContentSource            // 内容来源
  author_id: string                // 作者ID
  author_name: string              // 作者名称
  author_title?: string            // 作者头衔
  author_verified: boolean         // 是否认证

  // 分类扩展
  domain?: TriggerDomain           // 关联领域
  tags: string[]                   // 标签
  target_stages?: TTMStage[]       // 目标行为阶段

  // 可见性
  visibility: ContentVisibility
  required_level?: CoachLevel      // 最低等级要求
  price?: number                   // 价格（0为免费）

  // 统计
  view_count: number
  like_count: number
  collect_count: number
  enroll_count: number
  complete_count: number
  avg_rating?: number
  rating_count?: number

  // 审核
  review_status?: ReviewStatus
  reviewed_by?: string
  reviewed_at?: string

  // 关联
  related_activities?: string[]    // 关联活动
  prerequisites?: string[]         // 前置课程
}

/** 课程分类（扩展） */
export type CourseCategory =
  | 'knowledge'     // 知识体系
  | 'method'        // 方法体系
  | 'skill'         // 核心技能
  | 'value'         // 观念心智
  | 'practice'      // 实践练习（新增）
  | 'case'          // 案例学习（新增）

// ==================== 文章内容 ====================

/** 文章内容 */
export interface ArticleContent {
  article_id: string
  type: 'article'
  source: ContentSource
  status: ContentStatus

  // 基本信息
  title: string
  summary: string                  // 摘要（200字内）
  cover_url?: string
  content_html: string             // HTML正文
  word_count: number
  read_time: number                // 预计阅读分钟

  // 分类
  domain: TriggerDomain
  tags: string[]
  level: 'beginner' | 'intermediate' | 'advanced'
  target_stages?: TTMStage[]

  // 作者
  author_id: string
  author_name: string
  author_avatar?: string
  author_title?: string
  author_verified: boolean

  // 可见性
  visibility: ContentVisibility
  required_level?: CoachLevel

  // 统计
  view_count: number
  like_count: number
  collect_count: number
  comment_count: number
  share_count: number

  // 审核
  review_status?: ReviewStatus
  reviewed_by?: string
  reviewed_at?: string

  // 时间
  created_at: string
  updated_at: string
  published_at?: string
}

// ==================== 练习卡片 ====================

/** 练习卡片 */
export interface PracticeCard {
  card_id: string
  type: 'card'
  source: ContentSource
  status: ContentStatus

  // 基本信息
  title: string
  description: string
  icon: string
  cover_color: string              // 渐变背景色

  // 练习信息
  domain: TriggerDomain
  practice_type: 'daily' | 'situational' | 'weekly'
  estimated_minutes: number
  difficulty: 1 | 2 | 3            // 难度星级

  // 步骤
  steps: PracticeStep[]
  tips?: string[]

  // 作者
  author_id: string
  author_name: string

  // 可见性
  visibility: ContentVisibility
  target_stages?: TTMStage[]

  // 统计
  use_count: number
  complete_count: number
  like_count: number

  // 审核
  review_status?: ReviewStatus

  created_at: string
  updated_at: string
}

/** 练习步骤 */
export interface PracticeStep {
  order: number
  instruction: string
  duration_seconds?: number
  media_url?: string
  interaction?: 'read' | 'timer' | 'input' | 'breathe'
}

// ==================== 案例分享 (UGC) ====================

/** 案例分享 */
export interface CaseShare {
  case_id: string
  type: 'case_share'
  source: 'sharer' | 'coach' | 'expert'
  status: ContentStatus

  // 内容
  title: string
  domain: TriggerDomain
  challenge: string                // 遇到的问题
  approach: string                 // 采取的方法
  outcome: string                  // 结果收获
  reflection?: string              // 心得反思

  // 匿名设置
  is_anonymous: boolean
  display_name: string             // 显示名称

  // 作者
  author_id: string
  author_role: string              // 作者角色
  behavior_stage?: TTMStage        // 作者当前阶段

  // 互动
  allow_comments: boolean
  comment_count: number
  like_count: number
  helpful_count: number            // "有帮助"数

  // 审核（UGC必须审核）
  review_status: ReviewStatus
  reviewed_by?: string
  reviewed_at?: string
  review_comment?: string

  created_at: string
  published_at?: string
}

// ==================== 音频内容 ====================

/** 音频内容（正念、播客等） */
export interface AudioContent {
  audio_id: string
  type: 'audio'
  source: ContentSource
  status: ContentStatus

  // 基本信息
  title: string
  description: string
  cover_url?: string
  audio_url: string
  duration_seconds: number

  // 分类
  domain: TriggerDomain
  audio_category: 'mindfulness' | 'relaxation' | 'sleep' | 'podcast' | 'guide'
  tags: string[]

  // 正念音频特有
  voice_type?: 'male' | 'female'
  has_bgm?: boolean
  practice_type?: string

  // 作者
  author_id: string
  author_name: string
  author_title?: string

  // 统计
  play_count: number
  complete_count: number
  like_count: number
  collect_count: number

  // 审核
  review_status?: ReviewStatus

  created_at: string
  updated_at: string
}

// ==================== 审核系统 ====================

/** 审核状态 */
export type ReviewStatus =
  | 'pending'       // 待审核
  | 'in_review'     // 审核中
  | 'approved'      // 通过
  | 'rejected'      // 拒绝
  | 'revision'      // 需修改

/** 审核记录 */
export interface ContentReview {
  review_id: string
  content_id: string
  content_type: ContentType
  content_title: string
  content_source: ContentSource
  author_id: string
  author_name: string

  // 审核信息
  reviewer_id: string
  reviewer_name: string
  review_time: string
  decision: ReviewStatus
  comments: string
  revision_notes?: string          // 修改建议

  // 检查项
  checklist: ReviewChecklist

  // 二级审核（高风险内容）
  requires_senior?: boolean
  senior_reviewer_id?: string
  senior_decision?: ReviewStatus
}

/** 审核检查清单 */
export interface ReviewChecklist {
  content_accurate: boolean        // 内容准确
  no_medical_claims: boolean       // 无医学诊断声称
  no_sensitive: boolean            // 无敏感内容
  quality_ok: boolean              // 质量达标
  copyright_clear: boolean         // 版权无问题
  privacy_protected: boolean       // 隐私保护
}

/** 审核队列项 */
export interface ReviewQueueItem {
  content_id: string
  content_type: ContentType
  content_title: string
  source: ContentSource
  author_name: string
  submitted_at: string
  priority: 'high' | 'normal' | 'low'
  assigned_to?: string
  domain?: TriggerDomain
}

// ==================== 内容统一查询 ====================

/** 内容列表查询参数 */
export interface ContentListQuery {
  page?: number
  page_size?: number
  type?: ContentType
  source?: ContentSource
  status?: ContentStatus
  domain?: TriggerDomain
  level?: CoachLevel
  keyword?: string
  author_id?: string
  sort_by?: 'created_at' | 'view_count' | 'like_count' | 'rating'
  sort_order?: 'asc' | 'desc'
}

/** 内容摘要（列表展示用） */
export interface ContentSummary {
  id: string
  type: ContentType
  source: ContentSource
  status: ContentStatus
  title: string
  cover_url?: string
  icon?: string
  author_name: string
  author_verified: boolean
  domain?: TriggerDomain
  view_count: number
  like_count: number
  created_at: string
  review_status?: ReviewStatus
}

// ==================== 学习进度 ====================

/** 用户内容学习记录 */
export interface UserContentProgress {
  user_id: string
  content_id: string
  content_type: ContentType

  status: 'not_started' | 'in_progress' | 'completed'
  progress_percent: number
  last_position?: number           // 视频/音频播放位置
  last_chapter_id?: string         // 课程当前章节

  started_at?: string
  completed_at?: string
  last_accessed_at: string
  total_time_seconds: number       // 累计学习时长

  // 互动
  rating?: number
  review?: string
  notes?: string
}

// ==================== 配置常量 ====================

/** 内容来源配置 */
export const CONTENT_SOURCE_CONFIG: Record<ContentSource, {
  label: string
  badge: string
  color: string
  trustLevel: number
  requiresReview: boolean
}> = {
  platform: { label: '官方', badge: '官方', color: '#1890ff', trustLevel: 5, requiresReview: false },
  expert: { label: '专家', badge: '专家', color: '#722ed1', trustLevel: 4, requiresReview: false },
  coach: { label: '教练', badge: '教练', color: '#52c41a', trustLevel: 3, requiresReview: true },
  sharer: { label: '用户分享', badge: 'UGC', color: '#faad14', trustLevel: 2, requiresReview: true },
  ai_generated: { label: 'AI生成', badge: 'AI', color: '#13c2c2', trustLevel: 2, requiresReview: true },
  external: { label: '合作方', badge: '合作', color: '#8c8c8c', trustLevel: 3, requiresReview: true },
}

/** 内容类型配置 */
export const CONTENT_TYPE_CONFIG: Record<ContentType, {
  label: string
  icon: string
  color: string
  allowedSources: ContentSource[]
}> = {
  course: { label: '系统课程', icon: 'read', color: '#1890ff', allowedSources: ['platform', 'expert'] },
  video: { label: '视频', icon: 'video-camera', color: '#722ed1', allowedSources: ['platform', 'expert', 'coach'] },
  article: { label: '文章', icon: 'file-text', color: '#52c41a', allowedSources: ['platform', 'expert', 'coach', 'sharer', 'ai_generated'] },
  audio: { label: '音频', icon: 'audio', color: '#faad14', allowedSources: ['platform', 'expert'] },
  card: { label: '练习卡片', icon: 'credit-card', color: '#eb2f96', allowedSources: ['platform', 'expert', 'coach'] },
  live: { label: '直播', icon: 'youtube', color: '#ff4d4f', allowedSources: ['platform', 'expert', 'coach'] },
  case_share: { label: '案例分享', icon: 'message', color: '#13c2c2', allowedSources: ['sharer', 'coach', 'expert'] },
  tool: { label: '工具', icon: 'tool', color: '#8c8c8c', allowedSources: ['platform', 'external'] },
}

/** 审核优先级规则 */
export const REVIEW_PRIORITY_RULES: {
  source: ContentSource
  type: ContentType
  priority: 'high' | 'normal' | 'low'
}[] = [
  // UGC内容优先审核
  { source: 'sharer', type: 'case_share', priority: 'high' },
  { source: 'sharer', type: 'article', priority: 'high' },
  // 教练内容正常优先级
  { source: 'coach', type: 'article', priority: 'normal' },
  { source: 'coach', type: 'video', priority: 'normal' },
  // AI生成内容低优先级
  { source: 'ai_generated', type: 'article', priority: 'low' },
]

// ==================== 视频内容与配套测试 ====================

/** 视频内容 */
export interface VideoContent {
  video_id: string
  title: string
  description?: string
  url: string
  cover_url?: string
  duration_seconds: number
  source: ContentSource
  status: ContentStatus

  // 所属课程
  course_id?: string
  chapter_id?: string
  lesson_order?: number

  // 领域
  domain?: TriggerDomain

  // 配套测试
  has_quiz: boolean
  quiz_id?: string
  min_watch_percent: number  // 解锁测试最低观看百分比

  // 学习积分/时长配置
  coach_points: number       // 教练完成获得积分
  grower_minutes: number     // 成长者计算时长

  // 作者
  author_id: string
  author_name: string

  // 统计
  view_count: number
  complete_count: number

  created_at: string
  updated_at: string
}

/** 视频配套测试 */
export interface VideoQuiz {
  quiz_id: string
  video_id: string
  title: string
  description?: string

  // 题目
  questions: QuizQuestion[]

  // 通过条件
  pass_score: number         // 及格分数（百分制）
  max_attempts: number       // 最大尝试次数
  time_limit_seconds?: number

  // 奖励配置
  coach_points_bonus: number   // 满分额外积分
  grower_minutes_bonus: number // 满分额外时长

  created_at: string
  updated_at: string
}

/** 测试题目 */
export interface QuizQuestion {
  question_id: string
  quiz_id: string
  order: number
  type: 'single' | 'multiple' | 'judge'
  content: string
  options: { key: string; content: string }[]
  correct_answer: string | string[]
  explanation?: string
  points: number
}

/** 测试结果 */
export interface QuizResult {
  result_id: string
  quiz_id: string
  user_id: string
  score: number
  correct_count: number
  total_count: number
  passed: boolean
  points_earned: number
  minutes_earned: number
  attempt_number: number
  submitted_at: string
}

// ==================== 学习激励系统 ====================

/** 教练学习积分（认证晋级） */
export interface CoachLearningRecord {
  user_id: string
  total_points: number
  current_level: CoachLevel

  // 分类积分
  category_points: {
    knowledge: number
    method: number
    skill: number
    value: number
    practice: number
    case_study: number
  }

  // 认证进度
  certification_progress: {
    points_met: boolean
    exam_passed: boolean
    practice_hours: number
    mentor_approved: boolean
  }

  updated_at: string
}

/** 成长者学习时长（奖励获取） */
export interface GrowerLearningRecord {
  user_id: string
  total_minutes: number

  // 周期统计
  today_minutes: number
  week_minutes: number
  month_minutes: number

  // 连续学习
  current_streak: number
  longest_streak: number

  // 领域分布
  domain_minutes: Record<string, number>

  // 已获得奖励数
  rewards_earned: number

  updated_at: string
}

/** 积分/时长记录 */
export interface LearningPointsRecord {
  record_id: string
  user_id: string
  user_type: 'coach' | 'grower'

  // 来源
  source_type: 'video' | 'quiz' | 'course_complete' | 'exam' | 'practice'
  source_id: string
  source_title: string

  // 获得
  points: number        // 教练积分
  minutes: number       // 成长者时长
  category?: string     // 积分分类

  earned_at: string
}

// ==================== 学习激励配置 ====================

/** 教练等级积分要求 */
export const COACH_LEVEL_REQUIREMENTS: Record<CoachLevel, {
  min_total: number
  min_categories: Record<string, number>
  exam_required: boolean
}> = {
  L0: { min_total: 0, min_categories: {}, exam_required: false },
  L1: { min_total: 100, min_categories: { knowledge: 30, method: 20 }, exam_required: true },
  L2: { min_total: 300, min_categories: { knowledge: 80, method: 60, skill: 40 }, exam_required: true },
  L3: { min_total: 600, min_categories: { knowledge: 150, method: 120, skill: 100, value: 50 }, exam_required: true },
  L4: { min_total: 1000, min_categories: { knowledge: 250, method: 200, skill: 180, value: 100 }, exam_required: true },
}

/** 成长者时长奖励阈值 */
export const GROWER_TIME_MILESTONES = [
  { minutes: 60, reward: '初次探索', icon: '🌱' },
  { minutes: 180, reward: '持续学习', icon: '📚' },
  { minutes: 600, reward: '学习达人', icon: '🌟' },
  { minutes: 1200, reward: '知识探索者', icon: '🔭' },
  { minutes: 3000, reward: '学习大师', icon: '🏆' },
]

/** 连续学习奖励 */
export const STREAK_MILESTONES = [
  { days: 3, reward: '三日坚持', icon: '🔥' },
  { days: 7, reward: '一周达成', icon: '💪' },
  { days: 21, reward: '习惯养成', icon: '🎯' },
  { days: 30, reward: '月度冠军', icon: '🥇' },
]
