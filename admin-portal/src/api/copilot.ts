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

// Mock data generators
const mockPrescriptionHistory: PrescriptionHistoryItem[] = [
  { id: 'rx_001', risk_level: 'L2', instruction: '该用户近期情绪波动较大，建议启动压力快速评估，了解当前压力来源', suggested_tool: 'STRESS_ASSESSMENT_FORM', created_at: '2025-01-15 14:30:00', adopted: true, ignored: false, tool_action: 'start' },
  { id: 'rx_002', risk_level: 'L1', instruction: '用户处于前思考期(阻抗)，建议使用同理心倾听模式，不主动推送任务', suggested_tool: 'EMPATHY_MODULE_01', created_at: '2025-01-15 10:15:00', adopted: true, ignored: false, tool_action: 'start_listen' },
  { id: 'rx_003', risk_level: 'LOW', instruction: '用户表达了运动改变意愿，建议引导制定每日5分钟散步微习惯', suggested_tool: 'HABIT_DESIGNER', created_at: '2025-01-14 16:45:00', adopted: false, ignored: true },
  { id: 'rx_004', risk_level: 'L1', instruction: '用户提到睡眠质量下降，建议先通过开放式提问了解详情', suggested_tool: 'EMPATHY_MODULE_01', created_at: '2025-01-14 09:20:00', adopted: true, ignored: false },
  { id: 'rx_005', risk_level: 'L2', instruction: '用户自述暴饮暴食频率增加，建议紧急启动压力评估并通知督导', suggested_tool: 'STRESS_ASSESSMENT_FORM', created_at: '2025-01-13 15:30:00', adopted: true, ignored: false, tool_action: 'submit' },
]

const mockSuggestedActions: SuggestedAction[] = [
  { id: 'sa_001', label: '启动压力评估', description: '用户近期多次提到压力相关话题', tool: 'STRESS_ASSESSMENT_FORM', priority: 1, context_match: ['stress', 'anxiety', 'pressure'] },
  { id: 'sa_002', label: '进入倾听模式', description: '用户情绪低落，需要先建立信任关系', tool: 'EMPATHY_MODULE_01', priority: 2, context_match: ['sadness', 'resistance', 'avoidance'] },
  { id: 'sa_003', label: '制定微习惯', description: '用户已表达改变意愿，可引导具体行动', tool: 'HABIT_DESIGNER', priority: 3, context_match: ['motivation', 'willingness', 'action'] },
  { id: 'sa_004', label: '发送健康教育内容', description: '针对用户当前阶段推送相关科普内容', tool: 'GENERAL_CHAT', priority: 4, context_match: ['education', 'information', 'question'] },
]

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
    try {
      const res = await request.get(`/v1/copilot/prescriptions/${coachId}`, { params })
      return res.data
    } catch (e) {
      // Mock fallback
      const { page = 1, pageSize = 20 } = params
      const start = (page - 1) * pageSize
      const list = mockPrescriptionHistory.slice(start, start + pageSize)
      return { list, total: mockPrescriptionHistory.length, page, pageSize }
    }
  },

  /**
   * 工具执行结果上报 - 教练执行工具后回报结果
   */
  async submitToolAction(prescriptionId: string, action: ToolActionPayload) {
    try {
      const res = await request.post(`/v1/copilot/prescriptions/${prescriptionId}/action`, action)
      return res.data
    } catch (e) {
      // Mock fallback
      console.log('[Copilot] Tool action submitted (mock):', prescriptionId, action)
      return { success: true, prescriptionId, action: action.action }
    }
  },

  /**
   * 获取建议动作库 - 根据当前上下文获取推荐的教练动作
   */
  async getSuggestedActions(context: { stage?: string; risk_level?: string; recent_tags?: string[] } = {}) {
    try {
      const res = await request.post('/v1/copilot/suggested-actions', context)
      return res.data
    } catch (e) {
      // Mock fallback - filter by context
      let actions = [...mockSuggestedActions]
      if (context.risk_level === 'L2') {
        actions = actions.filter(a => a.priority <= 2)
      }
      return { actions }
    }
  },
}

export default copilotApi
