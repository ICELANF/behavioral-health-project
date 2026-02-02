import request from './request'
import type { AssessmentInput, AssessmentResult } from '@/types'

/**
 * 评估相关API
 */
export const assessmentAPI = {
  /**
   * 提交评估数据
   */
  submit(data: AssessmentInput): Promise<AssessmentResult> {
    return request.post<AssessmentResult>('/api/assessment/submit', data, {
      silentError: true // 使用Mock数据fallback，不显示错误提示
    })
  },

  /**
   * 获取评估结果
   */
  getResult(assessmentId: string): Promise<AssessmentResult> {
    return request.get<AssessmentResult>(`/api/assessment/${assessmentId}`, {
      silentError: true // 使用Mock数据fallback，不显示错误提示
    })
  },

  /**
   * 获取用户评估历史
   */
  getHistory(userId: number, page: number = 1, pageSize: number = 10): Promise<AssessmentResult[]> {
    return request.get<AssessmentResult[]>(`/api/assessment/history/${userId}`, {
      params: { page, page_size: pageSize },
      silentError: true // 使用Mock数据fallback，不显示错误提示
    })
  },

  /**
   * 获取用户最近的评估
   */
  getRecent(userId: number, limit: number = 5): Promise<AssessmentResult[]> {
    return request.get<AssessmentResult[]>(`/api/assessment/recent/${userId}`, {
      params: { limit },
      silentError: true // 使用Mock数据fallback，不显示错误提示
    })
  }
}
