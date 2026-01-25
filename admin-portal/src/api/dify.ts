/**
 * Dify API 客户端 - 对接 AI Agent
 */

// Dify 配置 (需要在 Dify 控制台创建应用后获取)
const DIFY_CONFIG = {
  // Dify API 基础地址
  baseUrl: import.meta.env.VITE_DIFY_API_URL || 'http://localhost/v1',
  // 应用 API Key (从 Dify 应用设置中获取)
  apiKey: import.meta.env.VITE_DIFY_API_KEY || '',
}

// ============ 类型定义 ============

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface ChatResponse {
  message_id: string
  conversation_id: string
  answer: string
  created_at: number
  metadata?: {
    usage?: {
      prompt_tokens: number
      completion_tokens: number
      total_tokens: number
    }
  }
}

export interface StreamChunk {
  event: 'message' | 'message_end' | 'error' | 'ping'
  message_id?: string
  conversation_id?: string
  answer?: string
  created_at?: number
}

export interface ConversationInfo {
  id: string
  name: string
  inputs: Record<string, unknown>
  status: string
  introduction: string
  created_at: number
  updated_at: number
}

// ============ API 函数 ============

/**
 * 检查 Dify 配置是否完整
 */
export function isDifyConfigured(): boolean {
  return !!DIFY_CONFIG.apiKey && DIFY_CONFIG.apiKey !== ''
}

/**
 * 发送聊天消息 (阻塞模式)
 */
export async function sendMessage(
  query: string,
  userId: string,
  conversationId?: string,
  inputs?: Record<string, unknown>
): Promise<ChatResponse> {
  if (!isDifyConfigured()) {
    throw new Error('Dify API Key 未配置')
  }

  const response = await fetch(`${DIFY_CONFIG.baseUrl}/chat-messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${DIFY_CONFIG.apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      inputs: inputs || {},
      query,
      response_mode: 'blocking',
      conversation_id: conversationId,
      user: userId,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || '请求失败')
  }

  return response.json()
}

/**
 * 发送聊天消息 (流式模式)
 */
export async function* sendMessageStream(
  query: string,
  userId: string,
  conversationId?: string,
  inputs?: Record<string, unknown>
): AsyncGenerator<StreamChunk> {
  if (!isDifyConfigured()) {
    throw new Error('Dify API Key 未配置')
  }

  const response = await fetch(`${DIFY_CONFIG.baseUrl}/chat-messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${DIFY_CONFIG.apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      inputs: inputs || {},
      query,
      response_mode: 'streaming',
      conversation_id: conversationId,
      user: userId,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || '请求失败')
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('无法读取响应流')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') return

        try {
          const chunk: StreamChunk = JSON.parse(data)
          yield chunk
        } catch {
          // 忽略解析错误
        }
      }
    }
  }
}

/**
 * 获取会话列表
 */
export async function getConversations(
  userId: string,
  limit = 20,
  lastId?: string
): Promise<{ data: ConversationInfo[]; has_more: boolean }> {
  if (!isDifyConfigured()) {
    throw new Error('Dify API Key 未配置')
  }

  const params = new URLSearchParams({
    user: userId,
    limit: String(limit),
  })
  if (lastId) {
    params.append('last_id', lastId)
  }

  const response = await fetch(
    `${DIFY_CONFIG.baseUrl}/conversations?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${DIFY_CONFIG.apiKey}`,
      },
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || '获取会话列表失败')
  }

  return response.json()
}

/**
 * 获取会话消息历史
 */
export async function getConversationMessages(
  conversationId: string,
  userId: string,
  limit = 20,
  firstId?: string
): Promise<{ data: ChatMessage[]; has_more: boolean }> {
  if (!isDifyConfigured()) {
    throw new Error('Dify API Key 未配置')
  }

  const params = new URLSearchParams({
    user: userId,
    limit: String(limit),
    conversation_id: conversationId,
  })
  if (firstId) {
    params.append('first_id', firstId)
  }

  const response = await fetch(
    `${DIFY_CONFIG.baseUrl}/messages?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${DIFY_CONFIG.apiKey}`,
      },
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || '获取消息历史失败')
  }

  return response.json()
}

/**
 * 删除会话
 */
export async function deleteConversation(
  conversationId: string,
  userId: string
): Promise<void> {
  if (!isDifyConfigured()) {
    throw new Error('Dify API Key 未配置')
  }

  const response = await fetch(
    `${DIFY_CONFIG.baseUrl}/conversations/${conversationId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${DIFY_CONFIG.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user: userId }),
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || '删除会话失败')
  }
}

/**
 * 重命名会话
 */
export async function renameConversation(
  conversationId: string,
  name: string,
  userId: string
): Promise<void> {
  if (!isDifyConfigured()) {
    throw new Error('Dify API Key 未配置')
  }

  const response = await fetch(
    `${DIFY_CONFIG.baseUrl}/conversations/${conversationId}/name`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DIFY_CONFIG.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, user: userId }),
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || '重命名失败')
  }
}

/**
 * 消息反馈 (点赞/点踩)
 */
export async function feedbackMessage(
  messageId: string,
  rating: 'like' | 'dislike' | null,
  userId: string,
  content?: string
): Promise<void> {
  if (!isDifyConfigured()) {
    throw new Error('Dify API Key 未配置')
  }

  const response = await fetch(
    `${DIFY_CONFIG.baseUrl}/messages/${messageId}/feedbacks`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DIFY_CONFIG.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        rating,
        user: userId,
        content,
      }),
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || '反馈提交失败')
  }
}

// ============ 行为健康专用函数 ============

/**
 * 健康咨询对话
 * @param message 用户消息
 * @param userId 用户ID
 * @param context 用户健康上下文
 * @param conversationId 会话ID (可选，用于继续对话)
 */
export async function healthConsult(
  message: string,
  userId: string,
  context?: {
    stage?: string
    focusAreas?: string[]
    recentGlucose?: number
    medications?: string[]
  },
  conversationId?: string
): Promise<ChatResponse> {
  const inputs: Record<string, unknown> = {}

  if (context) {
    if (context.stage) inputs.behavior_stage = context.stage
    if (context.focusAreas) inputs.focus_areas = context.focusAreas.join(',')
    if (context.recentGlucose) inputs.recent_glucose = context.recentGlucose
    if (context.medications) inputs.medications = context.medications.join(',')
  }

  return sendMessage(message, userId, conversationId, inputs)
}

/**
 * 健康咨询对话 (流式)
 */
export async function* healthConsultStream(
  message: string,
  userId: string,
  context?: {
    stage?: string
    focusAreas?: string[]
    recentGlucose?: number
    medications?: string[]
  },
  conversationId?: string
): AsyncGenerator<StreamChunk> {
  const inputs: Record<string, unknown> = {}

  if (context) {
    if (context.stage) inputs.behavior_stage = context.stage
    if (context.focusAreas) inputs.focus_areas = context.focusAreas.join(',')
    if (context.recentGlucose) inputs.recent_glucose = context.recentGlucose
    if (context.medications) inputs.medications = context.medications.join(',')
  }

  yield* sendMessageStream(message, userId, conversationId, inputs)
}
