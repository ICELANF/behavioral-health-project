<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { showConfirmDialog } from 'vant'

const router = useRouter()
const chatStore = useChatStore()

// 输入框内容
const inputMessage = ref('')
// 消息列表容器
const messageListRef = ref<HTMLElement | null>(null)
// 流式模式开关
const useStreamMode = ref(true)

// 快捷建议
const quickSuggestions = [
  '血糖高怎么办？',
  '运动有什么好处？',
  '如何改善睡眠？',
  '情绪不好怎么调节？'
]

/**
 * 滚动到底部
 */
const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

// 监听流式内容变化，自动滚动
watch(() => chatStore.streamingContent, () => {
  scrollToBottom()
})

/**
 * 发送消息
 */
const handleSend = async () => {
  const message = inputMessage.value.trim()
  if (!message || chatStore.loading) return

  inputMessage.value = ''
  scrollToBottom()

  try {
    if (useStreamMode.value) {
      // 流式模式
      await chatStore.sendMessageStream(message)
    } else {
      // 普通模式
      await chatStore.sendMessage(message)
    }
    scrollToBottom()
  } catch (error) {
    console.error('Send failed:', error)
  }
}

/**
 * 发送快捷消息
 */
const handleQuickSend = async (suggestion: string) => {
  if (chatStore.loading) return

  scrollToBottom()
  try {
    if (useStreamMode.value) {
      await chatStore.sendMessageStream(suggestion)
    } else {
      await chatStore.sendMessage(suggestion)
    }
    scrollToBottom()
  } catch (error) {
    console.error('Quick send failed:', error)
  }
}

/**
 * 返回首页
 */
const goBack = () => {
  router.back()
}

/**
 * 清空聊天记录
 */
const handleClear = () => {
  showConfirmDialog({
    title: '清空记录',
    message: '确定要清空所有聊天记录吗？'
  })
    .then(() => {
      chatStore.clearMessages()
      chatStore.getGreeting()
    })
    .catch(() => {})
}

/**
 * 格式化时间
 */
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

/**
 * LLM 状态文字
 */
const llmStatusText = computed(() => {
  if (!chatStore.llmHealth) return '检查中...'
  if (chatStore.isLLMAvailable) {
    const mode = useStreamMode.value ? '流式' : '普通'
    return `AI: ${chatStore.currentModel} (${mode})`
  }
  return 'AI 离线'
})

/**
 * 切换流式模式
 */
const toggleStreamMode = () => {
  useStreamMode.value = !useStreamMode.value
}

/**
 * LLM 状态颜色
 */
const llmStatusColor = computed(() => {
  if (!chatStore.llmHealth) return '#969799'
  return chatStore.isLLMAvailable ? '#07c160' : '#ee0a24'
})

onMounted(async () => {
  await chatStore.initChat()
  scrollToBottom()
})
</script>

