/**
 * Admin 飞轮指挥中心 API (admin_flywheel_api.py)
 * 9 GET + 1 POST = 10 endpoints
 */
import request from './request'

// ── Types ──

export interface CoreKPI {
  icon: string; value: string; label: string; sub: string
  trendDir: string; trendPct: number; status: string
}

export interface ChannelHealth {
  icon: string; name: string; status: string; statusLabel: string
  dau: string; msgToday: string; avgReply: string; errorRate?: number
}

export interface FunnelStep {
  label: string; count: string; pct: number; color: string; convRate?: string
}

export interface AgentGroup {
  name: string
  agents: Array<{ id: string; name: string; status: string; statusLabel: string }>
}

export interface AgentPerf {
  name: string; agentId?: string; p95: number; avg?: number; calls?: number
}

export interface CoachRank {
  name: string; coachId?: string; students: number
  todayReviewed: number; avgSeconds: number; approvalRate?: number
}

export interface SafetyMetric {
  rule: string; label: string; count: number; lastTriggered?: string
}

export interface ActiveAlert {
  id: string; level: string; message: string; source?: string
  time: string; autoResolved?: boolean
}

// ── Mappers ──

function mapKpi(raw: any): CoreKPI {
  return {
    icon: raw.icon ?? '', value: String(raw.value ?? ''),
    label: raw.label ?? '', sub: raw.sub ?? '',
    trendDir: raw.trend_dir ?? 'flat', trendPct: raw.trend_pct ?? 0,
    status: raw.status ?? 'good',
  }
}

function mapChannel(raw: any): ChannelHealth {
  return {
    icon: raw.icon ?? '', name: raw.name ?? '',
    status: raw.status ?? 'healthy', statusLabel: raw.status_label ?? '',
    dau: String(raw.dau ?? 0), msgToday: String(raw.msg_today ?? 0),
    avgReply: String(raw.avg_reply ?? ''), errorRate: raw.error_rate,
  }
}

function mapFunnel(raw: any): FunnelStep {
  return {
    label: raw.label ?? '', count: String(raw.count ?? 0),
    pct: raw.pct ?? 0, color: raw.color ?? '#3b82f6',
    convRate: raw.conv_rate != null ? String(raw.conv_rate) : undefined,
  }
}

function mapAgentStatus(raw: any): { id: string; name: string; layer: string; status: string; statusLabel: string; p95Ms: number; callsToday: number; errorRate: number } {
  return {
    id: raw.id ?? '', name: raw.name ?? '', layer: raw.layer ?? '',
    status: raw.status ?? 'ok', statusLabel: raw.status_label ?? '正常',
    p95Ms: raw.p95_ms ?? 0, callsToday: raw.calls_today ?? 0,
    errorRate: raw.error_rate ?? 0,
  }
}

function mapCoach(raw: any): CoachRank {
  return {
    name: raw.name ?? '', coachId: raw.coach_id,
    students: raw.students ?? 0, todayReviewed: raw.today_reviewed ?? 0,
    avgSeconds: raw.avg_seconds ?? 0, approvalRate: raw.approval_rate,
  }
}

function mapSafety(raw: any): SafetyMetric {
  return {
    rule: raw.rule ?? '', label: raw.label ?? '',
    count: raw.count ?? 0, lastTriggered: raw.last_triggered,
  }
}

function mapAlert(raw: any): ActiveAlert {
  return {
    id: raw.id ?? '', level: raw.level ?? 'info',
    message: raw.message ?? '', source: raw.source,
    time: raw.time ?? '', autoResolved: raw.auto_resolved,
  }
}

// ── API ──

export const adminFlywheelApi = {
  async getKpiRealtime(): Promise<CoreKPI[]> {
    const res = await request.get('/v1/admin/kpi/realtime')
    return (Array.isArray(res.data) ? res.data : []).map(mapKpi)
  },

  async getChannelsHealth(): Promise<ChannelHealth[]> {
    const res = await request.get('/v1/admin/channels/health')
    return (Array.isArray(res.data) ? res.data : []).map(mapChannel)
  },

  async getFunnel(): Promise<FunnelStep[]> {
    const res = await request.get('/v1/admin/funnel')
    return (Array.isArray(res.data) ? res.data : []).map(mapFunnel)
  },

  async getAgentsMonitor(): Promise<AgentGroup[]> {
    const res = await request.get('/v1/admin/agents/monitor')
    const rawList = Array.isArray(res.data) ? res.data : []
    // Group by layer
    const layerMap: Record<string, any[]> = {}
    for (const a of rawList.map(mapAgentStatus)) {
      const layer = a.layer || '其他'
      if (!layerMap[layer]) layerMap[layer] = []
      layerMap[layer].push({ id: a.id, name: a.name, status: a.status, statusLabel: a.statusLabel })
    }
    return Object.entries(layerMap).map(([name, agents]) => ({ name, agents }))
  },

  async getAgentsPerformance(topN = 5): Promise<AgentPerf[]> {
    const res = await request.get('/v1/admin/agents/performance', { params: { top_n: topN } })
    return (Array.isArray(res.data) ? res.data : []).map((raw: any) => ({
      name: raw.name ?? '', agentId: raw.agent_id, p95: raw.p95 ?? 0,
      avg: raw.avg, calls: raw.calls,
    }))
  },

  async getCoachesRanking(): Promise<CoachRank[]> {
    const res = await request.get('/v1/admin/coaches/ranking')
    return (Array.isArray(res.data) ? res.data : []).map(mapCoach)
  },

  async getSafety24h(): Promise<SafetyMetric[]> {
    const res = await request.get('/v1/admin/safety/24h')
    return (Array.isArray(res.data) ? res.data : []).map(mapSafety)
  },

  async getActiveAlerts(): Promise<ActiveAlert[]> {
    const res = await request.get('/v1/admin/alerts/active')
    return (Array.isArray(res.data) ? res.data : []).map(mapAlert)
  },

  async dismissAlert(alertId: string): Promise<{ success: boolean }> {
    const res = await request.post(`/v1/admin/alerts/${alertId}/dismiss`)
    return { success: res.data?.success ?? true }
  },
}

export default adminFlywheelApi
