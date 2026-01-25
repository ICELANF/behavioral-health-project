import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { examApi } from '../api/exam';
import type { ExamDefinition, ExamListParams, ExamStatistics } from '../types/exam';

/**
 * 考试状态管理
 */
export const useExamStore = defineStore('exam', () => {
  // State
  const exams = ref<ExamDefinition[]>([]);
  const currentExam = ref<ExamDefinition | null>(null);
  const statistics = ref<ExamStatistics | null>(null);
  const loading = ref(false);
  const total = ref(0);

  // Filters
  const filters = ref<ExamListParams>({
    page: 1,
    page_size: 10,
  });

  // Getters
  const publishedExams = computed(() => exams.value.filter((e) => e.status === 'published'));
  const draftExams = computed(() => exams.value.filter((e) => e.status === 'draft'));

  // Actions
  async function fetchExams(params?: ExamListParams) {
    loading.value = true;
    try {
      const mergedParams = { ...filters.value, ...params };
      const response = await examApi.list(mergedParams);
      exams.value = response.data.data || [];
      total.value = exams.value.length;
    } catch (error) {
      console.error('Failed to fetch exams:', error);
      exams.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function fetchExam(examId: string) {
    loading.value = true;
    try {
      const response = await examApi.get(examId);
      currentExam.value = response.data.data;
      return response.data.data;
    } catch (error) {
      console.error('Failed to fetch exam:', error);
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function createExam(exam: Partial<ExamDefinition>) {
    const response = await examApi.create(exam);
    const newExam = response.data.data;
    exams.value.unshift(newExam);
    return newExam;
  }

  async function updateExam(examId: string, exam: Partial<ExamDefinition>) {
    const response = await examApi.update(examId, exam);
    const updatedExam = response.data.data;
    const index = exams.value.findIndex((e) => e.exam_id === examId);
    if (index > -1) {
      exams.value[index] = updatedExam;
    }
    if (currentExam.value?.exam_id === examId) {
      currentExam.value = updatedExam;
    }
    return updatedExam;
  }

  async function deleteExam(examId: string) {
    await examApi.delete(examId);
    exams.value = exams.value.filter((e) => e.exam_id !== examId);
  }

  async function publishExam(examId: string) {
    const response = await examApi.publish(examId);
    const updatedExam = response.data.data;
    const index = exams.value.findIndex((e) => e.exam_id === examId);
    if (index > -1) {
      exams.value[index] = updatedExam;
    }
    return updatedExam;
  }

  async function archiveExam(examId: string) {
    const response = await examApi.archive(examId);
    const updatedExam = response.data.data;
    const index = exams.value.findIndex((e) => e.exam_id === examId);
    if (index > -1) {
      exams.value[index] = updatedExam;
    }
    return updatedExam;
  }

  async function fetchStatistics(examId: string) {
    const response = await examApi.getStatistics(examId);
    statistics.value = response.data.data;
    return response.data.data;
  }

  function setFilters(newFilters: Partial<ExamListParams>) {
    filters.value = { ...filters.value, ...newFilters };
  }

  function resetFilters() {
    filters.value = { page: 1, page_size: 10 };
  }

  function clearCurrentExam() {
    currentExam.value = null;
    statistics.value = null;
  }

  return {
    // State
    exams,
    currentExam,
    statistics,
    loading,
    total,
    filters,
    // Getters
    publishedExams,
    draftExams,
    // Actions
    fetchExams,
    fetchExam,
    createExam,
    updateExam,
    deleteExam,
    publishExam,
    archiveExam,
    fetchStatistics,
    setFilters,
    resetFilters,
    clearCurrentExam,
  };
});