<template>
  <div class="chat-page">
    <!-- 导航栏 -->
    <van-nav-bar
      title="AI 健康助手"
      left-arrow
      @click-left="goBack"
    >
      <template #right>
        <van-icon name="delete-o" size="20" @click="handleClear" />
      </template>
    </van-nav-bar>

    <!-- LLM 状态栏（点击切换流式模式） -->
    <div class="llm-status" :style="{ backgroundColor: llmStatusColor }" @click="toggleStreamMode">
      <van-icon name="service-o" />
      <span>{{ llmStatusText }}</span>
      <van-icon :name="useStreamMode ? 'play-circle-o' : 'pause-circle-o'" size="14" />
    </div>

    <!-- 消息列表 -->
    <div class="message-list" ref="messageListRef">
      <template v-if="chatStore.messages.length === 0 && !chatStore.loading">
        <div class="empty-chat">
          <div class="empty-icon">💬</div>
          <div class="empty-text">开始和 AI 健康助手对话吧</div>
        </div>
      </template>

      <template v-for="(msg, index) in chatStore.messages" :key="msg.id">
        <div class="message-item" :class="msg.role">
          <!-- 助手头像 -->
          <div v-if="msg.role === 'assistant'" class="avatar assistant-avatar">
            <van-icon name="service-o" size="24" />
          </div>

          <!-- 消息气泡 -->
          <div class="message-bubble" :class="{ streaming: chatStore.loading && index === chatStore.messages.length - 1 && msg.role === 'assistant' }">
            <div class="message-content">
              {{ msg.content }}<span v-if="chatStore.loading && index === chatStore.messages.length - 1 && msg.role === 'assistant'" class="typing-cursor">|</span>
            </div>
            <div class="message-time" v-if="!chatStore.loading || index !== chatStore.messages.length - 1 || msg.role !== 'assistant'">
              {{ formatTime(msg.timestamp) }}
            </div>
          </div>

          <!-- 用户头像 -->
          <div v-if="msg.role === 'user'" class="avatar user-avatar">
            <van-icon name="user-o" size="24" />
          </div>
        </div>
      </template>

      <!-- 加载中（仅非流式模式或流式还未开始时显示） -->
      <div v-if="chatStore.loading && !chatStore.streamingContent && chatStore.messages[chatStore.messages.length - 1]?.role === 'user'" class="message-item assistant">
        <div class="avatar assistant-avatar">
          <van-icon name="service-o" size="24" />
        </div>
        <div class="message-bubble loading">
          <van-loading size="20" />
          <span>思考中...</span>
        </div>
      </div>
    </div>

    <!-- 快捷建议 -->
    <div class="quick-suggestions" v-if="chatStore.messages.length <= 1">
      <div class="suggestion-title">试试问我：</div>
      <div class="suggestion-list">
        <van-tag
          v-for="(item, index) in quickSuggestions"
          :key="index"
          plain
          type="primary"
          size="medium"
          @click="handleQuickSend(item)"
        >
          {{ item }}
        </van-tag>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <van-field
        v-model="inputMessage"
        placeholder="输入你的问题..."
        :disabled="chatStore.loading"
        @keyup.enter="handleSend"
      >
        <template #button>
          <van-button
            type="primary"
            size="small"
            :loading="chatStore.loading"
            :disabled="!inputMessage.trim()"
            @click="handleSend"
          >
            发送
          </van-button>
        </template>
      </van-field>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f7f8fa;
}

.llm-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 4px;
  color: white;
  font-size: 12px;
  cursor: pointer;
  user-select: none;
}

.llm-status:active {
  opacity: 0.8;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  padding-bottom: 80px;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #969799;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 14px;
}

.message-item {
  display: flex;
  margin-bottom: 16px;
  align-items: flex-start;
}

.message-item.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.assistant-avatar {
  background: linear-gradient(135deg, #1989fa, #07c160);
  color: white;
  margin-right: 12px;
}

.user-avatar {
  background: #1989fa;
  color: white;
  margin-left: 12px;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  position: relative;
}

.message-item.assistant .message-bubble {
  background: white;
  border-top-left-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message-item.user .message-bubble {
  background: #1989fa;
  color: white;
  border-top-right-radius: 4px;
}

.message-bubble.loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #969799;
}

.message-content {
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.message-bubble.streaming {
  min-height: 24px;
}

.typing-cursor {
  display: inline-block;
  animation: blink 0.8s infinite;
  color: #1989fa;
  font-weight: bold;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.message-time {
  font-size: 11px;
  margin-top: 6px;
  opacity: 0.6;
}

.message-item.user .message-time {
  text-align: right;
}

.quick-suggestions {
  padding: 12px 16px;
  background: white;
  border-top: 1px solid #ebedf0;
}

.suggestion-title {
  font-size: 12px;
  color: #969799;
  margin-bottom: 8px;
}

.suggestion-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-list .van-tag {
  cursor: pointer;
}

.input-area {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-top: 1px solid #ebedf0;
  padding: 8px 12px;
  padding-bottom: calc(8px + env(safe-area-inset-bottom));
}

.input-area :deep(.van-field) {
  background: #f7f8fa;
  border-radius: 20px;
  padding: 8px 16px;
}

.input-area :deep(.van-field__control) {
  font-size: 15px;
}
</style>
