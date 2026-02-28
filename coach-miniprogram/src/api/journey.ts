/**
 * 成长路径 API
 * 对应后端: /api/v1/journey/*
 */
import http from './request'

const journeyApi = {
  /** 成长路径总览 */
  getOverview() {
    return http.get<any>('/v1/journey/overview')
  },
  /** 我的进度 */
  getProgress() {
    return http.get<any>('/v1/journey/progress')
  },
  /** 申请晋级 */
  applyPromotion(data: Record<string, any>) {
    return http.post<any>('/v1/journey/promotion/apply', data)
  },
  /** 晋级申请记录 */
  getPromotionHistory(params?: Record<string, any>) {
    return http.get<{ items: any[]; total: number }>('/v1/journey/promotion/history', params)
  },
}

export default journeyApi
