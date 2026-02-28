/**
 * 教练端 API
 * 对应后端: /api/v1/coach/*
 */
import http from './request'

const coachApi = {
  /** 教练仪表盘 */
  getDashboard() {
    return http.get<any>('/v1/coach/dashboard')
  },
  /** 学员列表 */
  getStudents(params?: Record<string, any>) {
    return http.get<{ items: any[]; total: number }>('/v1/coach/students', params)
  },
  /** 学员详情 */
  getStudentDetail(id: number) {
    return http.get<any>(`/v1/coach/students/${id}`)
  },
  /** 推送审批队列 */
  getPushQueue(params?: Record<string, any>) {
    return http.get<{ items: any[] }>('/v1/coach-push/pending', params)
  },
  /** 审批推送 */
  approvePush(id: number) {
    return http.post<any>(`/v1/coach-push/${id}/approve`, {})
  },
  /** 拒绝推送 */
  rejectPush(id: number, reason?: string) {
    return http.post<any>(`/v1/coach-push/${id}/reject`, { reason })
  },
  /** 评估列表 */
  getAssessments(params?: Record<string, any>) {
    return http.get<{ items: any[]; total: number }>('/v1/coach/assessments', params)
  },
  /** 审核评估 */
  reviewAssessment(id: number, data: Record<string, any>) {
    return http.post<any>(`/v1/coach/assessments/${id}/review`, data)
  },
  /** 教练绩效 */
  getPerformance() {
    return http.get<any>('/v1/coach/performance')
  },
}

export default coachApi
