import request from './request'

export interface SupervisedCoach {
  id: string
  name: string
  level: string
  studentCount: number
  successRate: number
  retention: number
  score: number
}

export interface ReviewItem {
  id: string
  type: 'promotion' | 'content' | 'case'
  title: string
  description: string
  submitter: string
  submitDate: string
  urgency: 'normal' | 'high'
}

export interface ResearchQuery {
  dimension: string
  dateRange?: [string, string]
  groupBy?: string
}

export interface ResearchResult {
  data: Array<{ category: string; count: number; percent: number }>
  summary: { total: number; avg: number; stdDev: number; median: number }
}

// Mock data
const mockCoaches: SupervisedCoach[] = [
  { id: '1', name: '王教练', level: 'L2 中级', studentCount: 15, successRate: 74, retention: 88, score: 4.5 },
  { id: '2', name: '李教练', level: 'L1 初级', studentCount: 8, successRate: 62, retention: 80, score: 3.8 },
  { id: '3', name: '张教练', level: 'L2 中级', studentCount: 12, successRate: 78, retention: 90, score: 4.2 },
]

const mockReviewQueue: ReviewItem[] = [
  { id: '1', type: 'promotion', title: '王教练申请L3晋级', description: '已完成所有必修课程', submitter: '王教练', submitDate: '2025-01-14', urgency: 'normal' },
  { id: '2', type: 'content', title: '《慢病自我管理》课程审核', description: '新增4个章节', submitter: '张专家', submitDate: '2025-01-13', urgency: 'normal' },
  { id: '3', type: 'case', title: '高风险案例复核', description: '患者连续5天未活跃', submitter: '李教练', submitDate: '2025-01-12', urgency: 'high' },
]

// ── Flywheel API (expert_flywheel_api.py) ──

export interface ExpertQualityMetrics {
  todayAudited: number
  passRate: number
  pendingQueue: number
  redlineBlocked: number
  agentAnomalyCount: number
  byType: Record<string, number>
  trend7d: any[]
}

export interface ExpertAuditItem {
  id: string; title: string; type: string; typeIcon: string
  agent: string; userName: string; userStage: string
  risk: string; time: string
  dialogue?: any[]; safetyFlags: any[]
  rxFields?: any[]; evidenceLevel?: number
  decisionSteps?: any[]; history: any[]
}

export interface AgentAnomaly {
  agentId: string; agentName: string; anomalyType: string
  severity: string; description: string; sampleCount: number
  firstSeen: string; lastSeen: string
}

function mapMetrics(raw: any): ExpertQualityMetrics {
  return {
    todayAudited: raw.today_audited ?? 0,
    passRate: raw.pass_rate ?? 0,
    pendingQueue: raw.pending_queue ?? 0,
    redlineBlocked: raw.redline_blocked ?? 0,
    agentAnomalyCount: raw.agent_anomaly_count ?? 0,
    byType: raw.by_type ?? {},
    trend7d: raw.trend_7d ?? [],
  }
}

function mapAuditItem(raw: any): ExpertAuditItem {
  return {
    id: raw.id, title: raw.title, type: raw.type,
    typeIcon: raw.type_icon ?? '', agent: raw.agent ?? '',
    userName: raw.user_name ?? '', userStage: raw.user_stage ?? '',
    risk: raw.risk ?? 'low', time: raw.time ?? '',
    dialogue: raw.dialogue,
    safetyFlags: (raw.safety_flags || []).map((f: any) => ({
      rule: f.rule, description: f.description, action: f.action,
    })),
    rxFields: (raw.rx_fields || []).map((f: any) => ({
      key: f.key, label: f.label, value: f.value,
      flagged: f.flagged ?? false, flagReason: f.flag_reason,
    })),
    evidenceLevel: raw.evidence_level,
    decisionSteps: raw.decision_steps,
    history: raw.history ?? [],
  }
}

function mapAnomaly(raw: any): AgentAnomaly {
  return {
    agentId: raw.agent_id, agentName: raw.agent_name,
    anomalyType: raw.anomaly_type, severity: raw.severity,
    description: raw.description, sampleCount: raw.sample_count ?? 0,
    firstSeen: raw.first_seen ?? '', lastSeen: raw.last_seen ?? '',
  }
}

