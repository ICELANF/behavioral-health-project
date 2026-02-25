<template>
  <div class="chat-view">
    <!-- 顶部导航栏 -->
    <div class="chat-nav">
      <div class="nav-left" @click="goBack">
        <LeftOutlined />
      </div>
      <div class="nav-title">
        <span class="title-icon">{{ agentInfo.icon }}</span>
        <span class="title-text">{{ agentInfo.name }}</span>
      </div>
      <div class="nav-right">
        <a-dropdown>
          <MoreOutlined />
          <template #overlay>
            <a-menu>
              <a-menu-item @click="clearHistory">
                <DeleteOutlined /> 清空对话
              </a-menu-item>
              <a-menu-item @click="showSettingsDrawer = true">
                <SettingOutlined /> 设置
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- 聊天主体区域 -->
    <div class="chat-body" ref="chatBodyRef">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-section">
        <div class="welcome-avatar">{{ agentInfo.icon }}</div>
        <h2 class="welcome-title">{{ agentInfo.greeting }}</h2>
        <p class="welcome-desc">{{ agentInfo.description }}</p>

        <!-- 快捷问题 -->
        <div class="quick-questions">
          <div
            v-for="q in agentInfo.quickQuestions"
            :key="q"
            class="quick-question-btn"
            @click="sendQuickQuestion(q)"
          >
            {{ q }}
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message-wrapper"
        :class="msg.role"
      >
        <div class="message-avatar">
          <template v-if="msg.role === 'assistant'">{{ agentInfo.icon }}</template>
          <template v-else><UserOutlined /></template>
        </div>
        <div class="message-bubble">
          <div class="message-content" v-html="formatMessage(msg.content)"></div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>

      <!-- 正在输入指示器 -->
      <div v-if="isLoading" class="message-wrapper assistant">
        <div class="message-avatar">{{ agentInfo.icon }}</div>
        <div class="message-bubble typing">
          <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部输入区域 -->
    <div class="chat-input-area">
      <div class="input-toolbar">
        <a-tooltip title="语音输入">
          <AudioOutlined class="toolbar-icon" />
        </a-tooltip>
        <a-tooltip title="上传图片">
          <CameraOutlined class="toolbar-icon" />
        </a-tooltip>
      </div>
      <div class="input-box">
        <a-textarea
          v-model:value="inputText"
          placeholder="输入你的问题..."
          :auto-size="{ minRows: 1, maxRows: 4 }"
          @pressEnter="handleEnter"
          :disabled="isLoading"
          class="message-input"
        />
        <div class="send-btn" :class="{ active: inputText.trim() && !isLoading }" @click="sendMessage">
          <SendOutlined v-if="!isLoading" />
          <LoadingOutlined v-else />
        </div>
      </div>
      <div class="input-hint">
        <span>按 Enter 发送，Shift + Enter 换行</span>
        <span class="model-tag">{{ selectedModel }}</span>
      </div>
    </div>

    <!-- 设置抽屉 -->
    <a-drawer
      v-model:open="showSettingsDrawer"
      title="聊天设置"
      placement="bottom"
      :height="400"
    >
      <a-form layout="vertical">
        <a-form-item label="AI 模型">
          <a-select v-model:value="selectedModel" style="width: 100%">
            <a-select-option value="qwen2.5:14b">Qwen2.5 14B (推荐)</a-select-option>
            <a-select-option value="deepseek-r1:7b">DeepSeek-R1 7B</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="流式输出">
          <a-switch v-model:checked="useStream" />
          <span class="form-hint">开启后可实时看到回复</span>
        </a-form-item>
        <a-form-item label="行为阶段">
          <a-select v-model:value="userContext.stage" placeholder="选择你当前的行为阶段">
            <a-select-option value="precontemplation">前意向期 - 还没想过改变</a-select-option>
            <a-select-option value="contemplation">意向期 - 开始考虑改变</a-select-option>
            <a-select-option value="preparation">准备期 - 准备开始行动</a-select-option>
            <a-select-option value="action">行动期 - 正在努力改变</a-select-option>
            <a-select-option value="maintenance">维持期 - 已形成习惯</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="关注领域">
          <a-checkbox-group v-model:value="userContext.focusAreas" :options="focusAreaOptions" />
        </a-form-item>
      </a-form>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  LeftOutlined,
  MoreOutlined,
  DeleteOutlined,
  SettingOutlined,
  UserOutlined,
  AudioOutlined,
  CameraOutlined,
  SendOutlined,
  LoadingOutlined
} from '@ant-design/icons-vue'
import {
  checkOllamaHealth,
  healthConsultStream,
  healthConsult,
  type ChatMessage
} from '@/api/ollama'
import { formatChatMessage } from '@/utils/sanitize'

