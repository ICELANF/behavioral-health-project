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

// ── Flywheel API (r6_coach_flywheel_api_live.py) ──

export interface CoachStatsToday {
  todayReviewed: number
  approved: number
  rejected: number
  pendingCount: number
  avgSeconds: number
  streakDays: number
}

export interface ReviewQueueItem {
  id: string
  name: string
  studentId: number
  type: string
  priority: string
  status: string
  aiSummary: string
  rxFields: any[] | null
  aiDraft: string | null
  pushType: string | null
  pushContent: string | null
  createdAt: string
  waitTime: string
  stage: string
  level: string
  bptType: string
  streakDays: number
  riskLevel: string
  typeLabel: string
}

function mapStatsToday(raw: any): CoachStatsToday {
  return {
    todayReviewed: raw.total_reviewed ?? 0,
    approved: raw.approved ?? 0,
    rejected: raw.rejected ?? 0,
    pendingCount: raw.pending ?? 0,
    avgSeconds: raw.avg_review_seconds ?? 0,
    streakDays: raw.streak_days ?? 0,
  }
}

function formatWaitTime(waitSeconds: number): string {
  if (waitSeconds < 60) return `${waitSeconds}秒前`
  if (waitSeconds < 3600) return `${Math.floor(waitSeconds / 60)}分钟前`
  return `${Math.floor(waitSeconds / 3600)}小时前`
}

const typeLabels: Record<string, string> = {
  prescription: '行为处方',
  ai_reply: 'AI回复审核',
  push: '推送审核',
}

function mapReviewItem(raw: any): ReviewQueueItem {
  return {
    id: raw.id,
    name: raw.student_name ?? '未知',
    studentId: raw.student_id,
    type: raw.type ?? 'prescription',
    priority: raw.priority ?? 'normal',
    status: raw.status ?? 'pending',
    aiSummary: raw.ai_summary ?? '',
    rxFields: raw.rx_fields,
    aiDraft: raw.ai_draft,
    pushType: raw.push_type,
    pushContent: raw.push_content,
    createdAt: raw.created_at ?? '',
    waitTime: formatWaitTime(raw.wait_seconds ?? 0),
    stage: raw.stage ?? '',
    level: raw.level ?? '',
    bptType: raw.bpt_type ?? '',
    streakDays: raw.streak_days ?? 0,
    riskLevel: raw.risk_level ?? 'low',
    typeLabel: typeLabels[raw.type] || raw.type || '',
  }
}

export const coachFlywheelApi = {
  async getStatsToday(): Promise<CoachStatsToday> {
    const res = await request.get('/v1/coach/stats/today')
    return mapStatsToday(res.data)
  },

  async getReviewQueue(params: { status?: string; limit?: number } = {}): Promise<{
    items: ReviewQueueItem[]
    totalPending: number
    urgentCount: number
  }> {
    const res = await request.get('/v1/coach/review-queue', { params })
    return {
      items: (res.data.items || []).map(mapReviewItem),
      totalPending: res.data.total_pending ?? 0,
      urgentCount: res.data.urgent_count ?? 0,
    }
  },

  async approveReview(reviewId: string, data?: { review_note?: string; edited_content?: string; edited_rx_json?: any }) {
    const res = await request.post(`/v1/coach/review/${reviewId}/approve`, data)
    return res.data
  },

  async rejectReview(reviewId: string, data: { reason: string; review_note?: string }) {
    const res = await request.post(`/v1/coach/review/${reviewId}/reject`, data)
    return res.data
  },
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
