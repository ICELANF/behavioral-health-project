import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatAPI, type ChatMessage, type LLMHealth, type ChatSessionInfo } from '@/api/chat'
import { showToast } from 'vant'
import { storage } from '@/utils/storage'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<ChatMessage[]>([])
  const sessionId = ref<string>('')
  const loading = ref(false)
  const llmHealth = ref<LLMHealth | null>(null)
  const streamingContent = ref('')
  const sessions = ref<ChatSessionInfo[]>([])

  // Getters
  const hasMessages = computed(() => messages.value.length > 0)
  const isLLMAvailable = computed(() =>
    llmHealth.value?.status === 'healthy' && llmHealth.value?.model_available
  )
  const currentModel = computed(() => llmHealth.value?.current_model || 'unknown')

  // Actions

  /**
   * 生成消息ID
   */
  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  /**
   * 检查 LLM 健康状态
   */
  const checkLLMHealth = async () => {
    try {
      llmHealth.value = await chatAPI.checkHealth()
      return llmHealth.value
    } catch (error) {
      console.error('Check LLM health failed:', error)
      llmHealth.value = {
        status: 'error',
        models: [],
        model_available: false,
        current_model: 'unknown',
        message: '无法连接到AI服务'
      }
      return llmHealth.value
    }
  }

  /**
   * 添加用户消息
   */
  const addUserMessage = (content: string) => {
    const message: ChatMessage = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    }
    messages.value.push(message)
    return message
  }

  /**
   * 添加助手消息
   */
  const addAssistantMessage = (content: string) => {
    const message: ChatMessage = {
      id: generateId(),
      role: 'assistant',
      content,
      timestamp: new Date().toISOString()
    }
    messages.value.push(message)
    return message
  }

  /**
   * 发送消息并获取回复
   */
  const sendMessage = async (content: string) => {
    if (!content.trim()) return

    // 添加用户消息
    addUserMessage(content)

    loading.value = true
    try {
      const response = await chatAPI.send({
        message: content,
        session_id: sessionId.value || undefined
      })

      // 更新 session ID 并保存到本地
      if (response.session_id) {
        sessionId.value = response.session_id
        saveSessionId()
      }

      // 添加助手回复
      addAssistantMessage(response.message)

      return response
    } catch (error: any) {
      console.error('Send message failed:', error)

      // 添加错误消息
      addAssistantMessage('抱歉，消息发送失败。请稍后重试。')

      showToast('发送失败，请重试')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 发送快捷消息（建议选项）
   */
  const sendQuickMessage = async (suggestion: string) => {
    return sendMessage(suggestion)
  }

  /**
   * 流式发送消息（打字机效果）
   */
  const sendMessageStream = async (content: string): Promise<string> => {
    if (!content.trim()) return ''

    // 添加用户消息
    addUserMessage(content)

    loading.value = true
    streamingContent.value = ''

    // 创建一个占位的助手消息
    const assistantMsg: ChatMessage = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    }
    messages.value.push(assistantMsg)
    const msgIndex = messages.value.length - 1

    return new Promise((resolve, reject) => {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

      // 使用 fetch 发送 POST 请求获取 SSE 流
      fetch(`${baseUrl}/api/v1/mp/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': '1'
        },
        body: JSON.stringify({
          message: content,
          session_id: sessionId.value || undefined
        })
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }
          if (!response.body) {
            throw new Error('Response body is null')
          }

          const reader = response.body.getReader()
          const decoder = new TextDecoder()
          let fullContent = ''

          const read = (): Promise<void> => {
            return reader.read().then(({ done, value }) => {
              if (done) {
                loading.value = false
                streamingContent.value = ''
                resolve(fullContent)
                return
              }

              const chunk = decoder.decode(value, { stream: true })
              const lines = chunk.split('\n')

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const data = line.slice(6)

                  if (data === '[DONE]') {
                    loading.value = false
                    streamingContent.value = ''
                    resolve(fullContent)
                    return
                  }

                  // 累加内容
                  fullContent += data
                  streamingContent.value = fullContent

                  // 更新消息内容
                  if (messages.value[msgIndex]) {
                    messages.value[msgIndex].content = fullContent
                  }
                }
              }

              return read()
            })
          }

          return read()
        })
        .catch(error => {
          console.error('Stream error:', error)
          loading.value = false
          streamingContent.value = ''

          // 更新为错误消息
          if (messages.value[msgIndex]) {
            messages.value[msgIndex].content = '抱歉，消息发送失败。请稍后重试。'
          }

          showToast('发送失败，请重试')
          reject(error)
        })
    })
  }

  /**
   * 获取开场问候
   */
  const getGreeting = async (stage: string = 'ONBOARDING') => {
    loading.value = true
    try {
      const response = await chatAPI.agentRespond('start', stage)

      // 添加助手问候
      addAssistantMessage(response.message)

      return response
    } catch (error) {
      console.error('Get greeting failed:', error)
      // 使用默认问候
      addAssistantMessage('你好！我是你的健康小助手，有什么我可以帮助你的吗？')
    } finally {
      loading.value = false
    }
  }

  /**
   * 清空聊天记录
   */
  const clearMessages = () => {
    messages.value = []
    sessionId.value = ''
    streamingContent.value = ''
  }

  /**
   * 加载聊天历史
   */
  const loadHistory = async (sid?: string) => {
    const targetSession = sid || sessionId.value
    if (!targetSession) return

    try {
      const response = await chatAPI.getHistory(targetSession)
      if (response.messages && response.messages.length > 0) {
        // 转换为本地消息格式
        messages.value = response.messages.map(msg => ({
          id: msg.id,
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: msg.timestamp || new Date().toISOString()
        }))
        console.log(`[ChatStore] Loaded ${response.messages.length} messages from history`)
      }
    } catch (error) {
      console.log('[ChatStore] No history found or service unavailable')
    }
  }

  /**
   * 加载用户会话列表
   */
  const loadSessions = async () => {
    try {
      const response = await chatAPI.getSessions()
      sessions.value = response.sessions || []
      return sessions.value
    } catch (error) {
      console.log('[ChatStore] Failed to load sessions')
      return []
    }
  }

  /**
   * 恢复上次会话
   */
  const resumeLastSession = async () => {
    // 尝试从本地存储获取上次会话ID
    const lastSessionId = localStorage.getItem('lastChatSessionId')
    if (lastSessionId) {
      sessionId.value = lastSessionId
      await loadHistory(lastSessionId)
      return true
    }
    return false
  }

  /**
   * 保存当前会话ID到本地
   */
  const saveSessionId = () => {
    if (sessionId.value) {
      localStorage.setItem('lastChatSessionId', sessionId.value)
    }
  }

  /**
   * 初始化聊天
   */
  const initChat = async () => {
    // 检查 LLM 状态
    await checkLLMHealth()

    // 尝试恢复上次会话
    const resumed = await resumeLastSession()

    // 如果没有恢复历史记录，获取问候语
    if (!resumed || messages.value.length === 0) {
      await getGreeting()
    }
  }

  return {
    // State
    messages,
    sessionId,
    loading,
    llmHealth,
    streamingContent,
    sessions,

    // Getters
    hasMessages,
    isLLMAvailable,
    currentModel,

    // Actions
    checkLLMHealth,
    addUserMessage,
    addAssistantMessage,
    sendMessage,
    sendMessageStream,
    sendQuickMessage,
    getGreeting,
    clearMessages,
    initChat,
    loadHistory,
    loadSessions,
    resumeLastSession,
    saveSessionId
  }
})