// 路由参数
const route = useRoute()
const router = useRouter()
const agentType = computed(() => (route.query.agent as string) || 'A1')

// Agent 配置
interface AgentConfig {
  name: string
  icon: string
  greeting: string
  description: string
  quickQuestions: string[]
}

const AGENT_CONFIGS: Record<string, AgentConfig> = {
  A1: {
    name: '健康教练',
    icon: '🌿',
    greeting: '你好，我是你的健康教练',
    description: '我可以帮你管理血糖、制定饮食计划、解答健康问题。有什么想聊的吗？',
    quickQuestions: [
      '如何控制餐后血糖？',
      '帮我制定运动计划',
      '低GI食物有哪些？',
      '血糖高怎么办？'
    ]
  },
  A2: {
    name: '运动指导',
    icon: '🏋️',
    greeting: '让我们一起动起来',
    description: '我会根据你的身体状况，为你设计安全有效的运动方案。',
    quickQuestions: [
      '适合糖尿病人的运动',
      '每天运动多久合适？',
      '饭后多久可以运动？',
      '如何避免运动低血糖？'
    ]
  },
  A3: {
    name: '饮食顾问',
    icon: '🥗',
    greeting: '吃对了，健康自然来',
    description: '我帮你选择适合的食物，制定个性化的饮食计划。',
    quickQuestions: [
      '今天吃什么好？',
      '哪些水果可以吃？',
      '如何计算碳水化合物？',
      '外出就餐怎么选？'
    ]
  },
  A4: {
    name: '心理支持',
    icon: '🧘',
    greeting: '我在这里陪伴你',
    description: '管理健康的路上，我会倾听你的心声，给你温暖的支持。',
    quickQuestions: [
      '我总是坚持不下来',
      '血糖控制不好很焦虑',
      '家人不理解我',
      '如何保持积极心态？'
    ]
  }
}

const agentInfo = computed(() => AGENT_CONFIGS[agentType.value] || AGENT_CONFIGS.A1)

// 消息列表
interface DisplayMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const messages = ref<DisplayMessage[]>([])
const chatHistory = ref<ChatMessage[]>([])
const inputText = ref('')
const isLoading = ref(false)
const chatBodyRef = ref<HTMLElement | null>(null)

// 设置
const showSettingsDrawer = ref(false)
const selectedModel = ref('qwen2.5:14b')
const useStream = ref(true)
const userContext = reactive({
  stage: 'preparation',
  focusAreas: ['glucose', 'diet'] as string[],
  recentGlucose: undefined as number | undefined
})

const focusAreaOptions = [
  { label: '血糖管理', value: 'glucose' },
  { label: '饮食控制', value: 'diet' },
  { label: '运动锻炼', value: 'exercise' },
  { label: '用药依从', value: 'medication' },
  { label: '睡眠质量', value: 'sleep' },
  { label: '体重管理', value: 'weight' }
]

// 检查服务状态
onMounted(async () => {
  const online = await checkOllamaHealth()
  if (!online) {
    message.warning('AI 服务离线，请确保 Ollama 正在运行')
  }

  // 从 localStorage 恢复历史消息
  const savedMessages = localStorage.getItem(`chat_history_${agentType.value}`)
  if (savedMessages) {
    try {
      const parsed = JSON.parse(savedMessages)
      messages.value = parsed.map((m: { role: string; content: string; timestamp: string }) => ({
        ...m,
        timestamp: new Date(m.timestamp)
      }))
      // 重建聊天历史
      chatHistory.value = messages.value.map(m => ({
        role: m.role,
        content: m.content
      }))
    } catch {
      // 忽略解析错误
    }
  }

  scrollToBottom()
})

