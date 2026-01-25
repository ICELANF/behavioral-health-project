import request from './request';
import type { Question, QuestionListParams } from '../types/exam';

/**
 * 题库管理 API
 */
export const questionApi = {
  /**
   * 获取题目列表
   */
  list(params?: QuestionListParams) {
    return request.get<{ success: boolean; data: Question[] }>('/certification/questions', { params });
  },

  /**
   * 获取单个题目详情
   */
  get(questionId: string) {
    return request.get<{ success: boolean; data: Question }>(`/certification/questions/${questionId}`);
  },

  /**
   * 创建题目
   */
  create(question: Partial<Question>) {
    return request.post<{ success: boolean; data: Question }>('/certification/questions', question);
  },

  /**
   * 更新题目
   */
  update(questionId: string, question: Partial<Question>) {
    return request.put<{ success: boolean; data: Question }>(`/certification/questions/${questionId}`, question);
  },

  /**
   * 删除题目
   */
  delete(questionId: string) {
    return request.delete<{ success: boolean }>(`/certification/questions/${questionId}`);
  },

  /**
   * 批量导入题目
   */
  bulkImport(questions: Partial<Question>[]) {
    return request.post<{ success: boolean; data: { imported: number; failed: number } }>('/certification/questions/bulk', {
      questions,
    });
  },
};
