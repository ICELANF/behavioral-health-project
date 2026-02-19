/**
 * 推荐系统 API - 基于用户状态的个性化推荐
 */
import request from './request'
import { BEHAVIOR_STAGE_MAP, TRIGGER_DOMAINS } from '@/constants/index'

// ============ 类型定义 ============

// 用户关注的问题领域
export type FocusArea = keyof typeof TRIGGER_DOMAINS

// 推荐视频
export interface RecommendedVideo {
  id: string
  title: string
  description: string
  thumbnail: string
  duration: number // 秒
  category: FocusArea
  stage: keyof typeof BEHAVIOR_STAGE_MAP
  views: number
  likes: number
  instructor: string
}

// 推荐产品
export interface RecommendedProduct {
  id: string
  name: string
  description: string
  image: string
  price: number
  originalPrice?: number
  category: FocusArea
  rating: number
  salesCount: number
  tags: string[]
}

// 推荐课程
export interface RecommendedCourse {
  id: string
  title: string
  description: string
  cover: string
  instructor: string
  instructorAvatar: string
  duration: number // 分钟
  lessonCount: number
  category: FocusArea
  stage: keyof typeof BEHAVIOR_STAGE_MAP
  level: 'beginner' | 'intermediate' | 'advanced'
  enrollCount: number
  rating: number
  price: number
  isFree: boolean
}

// 教练行为推荐
export interface RecommendedCoachAction {
  id: string
  title: string
  description: string
  category: 'education' | 'guidance' | 'coaching' | 'support'
  script: string
  tips: string[]
  stage: keyof typeof BEHAVIOR_STAGE_MAP
  focusArea: FocusArea
  difficulty: 'easy' | 'medium' | 'hard'
  expectedDuration: number // 分钟
}

// 综合推荐结果
export interface RecommendationResult {
  userStage: keyof typeof BEHAVIOR_STAGE_MAP
  focusAreas: FocusArea[]
  videos: RecommendedVideo[]
  products: RecommendedProduct[]
  courses: RecommendedCourse[]
  coachActions: RecommendedCoachAction[]
  dailyTip: {
    icon: string
    title: string
    content: string
  }
}

// ============ API 函数 ============

/**
 * 获取用户关注的问题领域
 */
export async function getUserFocusAreas(): Promise<FocusArea[]> {
  const res = await request.get('/v1/recommendations/focus-areas')
  return res.data
}

/**
 * 获取个性化推荐
 */
export async function getRecommendations(
  stage: keyof typeof BEHAVIOR_STAGE_MAP,
  focusAreas: FocusArea[]
): Promise<RecommendationResult> {
  const res = await request.get('/v1/recommendations', {
    params: { stage, focus_areas: focusAreas.join(',') }
  })
  return res.data
}

/**
 * 记录用户点击行为（用于优化推荐）
 */
export async function trackRecommendationClick(
  type: 'video' | 'product' | 'course' | 'coachAction',
  itemId: string
): Promise<void> {
  await request.post('/v1/recommendations/track', { type, item_id: itemId })
}

/**
 * 更新用户关注领域
 */
export async function updateUserFocusAreas(areas: FocusArea[]): Promise<boolean> {
  const res = await request.put('/v1/recommendations/focus-areas', { areas })
  return res.data
}
