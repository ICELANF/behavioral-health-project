import request from './request'

export interface CoachPerformance {
  successRate: number
  retentionRate: number
  avgResponseMin: number
  satisfaction: number
  monthlyData: Array<{ label: string; success: number; retention: number }>
}

export interface CoachCertification {
  currentLevel: { badge: string; name: string; description: string; color: string; since: string }
  nextLevel: { name: string; color: string }
  requirements: Array<{ label: string; current: number; target: number; completed: boolean }>
  completedCourses: Array<{ id: string; name: string; completedDate: string; required: boolean; score: number }>
  examHistory: Array<{ id: string; name: string; date: string; score: number; total: number; passed: boolean }>
}

export interface ContentSharingRecord {
  id: string
  contentType: string
  contentTitle: string
  recipientCount: number
  sentAt: string
  readCount: number
}

// Mock data
const mockPerformance: CoachPerformance = {
  successRate: 73.5,
  retentionRate: 88.2,
  avgResponseMin: 12,
  satisfaction: 4.6,
  monthlyData: [
    { label: '1月', success: 74, retention: 88 },
    { label: '12月', success: 69, retention: 85 },
    { label: '11月', success: 65, retention: 82 },
  ],
}

export const coachApi = {
  async getPerformance(coachId: string, params: { startDate?: string; endDate?: string } = {}) {
    try {
      const res = await request.get(`/v1/coach/${coachId}/performance`, { params })
      return res.data
    } catch (e) {
      return mockPerformance
    }
  },

  async getCertification(coachId: string) {
    try {
      const res = await request.get(`/v1/coach/${coachId}/certification`)
      return res.data
    } catch (e) {
      return {
        currentLevel: { badge: 'L2', name: '中级健康教练', description: '具备独立开展行为健康干预的能力', color: '#1890ff', since: '2024-08-15' },
        nextLevel: { name: '高级健康教练 (L3)', color: '#722ed1' },
        requirements: [
          { label: '服务学员数', current: 28, target: 30, completed: false },
          { label: '干预成功率', current: 74, target: 70, completed: true },
        ],
      }
    }
  },

  async applyPromotion(coachId: string) {
    try {
      const res = await request.post(`/v1/coach/${coachId}/promotion/apply`)
      return res.data
    } catch (e) {
      return { success: true, message: '申请已提交' }
    }
  },

  async getStudents(coachId: string) {
    try {
      const res = await request.get(`/v1/coach/${coachId}/students`)
      return res.data
    } catch (e) {
      return {
        students: [
          { id: '1', name: '张伟', stage: '行动期', risk: '低风险', completion: 85, activeDays: 6 },
          { id: '2', name: '李娜', stage: '思考期', risk: '中风险', completion: 45, activeDays: 3 },
        ]
      }
    }
  },

  async shareContent(coachId: string, data: { contentId: string; contentType: string; studentIds: string[]; message: string; sendMode: string; scheduledTime?: string }) {
    try {
      const res = await request.post(`/v1/coach/${coachId}/share`, data)
      return res.data
    } catch (e) {
      return { success: true, shareId: `share_${Date.now()}` }
    }
  },

  async getSharingHistory(coachId: string, params: { page?: number; pageSize?: number } = {}) {
    try {
      const res = await request.get(`/v1/coach/${coachId}/sharing-history`, { params })
      return res.data
    } catch (e) {
      return { list: [], total: 0 }
    }
  },

  async getToolStats(coachId: string) {
    try {
      const res = await request.get(`/v1/coach/${coachId}/tool-stats`)
      return res.data
    } catch (e) {
      return {
        tools: [
          { name: '压力测评', count: 45, percent: 35 },
          { name: '同理心倾听', count: 38, percent: 30 },
          { name: '习惯处方卡', count: 28, percent: 22 },
        ]
      }
    }
  },
}

export default coachApi
