import api from './index'
import type { ChatRequest, ChatResponse, Expert } from './types'

export const chatApi = {
  // 发送消息
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return api.post('/api/v1/dispatch', request)
  },

  // 匿名体验聊天 (无需 JWT, 每日 10 次)
  async sendTrialMessage(message: string, sessionId?: string) {
    return api.post('/api/v1/chat/trial', { message, session_id: sessionId })
  },

  // 发送短信验证码 (公开端点)
  async sendSmsCode(phone: string) {
    return api.post('/api/v1/auth/send-sms-code', { phone })
  },

  // 验证码登录
  async smsLogin(phone: string, code: string) {
    return api.post('/api/v1/auth/sms-login', { phone, code })
  },

  // 获取专家列表
  async getExperts(): Promise<Expert[]> {
    return api.get('/api/v1/experts')
  },

  // 任务分解
  async decomposeTasks(message: string, efficacy_score: number) {
    return api.post('/api/v1/decompose', {
      message,
      efficacy_score
    })
  },

  // 效能限幅
  async clampTasks(user_id: string, efficacy_score: number, tasks: any[], wearable_data?: any) {
    return api.post('/api/v1/clamping', {
      user_id,
      efficacy_score,
      tasks,
      wearable_data
    })
  }
}

export default chatApi
