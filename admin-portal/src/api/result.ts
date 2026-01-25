import request from './request';
import type { ExamResult, ResultListParams } from '../types/exam';

/**
 * 考试成绩 API
 */
export const resultApi = {
  /**
   * 获取考试成绩列表
   */
  list(params: ResultListParams) {
    return request.get<{ success: boolean; data: ExamResult[] }>('/certification/results', { params });
  },

  /**
   * 获取单个成绩详情
   */
  get(resultId: string) {
    return request.get<{ success: boolean; data: ExamResult }>(`/certification/results/${resultId}`);
  },

  /**
   * 导出成绩
   */
  export(examId: string, format: 'csv' | 'xlsx' = 'csv') {
    return request.get(`/certification/results/export`, {
      params: { exam_id: examId, format },
      responseType: 'blob',
    });
  },

  /**
   * 作废成绩
   */
  invalidate(resultId: string, reason: string) {
    return request.post<{ success: boolean }>(`/certification/results/${resultId}/invalidate`, { reason });
  },

  /**
   * 获取考生的所有成绩
   */
  getByCoach(coachId: string) {
    return request.get<{ success: boolean; data: ExamResult[] }>(`/certification/coaches/${coachId}/results`);
  },
};
