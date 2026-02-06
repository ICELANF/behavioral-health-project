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

// Mock questionnaire list
const mockQuestionnaires: Omit<Questionnaire, 'questions'>[] = [
  { id: 'phq9', name: 'PHQ-9 抑郁筛查', description: '评估过去两周的抑郁症状', category: 'mood', questionCount: 9, estimatedMin: 3, icon: '😔', color: '#e6f7ff' },
  { id: 'gad7', name: 'GAD-7 焦虑评估', description: '广泛性焦虑障碍7项量表', category: 'mood', questionCount: 7, estimatedMin: 3, icon: '😰', color: '#fff7e6' },
  { id: 'pss10', name: 'PSS-10 压力感知', description: '感知压力量表10项版', category: 'stress', questionCount: 10, estimatedMin: 5, icon: '😤', color: '#fff1f0' },
  { id: 'who5', name: 'WHO-5 幸福指数', description: 'WHO五项幸福感指数', category: 'wellbeing', questionCount: 5, estimatedMin: 2, icon: '😊', color: '#f6ffed' },
  { id: 'audit', name: 'AUDIT 饮酒评估', description: '酒精使用障碍识别测试', category: 'behavior', questionCount: 10, estimatedMin: 5, icon: '🍷', color: '#f9f0ff' },
  { id: 'ipaq', name: 'IPAQ 体力活动', description: '国际体力活动问卷-短版', category: 'behavior', questionCount: 7, estimatedMin: 4, icon: '🏃', color: '#e6fffb' },
  { id: 'psqi', name: 'PSQI 睡眠质量', description: '匹兹堡睡眠质量指数', category: 'wellbeing', questionCount: 19, estimatedMin: 8, icon: '😴', color: '#f0f5ff' },
  { id: 'dass21', name: 'DASS-21 综合评估', description: '抑郁-焦虑-压力量表21项', category: 'mood', questionCount: 21, estimatedMin: 10, icon: '📋', color: '#fffbe6' },
]

const mockResults: AssessmentResult[] = [
  { id: 'r1', questionnaireId: 'gad7', questionnaireName: 'GAD-7 焦虑评估', score: 8, maxScore: 21, level: '轻度焦虑', date: '2025-01-15', answers: [] },
  { id: 'r2', questionnaireId: 'phq9', questionnaireName: 'PHQ-9 抑郁筛查', score: 5, maxScore: 27, level: '无/极轻微', date: '2025-01-10', answers: [] },
  { id: 'r3', questionnaireId: 'who5', questionnaireName: 'WHO-5 幸福指数', score: 56, maxScore: 100, level: '一般', date: '2025-01-05', answers: [] },
  { id: 'r4', questionnaireId: 'pss10', questionnaireName: 'PSS-10 压力感知', score: 22, maxScore: 40, level: '中等压力', date: '2024-12-28', answers: [] },
]

export const assessmentApi = {
  async getQuestionnaires(params: { category?: string } = {}) {
    try {
      const res = await request.get('/v1/assessment/questionnaires', { params })
      return res.data
    } catch (e) {
      let list = mockQuestionnaires
      if (params.category) list = list.filter(q => q.category === params.category)
      return { list }
    }
  },

  async getQuestionnaire(id: string) {
    try {
      const res = await request.get(`/v1/assessment/questionnaires/${id}`)
      return res.data
    } catch (e) {
      return null
    }
  },

  async submitAssessment(data: AssessmentSubmission) {
    try {
      const res = await request.post('/v1/assessment/submit', data)
      return res.data
    } catch (e) {
      return { success: true, resultId: `r_${Date.now()}` }
    }
  },

  async getResult(resultId: string) {
    try {
      const res = await request.get(`/v1/assessment/results/${resultId}`)
      return res.data
    } catch (e) {
      return mockResults.find(r => r.id === resultId) || null
    }
  },

  async getPatientResults(patientId: string, params: { page?: number; pageSize?: number } = {}) {
    try {
      const res = await request.get(`/v1/assessment/patient/${patientId}/results`, { params })
      return res.data
    } catch (e) {
      return { list: mockResults, total: mockResults.length }
    }
  },

  async getRecommended(patientId: string) {
    try {
      const res = await request.get(`/v1/assessment/patient/${patientId}/recommended`)
      return res.data
    } catch (e) {
      return {
        recommended: [
          { id: 'phq9', name: 'PHQ-9 抑郁筛查', description: '共9题，约3分钟完成' },
        ]
      }
    }
  },

  async saveDraft(patientId: string, questionnaireId: string, data: { answers: any[]; currentIndex: number }) {
    try {
      const res = await request.post(`/v1/assessment/patient/${patientId}/draft/${questionnaireId}`, data)
      return res.data
    } catch (e) {
      return { success: true }
    }
  },

  async getDraft(patientId: string, questionnaireId: string) {
    try {
      const res = await request.get(`/v1/assessment/patient/${patientId}/draft/${questionnaireId}`)
      return res.data
    } catch (e) {
      return null
    }
  },
}

export default assessmentApi
