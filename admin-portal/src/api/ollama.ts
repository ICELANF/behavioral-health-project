/**
 * Ollama API 客户端 - 本地大模型对接
 * 使用 DeepSeek-R1 或 Qwen2.5 进行健康咨询
 */

// Ollama 配置
const OLLAMA_CONFIG = {
  baseUrl: import.meta.env.VITE_OLLAMA_URL || 'http://localhost:11434',
  model: import.meta.env.VITE_OLLAMA_MODEL || 'deepseek-r1:7b',
  // 备用模型
  fallbackModel: 'qwen2.5:14b',
}

// ============ 类型定义 ============

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface GenerateResponse {
  model: string
  created_at: string
  response: string
  done: boolean
  context?: number[]
  total_duration?: number
  load_duration?: number
  prompt_eval_count?: number
  prompt_eval_duration?: number
  eval_count?: number
  eval_duration?: number
}

export interface ChatResponse {
  model: string
  created_at: string
  message: ChatMessage
  done: boolean
  total_duration?: number
  eval_count?: number
}

export interface ModelInfo {
  name: string
  modified_at: string
  size: number
  digest: string
  details: {
    format: string
    family: string
    parameter_size: string
    quantization_level: string
  }
}

// ============ 系统提示词 ============

const HEALTH_COACH_SYSTEM_PROMPT = `# 角色定义
你是一名专业的行为健康教练，专注于糖尿病管理和慢性病行为干预。

## TTM 跨理论模型 - 行为改变阶段
1. **前意向期** - 无改变意愿，需要提升认知
2. **意向期** - 开始考虑改变，帮助评估利弊
3. **准备期** - 准备行动，帮助制定计划
4. **行动期** - 正在改变，提供支持鼓励
5. **维持期** - 已形成习惯，预防复发

## 关注领域
- 🩸 血糖管理：监测、解读、波动分析
- 🥗 饮食控制：低GI饮食、食物选择
- 🏃 运动锻炼：有氧运动、运动处方
- 💊 用药依从：服药提醒、药物知识
- 😴 睡眠质量：作息调整
- 🧘 压力管理：放松技巧
- ⚖️ 体重管理：减重策略

## 动机访谈原则
- 使用开放式问题引导对话
- 认可用户的努力和进步
- 反映式倾听，理解感受
- 不批判不说教，尊重自主性

## 安全提示
- 血糖>16.7或<3.9 mmol/L，建议立即就医
- 不提供具体药物调整建议
- 识别负面情绪，必要时建议专业支持

## 输出格式
- 回复简洁温暖，不超过200字
- 使用emoji增加亲和力
- 适时提出引导性问题`

// ============ API 函数 ============

/**
 * 检查 Ollama 服务是否可用
 */
export async function checkOllamaHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${OLLAMA_CONFIG.baseUrl}/api/tags`)
    return response.ok
  } catch {
    return false
  }
}

/**
 * 获取可用模型列表
 */
export async function getAvailableModels(): Promise<ModelInfo[]> {
  const response = await fetch(`${OLLAMA_CONFIG.baseUrl}/api/tags`)
  if (!response.ok) {
    throw new Error('获取模型列表失败')
  }
  const data = await response.json()
  return data.models || []
}

/**
 * 检查指定模型是否可用
 */
export async function isModelAvailable(modelName: string): Promise<boolean> {
  try {
    const models = await getAvailableModels()
    return models.some(m => m.name === modelName || m.name.startsWith(modelName.split(':')[0]))
  } catch {
    return false
  }
}

/**
 * 简单生成 (单轮对话)
 */
export async function generate(
  prompt: string,
  options?: {
    model?: string
    system?: string
    stream?: boolean
    context?: number[]
  }
): Promise<GenerateResponse> {
  const model = options?.model || OLLAMA_CONFIG.model

  const response = await fetch(`${OLLAMA_CONFIG.baseUrl}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      prompt,
      system: options?.system || HEALTH_COACH_SYSTEM_PROMPT,
      stream: options?.stream ?? false,
      context: options?.context,
      options: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 512,
      },
    }),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`生成失败: ${error}`)
  }

  return response.json()
}

/**
 * 流式生成
 */