// 保存消息到 localStorage
watch(messages, (newMessages) => {
  localStorage.setItem(`chat_history_${agentType.value}`, JSON.stringify(newMessages))
}, { deep: true })

// 发送消息
const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: text,
    timestamp: new Date()
  })
  inputText.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    if (useStream.value) {
      // 流式输出
      let assistantMessage = ''
      messages.value.push({
        role: 'assistant',
        content: '',
        timestamp: new Date()
      })
      const lastIndex = messages.value.length - 1

      const stream = healthConsultStream(
        text,
        chatHistory.value,
        userContext
      )

      for await (const chunk of stream) {
        assistantMessage += chunk
        messages.value[lastIndex].content = assistantMessage
        scrollToBottom()
      }

      // 更新历史
      chatHistory.value.push(
        { role: 'user', content: text },
        { role: 'assistant', content: assistantMessage }
      )
    } else {
      // 阻塞输出
      const result = await healthConsult(
        text,
        chatHistory.value,
        userContext
      )

      messages.value.push({
        role: 'assistant',
        content: result.response,
        timestamp: new Date()
      })

      chatHistory.value = result.messages
    }
  } catch (error: unknown) {
    const errorMsg = error instanceof Error ? error.message : 'AI 响应失败'
    message.error(errorMsg)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，我暂时无法回复。请检查 Ollama 服务是否正常运行。',
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 快捷问题
const sendQuickQuestion = (question: string) => {
  inputText.value = question
  sendMessage()
}

// 处理回车
const handleEnter = (e: KeyboardEvent) => {
  if (!e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 清空历史
const clearHistory = () => {
  messages.value = []
  chatHistory.value = []
  localStorage.removeItem(`chat_history_${agentType.value}`)
  message.success('对话已清空')
}

// 返回
const goBack = () => {
  router.back()
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatBodyRef.value) {
      chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
    }
  })
}

// 格式化消息 (DOMPurify sanitize 防 XSS)
const formatMessage = (content: string) => formatChatMessage(content)

// 格式化时间
const formatTime = (date: Date) => {
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

/* 顶部导航 */
.chat-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-left, .nav-right {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 18px;
}

.nav-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 24px;
}

.title-text {
  font-size: 17px;
  font-weight: 600;
}

/* 聊天主体 */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  padding-bottom: 120px;
}

/* 欢迎区域 */
.welcome-section {
  text-align: center;
  padding: 40px 20px;
}

.welcome-avatar {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.welcome-desc {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 24px;
  line-height: 1.6;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.quick-question-btn {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-question-btn:hover {
  background: #667eea;
  color: #fff;
  border-color: #667eea;
}

/* 消息 */
.message-wrapper {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  max-width: 85%;
}

.message-wrapper.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: #e5e7eb;
}

.message-wrapper.assistant .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message-bubble {
  max-width: calc(100% - 46px);
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-wrapper.assistant .message-content {
  background: #fff;
  color: #374151;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.message-wrapper.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
  padding: 0 4px;
}

.message-wrapper.user .message-time {
  text-align: right;
}

/* 输入指示器 */
.message-bubble.typing {
  padding: 12px 16px;
  background: #fff;
  border-radius: 16px;
  border-bottom-left-radius: 4px;
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite both;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

/* 底部输入区域 */
.chat-input-area {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  border-top: 1px solid #e5e7eb;
  padding: 8px 16px 16px;
  z-index: 100;
}

.input-toolbar {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}

.toolbar-icon {
  font-size: 20px;
  color: #9ca3af;
  cursor: pointer;
  transition: color 0.2s;
}

.toolbar-icon:hover {
  color: #667eea;
}

.input-box {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: #f3f4f6;
  border-radius: 24px;
  padding: 8px 12px;
}

.message-input {
  flex: 1;
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
  resize: none;
  font-size: 15px;
  padding: 4px 0;
}

.message-input:focus {
  border: none !important;
  box-shadow: none !important;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  cursor: not-allowed;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  cursor: pointer;
}

.input-hint {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 6px;
  padding: 0 8px;
}

.model-tag {
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 10px;
}

/* 设置抽屉 */
.form-hint {
  font-size: 12px;
  color: #9ca3af;
  margin-left: 8px;
}

/* 代码样式 */
:deep(code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: monospace;
}

.message-wrapper.user :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}
</style>
