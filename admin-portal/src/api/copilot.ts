import request from './request'

export interface CopilotAnalyzeParams {
  uid: string
  message: string
  context?: {
    stage?: string
    baps?: Record<string, any>
  }
}

export interface CopilotPrescription {
  risk_level: string
  instruction: string
  suggested_tool: string
  tool_props: Record<string, any>
}

export interface CopilotAnalyzeResult {
  status: string
  source: string
  analysis: Array<{
    tag: string
    label: string
    source: string
  }>
  triggered_tags: string[]
  outputs: {
    to_patient: { content: string }
    to_coach: CopilotPrescription[]
  }
}

export interface PrescriptionHistoryParams {
  page?: number
  pageSize?: number
  startDate?: string
  endDate?: string
  riskLevel?: string
}

export interface PrescriptionHistoryItem {
  id: string
  risk_level: string
  instruction: string
  suggested_tool: string
  created_at: string
  adopted: boolean
  ignored: boolean
  tool_action?: string
}

export interface ToolActionPayload {
  action: string
  tool?: string
  instruction?: string
  data?: Record<string, any>
}

export interface SuggestedAction {
  id: string
  label: string
  description: string
  tool: string
  priority: number
  context_match: string[]
}

export const copilotApi = {
  /**
   * 调用 CoachCopilot 分析端点 (生产 8002)
   */
  analyze(params: CopilotAnalyzeParams) {
    return request.post<CopilotAnalyzeResult>('/v1/copilot/analyze', params)
  },

  /**
   * SSE 实时处方流 - 连接到后端 SSE 端点接收实时处方推送
   */
  streamPrescription(userId: string): EventSource | null {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api'
    const token = localStorage.getItem('admin_token')
    try {
      const url = `${baseUrl}/v1/copilot/stream/${userId}?token=${token || ''}`
      const es = new EventSource(url)
      return es
    } catch (e) {
      console.warn('[Copilot] SSE connection failed, falling back to mock mode')
      return null
    }
  },

  /**
   * 获取历史处方列表
   */
  async getPrescriptionHistory(coachId: string, params: PrescriptionHistoryParams = {}) {
    const res = await request.get(`/v1/copilot/prescriptions/${coachId}`, { params })
    return res.data
  },

  async submitToolAction(prescriptionId: string, action: ToolActionPayload) {
    const res = await request.post(`/v1/copilot/prescriptions/${prescriptionId}/action`, action)
    return res.data
  },

  async getSuggestedActions(context: { stage?: string; risk_level?: string; recent_tags?: string[] } = {}) {
    const res = await request.post('/v1/copilot/suggested-actions', context)
    return res.data
  },
}

export default copilotApi
