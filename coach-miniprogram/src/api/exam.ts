/**
 * 认证考试 API
 * 对应后端: /api/v1/certification/*
 */
import http from './request'

const examApi = {
  /** 可用考试列表 */
  getExams(params?: Record<string, any>) {
    return http.get<{ items: any[]; total: number }>('/v1/certification/exams', params)
  },
  /** 考试详情 */
  getExamDetail(id: number) {
    return http.get<any>(`/v1/certification/exams/${id}`)
  },
  /** 开始考试 */
  startSession(examId: number) {
    return http.post<any>('/v1/certification/sessions/start', { exam_id: examId })
  },
  /** 提交考试 */
  submitSession(data: Record<string, any>) {
    return http.post<any>('/v1/certification/sessions/submit', data)
  },
  /** 考试结果 */
  getResult(sessionId: number) {
    return http.get<any>(`/v1/certification/sessions/${sessionId}/result`)
  },
  /** 我的考试结果列表 */
  getMyResults(params?: Record<string, any>) {
    return http.get<any>('/v1/certification/sessions/my-results', params)
  },
  /** 题库 */
  getQuestions(params?: Record<string, any>) {
    return http.get<any>('/v1/certification/questions', params)
  },
}

export default examApi
