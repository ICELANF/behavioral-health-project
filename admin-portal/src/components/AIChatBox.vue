<template>
  <div class="ai-chat-box">
    <!-- 聊天头部 -->
    <div class="chat-header">
      <div class="header-info">
        <div class="ai-avatar">🌿</div>
        <div class="ai-name">
          <span class="name">健康教练</span>
          <span class="status" :class="{ online: isOnline }">
            {{ isOnline ? '在线' : '离线' }}
          </span>
        </div>
      </div>
      <div class="header-actions">
        <a-tooltip title="清空对话">
          <DeleteOutlined @click="clearMessages" />
        </a-tooltip>
        <a-tooltip title="设置">
          <SettingOutlined @click="showSettings = true" />
        </a-tooltip>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-message">
        <div class="welcome-icon">🌿</div>
        <h3>你好！我是你的健康教练</h3>
        <p>我可以帮助你管理血糖、制定饮食计划、设计运动方案。有什么想聊的吗？</p>
        <div class="quick-questions">
          <a-button
            v-for="q in quickQuestions"
            :key="q"
            size="small"
            @click="sendQuickQuestion(q)"
          >
            {{ q }}
          </a-button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message"
        :class="msg.role"
      >
        <div class="message-avatar">
          <template v-if="msg.role === 'assistant'">🌿</template>
          <template v-else>👤</template>
        </div>
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(msg.content)"></div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>

      <!-- 加载指示器 -->
      <div v-if="isLoading" class="message assistant loading">
        <div class="message-avatar">🌿</div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input">
      <a-textarea
        v-model:value="inputText"
        placeholder="输入你的问题..."
        :auto-size="{ minRows: 1, maxRows: 4 }"
        @pressEnter="handleEnter"
        :disabled="isLoading"
      />
      <a-button
        type="primary"
        :loading="isLoading"
        :disabled="!inputText.trim()"
        @click="sendMessage"
      >
        <template #icon><SendOutlined /></template>
      </a-button>
    </div>

    <!-- 设置抽屉 -->
    <a-drawer
      v-model:open="showSettings"
      title="AI 设置"
      placement="right"
      :width="320"
    >
      <a-form layout="vertical">
        <a-form-item label="模型选择">
          <a-select v-model:value="selectedModel" style="width: 100%">
            <a-select-option value="deepseek-r1:7b">DeepSeek-R1 7B</a-select-option>
            <a-select-option value="qwen2.5:14b">Qwen2.5 14B</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="流式输出">
          <a-switch v-model:checked="useStream" />
        </a-form-item>
        <a-form-item label="用户上下文">
          <a-select v-model:value="userContext.stage" placeholder="行为阶段">
            <a-select-option value="precontemplation">前意向期</a-select-option>
            <a-select-option value="contemplation">意向期</a-select-option>
            <a-select-option value="preparation">准备期</a-select-option>
            <a-select-option value="action">行动期</a-select-option>
            <a-select-option value="maintenance">维持期</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  DeleteOutlined,
  SettingOutlined,
  SendOutlined
} from '@ant-design/icons-vue'
import {
  checkOllamaHealth,
  healthConsult,
  healthConsultStream,
  type ChatMessage
} from '@/api/ollama'
import { formatChatMessage } from '@/utils/sanitize'

interface DisplayMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

// 状态
const messages = ref<DisplayMessage[]>([])
const inputText = ref('')
const isLoading = ref(false)
const isOnline = ref(false)
const showSettings = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

// 设置
const selectedModel = ref('qwen2.5:14b')
const useStream = ref(true)
const userContext = reactive({
  stage: 'preparation',
  focusAreas: ['glucose', 'diet'],
  recentGlucose: undefined as number | undefined
})

// 快捷问题
const quickQuestions = [
  '如何控制餐后血糖？',
  '帮我制定运动计划',
  '低GI食物有哪些？',
  '血糖高怎么办？'
]

// 对话历史 (用于多轮对话)
const chatHistory = ref<ChatMessage[]>([])

// 检查服务状态
onMounted(async () => {
  isOnline.value = await checkOllamaHealth()
  if (!isOnline.value) {
    message.warning('AI 服务离线，请检查 Ollama 是否运行')
  }
})

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
    const errorMessage = error instanceof Error ? error.message : 'AI 响应失败'
    message.error(errorMessage)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，我暂时无法回复。请稍后再试。',
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

// 清空消息
const clearMessages = () => {
  messages.value = []
  chatHistory.value = []
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
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
.ai-chat-box {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* 头部 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-avatar {
  font-size: 28px;
}

.ai-name .name {
  font-size: 16px;
  font-weight: 600;
  display: block;
}

.ai-name .status {
  font-size: 11px;
  opacity: 0.8;
}

.ai-name .status.online::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  background: #52c41a;
  border-radius: 50%;
  margin-right: 4px;
}

.header-actions {
  display: flex;
  gap: 16px;
  font-size: 18px;
  cursor: pointer;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f9fafb;
}

/* 欢迎消息 */
.welcome-message {
  text-align: center;
  padding: 40px 20px;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.welcome-message h3 {
  font-size: 18px;
  color: #1f2937;
  margin-bottom: 8px;
}

.welcome-message p {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 20px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.quick-questions .ant-btn {
  border-radius: 20px;
  font-size: 12px;
}

/* 消息 */
.message {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.message.assistant .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message-content {
  max-width: 70%;
}

.message-text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.message.assistant .message-text {
  background: #fff;
  color: #374151;
  border-bottom-left-radius: 4px;
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
  text-align: right;
}

.message.assistant .message-time {
  text-align: left;
}

/* 加载指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 10px 14px;
  background: #fff;
  border-radius: 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite both;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
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

/* 输入区域 */
.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  background: #fff;
}

.chat-input .ant-input {
  border-radius: 20px;
  resize: none;
}

.chat-input .ant-btn {
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
