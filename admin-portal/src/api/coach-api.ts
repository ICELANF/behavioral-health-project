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
  async getPerformance(_coachId: string, params: { startDate?: string; endDate?: string } = {}) {
    const res = await request.get('/v1/coach/performance', { params })
    return res.data
  },

  async getCertification(_coachId: string) {
    const res = await request.get('/v1/coach/my-certification')
    return res.data
  },

  async applyPromotion(_coachId: string) {
    const res = await request.post('/v1/promotion/apply')
    return res.data
  },

  async getStudents(_coachId: string) {
    const res = await request.get('/v1/coach/students')
    return res.data
  },

  async shareContent(_coachId: string, data: { contentId: string; contentType: string; studentIds: string[]; message: string; sendMode: string; scheduledTime?: string }) {
    const res = await request.post('/v1/coach/share', data)
    return res.data
  },

  async getSharingHistory(_coachId: string, params: { page?: number; pageSize?: number } = {}) {
    const res = await request.get('/v1/coach/sharing-history', { params })
    return res.data
  },

  async getToolStats(_coachId: string) {
    const res = await request.get('/v1/coach/my-tools-stats')
    return res.data
  },
}

export default coachApi
