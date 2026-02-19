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
    const res = await request.get(`/v1/expert/${expertId}/coaches`)
    return res.data
  },

  async getReviewQueue(expertId: string) {
    const res = await request.get(`/v1/expert/${expertId}/reviews/pending`)
    return res.data
  },

  async submitReview(reviewId: string, decision: { approved: boolean; comment: string }) {
    const res = await request.post(`/v1/expert/reviews/${reviewId}/decide`, decision)
    return res.data
  },

  async getReviewHistory(expertId: string, params: { page?: number; pageSize?: number } = {}) {
    const res = await request.get(`/v1/expert/${expertId}/reviews/history`, { params })
    return res.data
  },

  async scheduleSupervision(expertId: string, data: { coachId: string; topic: string; date: string; notes?: string }) {
    const res = await request.post(`/v1/expert/${expertId}/supervision/schedule`, data)
    return res.data
  },

  async getSupervisionSessions(expertId: string) {
    const res = await request.get(`/v1/expert/${expertId}/supervision/sessions`)
    return res.data
  },

  async queryResearchData(query: ResearchQuery) {
    const res = await request.post('/v1/expert/research/query', query)
    return res.data
  },

  async exportResearchData(query: ResearchQuery, format: 'csv' | 'excel') {
    const res = await request.post('/v1/expert/research/export', { ...query, format }, { responseType: 'blob' })
    return res.data
  },
}

export default expertApi
