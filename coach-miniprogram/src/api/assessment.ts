/**
 * 评估 API
 * 对应后端: /api/v1/assessment-assignments/*
 */
import http from './request'

const assessmentApi = {
  /** 待完成评估 */
  getPending(params?: Record<string, any>) {
    return http.get<{ items: any[] }>('/v1/assessment-assignments/my-pending', { status: 'assigned', ...params })
  },
  /** 评估详情 */
  getDetail(id: number) {
    return http.get<any>(`/v1/assessment-assignments/${id}`)
  },
  /** 提交评估答案 */
  submit(id: number, answers: Record<string, any>) {
    return http.post<any>(`/v1/assessment-assignments/${id}/submit`, answers)
  },
  /** 评估结果 */
  getResult(id: number) {
    return http.get<any>(`/v1/assessment-assignments/${id}/result`)
  },
}

export default assessmentApi
