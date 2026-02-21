import { defineStore } from 'pinia';
import { ref } from 'vue';
import { questionApi } from '../api/question';
import type { Question, QuestionListParams } from '../types/exam';

/**
 * 题库状态管理
 */
export const useQuestionStore = defineStore('question', () => {
  // State
  const questions = ref<Question[]>([]);
  const currentQuestion = ref<Question | null>(null);
  const loading = ref(false);
  const total = ref(0);

  // Filters
  const filters = ref<QuestionListParams>({
    page: 1,
    page_size: 20,
    status: 'active',
  });

  // Actions
  async function fetchQuestions(params?: QuestionListParams) {
    loading.value = true;
    try {
      const mergedParams = { ...filters.value, ...params };
      const response = await questionApi.list(mergedParams);
      const body = response.data as any;
      questions.value = body.items || body.data || [];
      total.value = body.total ?? questions.value.length;
    } catch (error) {
      console.error('Failed to fetch questions:', error);
      questions.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function fetchQuestion(questionId: string) {
    loading.value = true;
    try {
      const response = await questionApi.get(questionId);
      const body = response.data as any;
      const q = body.data || body;
      currentQuestion.value = q;
      return q;
    } catch (error) {
      console.error('Failed to fetch question:', error);
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function createQuestion(question: Partial<Question>) {
    const response = await questionApi.create(question);
    const body = response.data as any;
    const newQuestion = body.data || body;
    questions.value.unshift(newQuestion);
    return newQuestion;
  }

  async function updateQuestion(questionId: string, question: Partial<Question>) {
    const response = await questionApi.update(questionId, question);
    const body = response.data as any;
    const updatedQuestion = body.data || body;
    const index = questions.value.findIndex((q) => q.question_id === questionId);
    if (index > -1) {
      questions.value[index] = updatedQuestion;
    }
    if (currentQuestion.value?.question_id === questionId) {
      currentQuestion.value = updatedQuestion;
    }
    return updatedQuestion;
  }

  async function deleteQuestion(questionId: string) {
    await questionApi.delete(questionId);
    questions.value = questions.value.filter((q) => q.question_id !== questionId);
  }

  function setFilters(newFilters: Partial<QuestionListParams>) {
    filters.value = { ...filters.value, ...newFilters };
  }

  function resetFilters() {
    filters.value = { page: 1, page_size: 20, status: 'active' };
  }

  function clearCurrentQuestion() {
    currentQuestion.value = null;
  }

  return {
    // State
    questions,
    currentQuestion,
    loading,
    total,
    filters,
    // Actions
    fetchQuestions,
    fetchQuestion,
    createQuestion,
    updateQuestion,
    deleteQuestion,
    setFilters,
    resetFilters,
    clearCurrentQuestion,
  };
});
