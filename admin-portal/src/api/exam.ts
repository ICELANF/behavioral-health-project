import request from './request';
import type { ExamDefinition, ExamListParams, ExamStatistics } from '../types/exam';

/**
 * 考试管理 API
 */
export const examApi = {
  /**
   * 获取考试列表
   */
  list(params?: ExamListParams) {
    return request.get<{ success: boolean; data: ExamDefinition[] }>('/v1/certification/exams', { params });
  },

  /**
   * 获取单个考试详情
   */
  get(examId: string) {
    return request.get<{ success: boolean; data: ExamDefinition }>(`/v1/certification/exams/${examId}`);
  },

  /**
   * 创建考试
   */
  create(exam: Partial<ExamDefinition>) {
    return request.post<{ success: boolean; data: ExamDefinition }>('/v1/certification/exams', exam);
  },

  /**
   * 更新考试
   */
  update(examId: string, exam: Partial<ExamDefinition>) {
    return request.put<{ success: boolean; data: ExamDefinition }>(`/v1/certification/exams/${examId}`, exam);
  },

  /**
   * 删除考试
   */
  delete(examId: string) {
    return request.delete<{ success: boolean }>(`/v1/certification/exams/${examId}`);
  },

  /**
   * 发布考试
   */
  publish(examId: string) {
    return request.post<{ success: boolean; data: ExamDefinition }>(`/v1/certification/exams/${examId}/publish`);
  },

  /**
   * 下架考试
   */
  archive(examId: string) {
    return request.post<{ success: boolean; data: ExamDefinition }>(`/v1/certification/exams/${examId}/archive`);
  },

  /**
   * 获取考试统计
   */
  getStatistics(examId: string) {
    return request.get<{ success: boolean; data: ExamStatistics }>(`/v1/certification/exams/${examId}/statistics`);
  },

  /**
   * 分配题目到考试
   */
  assignQuestions(examId: string, questionIds: string[]) {
    return request.post<{ success: boolean; data: ExamDefinition }>(`/v1/certification/exams/${examId}/questions`, {
      question_ids: questionIds,
    });
  },

  /**
   * 获取考试的题目列表
   */
  getQuestions(examId: string) {
    return request.get(`/v1/certification/exams/${examId}/questions`);
  },
};
