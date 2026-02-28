/**
 * 学习中心 API
 * 对应后端: /api/v1/content/*, /api/v1/learning/*
 */
import http from './request'

const learningApi = {
  /** 课程列表 */
  getCourses(params?: Record<string, any>) {
    return http.get<{ items: any[]; total: number }>('/v1/content/courses', params)
  },
  /** 课程详情 */
  getCourseDetail(id: number) {
    return http.get<any>(`/v1/content/courses/${id}`)
  },
  /** 内容详情 */
  getContentDetail(id: number) {
    return http.get<any>(`/v1/content/${id}`)
  },
  /** 推荐内容 */
  getRecommended(params?: Record<string, any>) {
    return http.get<{ items: any[] }>('/v1/content/recommended', params)
  },
  /** 我的学习记录 */
  getMyLearning(params?: Record<string, any>) {
    return http.get<{ items: any[]; total: number }>('/v1/learning/my', params)
  },
  /** 我的学分 */
  getMyCredits() {
    return http.get<{ total_credits: number; items: any[] }>('/v1/learning/credits')
  },
  /** 提交测验 */
  submitQuiz(contentId: number, answers: Record<string, any>) {
    return http.post<any>(`/v1/content/${contentId}/quiz/submit`, answers)
  },
}

export default learningApi
