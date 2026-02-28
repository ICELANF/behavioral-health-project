/**
 * 认证考试 API
 * 对应后端: /api/v1/exams/*
 */
import http from './request'

const examApi = {
  /** 可用考试列表 */
  getExams(params?: Record<string, any>) {
    return http.get<{ items: any[]; total: number }>('/v1/exams', params)
  },
  /** 考试详情 */
  getExamDetail(id: number) {
    return http.get<any>(`/v1/exams/${id}`)
  },
  /** 开始考试 */
  startSession(examId: number) {
    return http.post<any>(`/v1/exams/${examId}/start`, {})
  },
  /** 提交答案 */
  submitAnswer(sessionId: number, questionId: number, answer: any) {
    return http.post<any>(`/v1/exam-sessions/${sessionId}/answer`, { question_id: questionId, answer })
  },
  /** 完成考试 */
  finishSession(sessionId: number) {
    return http.post<any>(`/v1/exam-sessions/${sessionId}/finish`, {})
  },
  /** 考试结果 */
  getResult(sessionId: number) {
    return http.get<any>(`/v1/exam-sessions/${sessionId}/result`)
  },
  /** 考试历史 */
  getHistory(params?: Record<string, any>) {
    return http.get<{ items: any[]; total: number }>('/v1/exam-sessions/my', params)
  },
}

export default examApi
