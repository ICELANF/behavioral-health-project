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
   * SSE 实时处方流 - 使用 fetch + ReadableStream (不暴露 JWT 到 URL)
   * 返回 AbortController 供调用方取消连接
   */
  streamPrescription(
    userId: string,
    onMessage: (event: { type: string; data: string }) => void,
    onError?: (err: Error) => void
  ): AbortController | null {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    const token = localStorage.getItem('admin_token')
    const controller = new AbortController()

    fetch(`${baseUrl}/v1/copilot/stream/${userId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token || ''}`,
        'Accept': 'text/event-stream',
      },
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok || !response.body) {
          throw new Error(`SSE connection failed: ${response.status}`)
        }
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          let eventType = 'message'
          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.slice(6).trim()
            } else if (line.startsWith('data:')) {
              onMessage({ type: eventType, data: line.slice(5).trim() })
              eventType = 'message'
            }
          }
        }
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          onError?.(err)
        }
      })

    return controller
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
