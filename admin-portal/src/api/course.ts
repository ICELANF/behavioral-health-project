/**
 * 课程内容 API 客户端
 * 调用 /api/v1/content 系列端点
 */

import request from './request'

export interface ContentAccessStatus {
  accessible: boolean
  reason: string | null
  unlock_level: string | null
  unlock_level_label: string | null
}

export interface ContentItem {
  id: string
  type: string
  source: string
  title: string
  domain?: string
  level?: string
  audience?: string
  author: Record<string, any>
  view_count: number
  like_count: number
  duration?: number
  is_free: boolean
  access_status?: ContentAccessStatus
}

export interface ContentListParams {
  page?: number
  page_size?: number
  type?: string
  source?: string
  domain?: string
  level?: string
  audience?: string
  keyword?: string
}

export interface CourseDetail {
  id: string
  title: string
  description: string
  author: Record<string, any>
  domain: string
  level: string
  duration_minutes: number
  chapter_count: number
  lesson_count?: number
  chapters?: any[]
  is_free: boolean
  enroll_count: number
  rating: number
  coach_points?: number
  grower_minutes?: number
  video_url?: string
  access_status?: ContentAccessStatus
}

/**
 * 获取内容列表
 */
export async function fetchContentList(params: ContentListParams = {}) {
  const res = await request.get('/v1/content', { params })
  return res.data
}

/**
 * 获取课程详情
 */
export async function fetchCourseDetail(courseId: string): Promise<CourseDetail | null> {
  const res = await request.get(`/v1/content/course/${courseId}`)
  return res.data
}

/**
 * 报名课程
 */
export async function enrollCourse(courseId: string) {
  const res = await request.post(`/v1/content/course/${courseId}/enroll`)
  return res.data
}