export const expertFlywheelApi = {
  async getQualityMetrics(): Promise<ExpertQualityMetrics> {
    const res = await request.get('/v1/expert/quality-metrics')
    return mapMetrics(res.data)
  },

  async getAuditQueue(filters: { type_filter?: string; risk_filter?: string; agent_filter?: string } = {}): Promise<{
    items: ExpertAuditItem[]
    total: number
    byType: Record<string, number>
    byRisk: Record<string, number>
  }> {
    const res = await request.get('/v1/expert/audit-queue', { params: filters })
    return {
      items: (res.data.items || []).map(mapAuditItem),
      total: res.data.total ?? 0,
      byType: res.data.by_type ?? {},
      byRisk: res.data.by_risk ?? {},
    }
  },

  async submitVerdict(auditId: string, data: { verdict: string; score: number; issues: string[]; note: string }): Promise<{
    success: boolean; auditId: string; verdict: string; nextId?: string; message: string
  }> {
    const res = await request.post(`/v1/expert/audit/${auditId}/verdict`, data)
    return {
      success: res.data.success,
      auditId: res.data.audit_id,
      verdict: res.data.verdict,
      nextId: res.data.next_id,
      message: res.data.message ?? '',
    }
  },

  async getAgentAnomalies(): Promise<AgentAnomaly[]> {
    const res = await request.get('/v1/expert/agent-anomalies')
    return (Array.isArray(res.data) ? res.data : []).map(mapAnomaly)
  },
}

export const expertApi = {
  async getSupervisedCoaches(expertId: string) {
    try {
      const res = await request.get(`/v1/expert/${expertId}/coaches`)
      return res.data
    } catch (e) {
      return { coaches: mockCoaches }
    }
  },

  async getReviewQueue(expertId: string) {
    try {
      const res = await request.get(`/v1/expert/${expertId}/reviews/pending`)
      return res.data
    } catch (e) {
      return { items: mockReviewQueue }
    }
  },

  async submitReview(reviewId: string, decision: { approved: boolean; comment: string }) {
    try {
      const res = await request.post(`/v1/expert/reviews/${reviewId}/decide`, decision)
      return res.data
    } catch (e) {
      return { success: true }
    }
  },

  async getReviewHistory(expertId: string, params: { page?: number; pageSize?: number } = {}) {
    try {
      const res = await request.get(`/v1/expert/${expertId}/reviews/history`, { params })
      return res.data
    } catch (e) {
      return { list: [], total: 0 }
    }
  },

  async scheduleSupervision(expertId: string, data: { coachId: string; topic: string; date: string; notes?: string }) {
    try {
      const res = await request.post(`/v1/expert/${expertId}/supervision/schedule`, data)
      return res.data
    } catch (e) {
      return { success: true, sessionId: `ss_${Date.now()}` }
    }
  },

  async getSupervisionSessions(expertId: string) {
    try {
      const res = await request.get(`/v1/expert/${expertId}/supervision/sessions`)
      return res.data
    } catch (e) {
      return {
        sessions: [
          { id: '1', coach: '李教练', status: '已完成', date: '2025-01-14 14:00', topic: '低成功率案例复盘' },
          { id: '2', coach: '王教练', status: '待进行', date: '2025-01-18 14:00', topic: 'L3晋级准备指导' },
        ]
      }
    }
  },

  async queryResearchData(query: ResearchQuery) {
    try {
      const res = await request.post('/v1/expert/research/query', query)
      return res.data
    } catch (e) {
      return {
        data: [
          { category: '前思考期', count: 186, percent: 14.9 },
          { category: '思考期', count: 312, percent: 25.0 },
          { category: '准备期', count: 268, percent: 21.5 },
          { category: '行动期', count: 298, percent: 23.9 },
          { category: '维持期', count: 152, percent: 12.2 },
          { category: '终止期', count: 32, percent: 2.5 },
        ],
        summary: { total: 1248, avg: 208, stdDev: 89.45, median: 275 },
      }
    }
  },

  async exportResearchData(query: ResearchQuery, format: 'csv' | 'excel') {
    try {
      const res = await request.post('/v1/expert/research/export', { ...query, format }, { responseType: 'blob' })
      return res.data
    } catch (e) {
      return null
    }
  },
}

export default expertApi