export async function* generateStream(
  prompt: string,
  options?: {
    model?: string
    system?: string
    context?: number[]
  }
): AsyncGenerator<string> {
  const model = options?.model || OLLAMA_CONFIG.model

  const response = await fetch(`${OLLAMA_CONFIG.baseUrl}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      prompt,
      system: options?.system || HEALTH_COACH_SYSTEM_PROMPT,
      stream: true,
      context: options?.context,
      options: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 512,
      },
    }),
  })

  if (!response.ok) {
    throw new Error('生成失败')
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('无法读取响应流')

  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const text = decoder.decode(value, { stream: true })
    const lines = text.split('\n').filter(line => line.trim())

    for (const line of lines) {
      try {
        const data: GenerateResponse = JSON.parse(line)
        if (data.response) {
          yield data.response
        }
      } catch {
        // 忽略解析错误
      }
    }
  }
}

/**
 * 多轮对话 (Chat API)
 */
export async function chat(
  messages: ChatMessage[],
  options?: {
    model?: string
    stream?: boolean
  }
): Promise<ChatResponse> {
  const model = options?.model || OLLAMA_CONFIG.model

  // 添加系统提示词
  const messagesWithSystem: ChatMessage[] = [
    { role: 'system', content: HEALTH_COACH_SYSTEM_PROMPT },
    ...messages,
  ]

  const response = await fetch(`${OLLAMA_CONFIG.baseUrl}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      messages: messagesWithSystem,
      stream: options?.stream ?? false,
      options: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 512,
      },
    }),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`对话失败: ${error}`)
  }

  return response.json()
}

/**
 * 流式多轮对话
 */
export async function* chatStream(
  messages: ChatMessage[],
  options?: {
    model?: string
  }
): AsyncGenerator<string> {
  const model = options?.model || OLLAMA_CONFIG.model

  const messagesWithSystem: ChatMessage[] = [
    { role: 'system', content: HEALTH_COACH_SYSTEM_PROMPT },
    ...messages,
  ]

  const response = await fetch(`${OLLAMA_CONFIG.baseUrl}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      messages: messagesWithSystem,
      stream: true,
      options: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 512,
      },
    }),
  })

  if (!response.ok) {
    throw new Error('对话失败')
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('无法读取响应流')

  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const text = decoder.decode(value, { stream: true })
    const lines = text.split('\n').filter(line => line.trim())

    for (const line of lines) {
      try {
        const data: ChatResponse = JSON.parse(line)
        if (data.message?.content) {
          yield data.message.content
        }
      } catch {
        // 忽略解析错误
      }
    }
  }
}

// ============ 健康咨询专用函数 ============

/**
 * 健康咨询对话
 */
export async function healthConsult(
  userMessage: string,
  history: ChatMessage[] = [],
  context?: {
    stage?: string
    focusAreas?: string[]
    recentGlucose?: number
  }
): Promise<{ response: string; messages: ChatMessage[] }> {
  // 构建上下文增强的消息
  let enhancedMessage = userMessage

  if (context) {
    const contextParts: string[] = []
    if (context.stage) {
      contextParts.push(`[用户当前处于${context.stage}阶段]`)
    }
    if (context.focusAreas?.length) {
      contextParts.push(`[关注领域: ${context.focusAreas.join(', ')}]`)
    }
    if (context.recentGlucose) {
      contextParts.push(`[最近血糖: ${context.recentGlucose} mmol/L]`)
    }
    if (contextParts.length > 0) {
      enhancedMessage = `${contextParts.join(' ')}\n\n用户说: ${userMessage}`
    }
  }

  const messages: ChatMessage[] = [
    ...history,
    { role: 'user', content: enhancedMessage },
  ]

  const response = await chat(messages)

  return {
    response: response.message.content,
    messages: [
      ...history,
      { role: 'user', content: userMessage },
      { role: 'assistant', content: response.message.content },
    ],
  }
}

/**
 * 健康咨询对话 (流式)
 */
export async function* healthConsultStream(
  userMessage: string,
  history: ChatMessage[] = [],
  context?: {
    stage?: string
    focusAreas?: string[]
    recentGlucose?: number
  }
): AsyncGenerator<string> {
  let enhancedMessage = userMessage

  if (context) {
    const contextParts: string[] = []
    if (context.stage) {
      contextParts.push(`[用户当前处于${context.stage}阶段]`)
    }
    if (context.focusAreas?.length) {
      contextParts.push(`[关注领域: ${context.focusAreas.join(', ')}]`)
    }
    if (context.recentGlucose) {
      contextParts.push(`[最近血糖: ${context.recentGlucose} mmol/L]`)
    }
    if (contextParts.length > 0) {
      enhancedMessage = `${contextParts.join(' ')}\n\n用户说: ${userMessage}`
    }
  }

  const messages: ChatMessage[] = [
    ...history,
    { role: 'user', content: enhancedMessage },
  ]

  yield* chatStream(messages)
}
