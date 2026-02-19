import request from './request'

export interface Questionnaire {
  id: string
  name: string
  description: string
  category: string
  questionCount: number
  estimatedMin: number
  icon: string
  color: string
  questions: AssessmentQuestion[]
}

export interface AssessmentQuestion {
  text: string
  type: 'single' | 'multiple' | 'scale'
  options?: Array<{ text: string; score: number }>
  minLabel?: string
  maxLabel?: string
  maxValue?: number
}

export interface AssessmentSubmission {
  questionnaireId: string
  answers: (number | number[] | null)[]
  totalScore: number
  timestamp: string
}

export interface AssessmentResult {
  id: string
  questionnaireId: string
  questionnaireName: string
  score: number
  maxScore: number
  level: string
  date: string
  answers: (number | number[] | null)[]
}

export const assessmentApi = {
  async getQuestionnaires(params: { category?: string } = {}) {
    const res = await request.get('/v1/assessment/questionnaires', { params })
    return res.data
  },

  async getQuestionnaire(id: string) {
    const res = await request.get(`/v1/assessment/questionnaires/${id}`)
    return res.data
  },

  async submitAssessment(data: AssessmentSubmission) {
    const res = await request.post('/v1/assessment/submit', data)
    return res.data
  },

  async getResult(resultId: string) {
    const res = await request.get(`/v1/assessment/results/${resultId}`)
    return res.data
  },

  async getPatientResults(patientId: string, params: { page?: number; pageSize?: number } = {}) {
    const res = await request.get(`/v1/assessment/patient/${patientId}/results`, { params })
    return res.data
  },

  async getRecommended(patientId: string) {
    const res = await request.get(`/v1/assessment/patient/${patientId}/recommended`)
    return res.data
  },

  async saveDraft(patientId: string, questionnaireId: string, data: { answers: any[]; currentIndex: number }) {
    const res = await request.post(`/v1/assessment/patient/${patientId}/draft/${questionnaireId}`, data)
    return res.data
  },

  async getDraft(patientId: string, questionnaireId: string) {
    const res = await request.get(`/v1/assessment/patient/${patientId}/draft/${questionnaireId}`)
    return res.data
  },
}

export default assessmentApi
