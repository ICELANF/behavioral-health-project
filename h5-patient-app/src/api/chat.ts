import request from './request'

/**
 * 聊天消息
 */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

/**
 * 聊天请求
 */
export interface ChatRequest {
  message: string
  session_id?: string
  stream?: boolean
}

/**
 * 聊天响应
 */
export interface ChatResponse {
  message: string
  session_id: string
  model: string
}

/**
 * LLM健康状态
 */
export interface LLMHealth {
  status: 'healthy' | 'unhealthy' | 'unavailable' | 'error'
  models: string[]
  model_available: boolean
  current_model: string
  message?: string
}

/**
 * Agent响应
 */
export interface AgentResponse {
  message: string
  explain?: string
  suggestions: string[]
  emotion: string
}

/**
 * 聊天历史消息
 */
export interface ChatHistoryItem {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

/**
 * 聊天会话信息
 */
export interface ChatSessionInfo {
  session_id: string
  message_count: number
  created_at: string
  updated_at: string
}

/**
 * 聊天 API
 */
export const chatAPI = {
  /**
   * 检查 LLM 服务健康状态
   */
  checkHealth(): Promise<LLMHealth> {
    return request.get('/api/v1/mp/llm/health')
  },

  /**
   * 发送聊天消息（非流式）
   */
  send(data: ChatRequest): Promise<ChatResponse> {
    return request.post('/api/v1/mp/chat', data, {
      timeout: 120000  // 2分钟超时，LLM 响应较慢
    })
  },

  /**
   * 发送 Agent 请求
   */
  agentRespond(event: string, stage: string, userInput?: string): Promise<AgentResponse> {
    return request.post('/api/v1/mp/agent/respond', {
      event,
      stage,
      user_input: userInput
    }, {
      timeout: 120000
    })
  },

  /**
   * 流式聊天（返回 EventSource URL）
   */
  getStreamUrl(): string {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    return `${baseUrl}/api/v1/mp/chat/stream`
  },

  /**
   * 获取聊天历史
   */
  getHistory(sessionId: string, limit: number = 50): Promise<{
    session_id: string
    messages: ChatHistoryItem[]
    total: number
  }> {
    return request.get(`/api/v1/mp/chat/history/${sessionId}`, {
      params: { limit },
      silentError: true  // 静默失败，避免弹出错误
    })
  },

  /**
   * 获取用户会话列表
   */
  getSessions(limit: number = 20): Promise<{
    sessions: ChatSessionInfo[]
    total: number
  }> {
    return request.get('/api/v1/mp/chat/sessions', {
      params: { limit },
      silentError: true
    })
  },

  /**
   * 删除会话
   */
  deleteSession(sessionId: string): Promise<{ success: boolean; message: string }> {
    return request.delete(`/api/v1/mp/chat/session/${sessionId}`)
  },

  /**
   * 清空所有历史
   */
  clearHistory(): Promise<{ success: boolean; message: string; cleared: number }> {
    return request.delete('/api/v1/mp/chat/history')
  }
}
