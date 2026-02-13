<template>
  <div class="chat-optimized">
    <!-- 顶部导航 -->
    <div class="chat-header">
      <div class="header-left" @click="goBack">
        <LeftOutlined />
      </div>
      <div class="header-center">
        <div class="ai-avatar" :class="aiMood">{{ agentEmoji }}</div>
        <div class="ai-info">
          <div class="ai-name">{{ agentName }}</div>
          <div class="ai-status">{{ aiStatusText }}</div>
        </div>
      </div>
      <div class="header-right" @click="showMenu = true">
        <MoreOutlined />
      </div>
    </div>

    <!-- 聊天区域 -->
    <div class="chat-container" ref="chatContainer">
      <!-- 欢迎界面 -->
      <div v-if="messages.length === 0" class="welcome-screen">
        <div class="welcome-avatar">{{ agentEmoji }}</div>
        <h2 class="welcome-title">{{ welcomeTitle }}</h2>
        <p class="welcome-subtitle">{{ welcomeSubtitle }}</p>

        <!-- 健康快照卡片 -->
        <div class="health-snapshot-card" v-if="healthSnapshot">
          <div class="snapshot-title">📊 您的健康快照</div>
          <div class="snapshot-grid">
            <div class="snapshot-item">
              <div class="snapshot-label">血糖</div>
              <div class="snapshot-value">{{ healthSnapshot.glucose }}</div>
            </div>
            <div class="snapshot-item">
              <div class="snapshot-label">体重</div>
              <div class="snapshot-value">{{ healthSnapshot.weight }}</div>
            </div>
          </div>
          <div class="snapshot-hint">我已经了解您的情况，可以给您更准确的建议</div>
        </div>

        <!-- 快速提问 -->
        <div class="quick-questions">
          <div class="quick-title">💬 您可以这样问我</div>
          <div
            v-for="(q, index) in quickQuestions"
            :key="index"
            class="quick-question"
            @click="askQuestion(q.text)"
          >
            <div class="question-icon">{{ q.icon }}</div>
            <div class="question-text">{{ q.text }}</div>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="messages-list">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message-item"
          :class="msg.role"
        >
          <!-- AI消息 -->
          <template v-if="msg.role === 'assistant'">
            <div class="message-row">
              <div class="message-avatar ai">{{ agentEmoji }}</div>
              <div class="message-bubble ai">
                <div class="bubble-content" v-html="formatMessage(msg.content)"></div>

                <!-- 数据卡片（如果有） -->
                <div v-if="msg.dataCard" class="data-card">
                  <div class="data-card-title">{{ msg.dataCard.title }}</div>
                  <div class="data-card-content">{{ msg.dataCard.content }}</div>
                </div>

                <!-- 快捷回复建议 -->
                <div v-if="msg.suggestedReplies" class="suggested-replies">
                  <div
                    v-for="(reply, i) in msg.suggestedReplies"
                    :key="i"
                    class="reply-chip"
                    @click="askQuestion(reply)"
                  >
                    {{ reply }}
                  </div>
                </div>

                <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
              </div>
            </div>
          </template>

          <!-- 用户消息 -->
          <template v-else>
            <div class="message-row">
              <div class="message-bubble user">
                <div class="bubble-content">{{ msg.content }}</div>
                <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
              </div>
              <div class="message-avatar user">👤</div>
            </div>
          </template>
        </div>

        <!-- 正在输入 -->
        <div v-if="isTyping" class="message-item assistant">
          <div class="message-row">
            <div class="message-avatar ai">{{ agentEmoji }}</div>
            <div class="message-bubble ai typing">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷回复栏（当有消息时显示） -->
    <div v-if="messages.length > 0 && contextualQuickReplies.length > 0" class="quick-reply-bar">
      <div class="quick-reply-scroll">
        <div
          v-for="(reply, index) in contextualQuickReplies"
          :key="index"
          class="quick-reply-btn"
          @click="askQuestion(reply)"
        >
          {{ reply }}
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-container">
      <div class="input-wrapper">
        <div class="input-actions">
          <div class="action-btn" @click="showVoiceInput">
            <AudioOutlined />
          </div>
        </div>
        <a-textarea
          v-model:value="userInput"
          :placeholder="inputPlaceholder"
          :auto-size="{ minRows: 1, maxRows: 3 }"
          class="chat-input"
          @pressEnter.prevent="handleSend"
          :disabled="isTyping"
        />
        <div
          class="send-button"
          :class="{ active: canSend }"
          @click="handleSend"
        >
          <SendOutlined v-if="!isTyping" />
          <LoadingOutlined v-else spin />
        </div>
      </div>
    </div>

    <!-- 菜单抽屉 -->
    <a-drawer
      v-model:open="showMenu"
      title="对话设置"
      placement="right"
      :width="280"
    >
      <div class="menu-list">
        <div class="menu-item" @click="clearMessages">
          <DeleteOutlined />
          <span>清空对话</span>
        </div>
        <div class="menu-item" @click="exportChat">
          <DownloadOutlined />
          <span>导出对话</span>
        </div>
        <div class="menu-item" @click="showHelp">
          <QuestionCircleOutlined />
          <span>使用帮助</span>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LeftOutlined,
  MoreOutlined,
  SendOutlined,
  AudioOutlined,
  LoadingOutlined,
  DeleteOutlined,
  DownloadOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { healthApi } from '@/api/health'

const router = useRouter()

// 患者ID（实际应该从登录状态获取）
const patientId = 'p001'

// AI信息
const agentName = ref('AI健康助手')
const agentEmoji = ref('🤖')
const aiMood = ref('happy') // happy, thinking, caring
const aiStatusText = ref('在线，随时为您服务')

const welcomeTitle = ref('你好！我是你的健康助手')
const welcomeSubtitle = ref('有什么我可以帮助你的吗？')

// 健康快照
const healthSnapshot = ref({
  glucose: '--',
  weight: '--'
})

// 加载健康快照数据
const loadHealthSnapshot = async () => {
  try {
    const data = await healthApi.getHealthSnapshot(patientId)
    if (data) {
      healthSnapshot.value = {
        glucose: `${data.glucose.value} mmol/L`,
        weight: `${data.weight.value} kg`
      }
    }
  } catch (error) {
    console.error('加载健康快照失败:', error)
  }
}

// 快速提问
const quickQuestions = ref([
  { icon: '🩸', text: '今天的血糖正常吗？' },
  { icon: '🍽️', text: '午餐应该吃什么？' },
  { icon: '🏃', text: '推荐一个运动计划' },
  { icon: '💊', text: '忘记吃药怎么办？' }
])

// 上下文快捷回复
const contextualQuickReplies = ref<string[]>([])

// 消息列表
interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  suggestedReplies?: string[]
  dataCard?: {
    title: string
    content: string
  }
}

const messages = ref<Message[]>([])
const userInput = ref('')
const isTyping = ref(false)
const showMenu = ref(false)
const chatContainer = ref<HTMLElement | null>(null)

const inputPlaceholder = computed(() => {
  if (isTyping.value) return 'AI正在思考...'
  return '输入你的问题...'
})

const canSend = computed(() => {
  return userInput.value.trim().length > 0 && !isTyping.value
})

// 发送消息
const handleSend = async () => {
  if (!canSend.value) return

  const text = userInput.value.trim()
  userInput.value = ''

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: text,
    timestamp: Date.now()
  })

  scrollToBottom()

  // 模拟AI回复
  isTyping.value = true
  aiMood.value = 'thinking'
  aiStatusText.value = '正在思考...'

  setTimeout(() => {
    const reply = generateAIReply(text)
    messages.value.push(reply)

    isTyping.value = false
    aiMood.value = 'happy'
    aiStatusText.value = '在线，随时为您服务'

    // 更新上下文快捷回复
    updateContextualReplies(text)

    scrollToBottom()
  }, 1500 + Math.random() * 1000)
}

// 快速提问
const askQuestion = (text: string) => {
  userInput.value = text
  handleSend()
}

// 生成AI回复
const generateAIReply = (userText: string): Message => {
  const lowerText = userText.toLowerCase()

  if (lowerText.includes('血糖')) {
    return {
      role: 'assistant',
      content: '根据您今天的血糖记录 **6.5 mmol/L**，您的血糖控制得不错！这个数值在正常范围内。\n\n建议您继续保持：\n- 均衡饮食\n- 适量运动\n- 按时用药',
      timestamp: Date.now(),
      dataCard: {
        title: '📊 血糖趋势',
        content: '近7天平均：6.3 mmol/L ✅'
      },
      suggestedReplies: ['饮食有什么建议？', '需要调整用药吗？']
    }
  }

  if (lowerText.includes('午餐') || lowerText.includes('吃什么')) {
    return {
      role: 'assistant',
      content: '午餐推荐：\n\n**主食**：糙米饭或全麦面包（控制在100g左右）\n**蛋白质**：清蒸鱼或鸡胸肉\n**蔬菜**：西兰花、胡萝卜等\n**水果**：饭后1小时吃半个苹果\n\n记得饭后散步15分钟哦！',
      timestamp: Date.now(),
      suggestedReplies: ['晚餐呢？', '有什么忌口的吗？']
    }
  }

  if (lowerText.includes('运动')) {
    return {
      role: 'assistant',
      content: '为您推荐一个适合的运动计划：\n\n**每天30分钟**\n- 快走 20分钟\n- 拉伸 10分钟\n\n**建议时间**：饭后1小时\n\n**注意事项**：\n- 携带糖果预防低血糖\n- 穿舒适的鞋子\n- 循序渐进，不要勉强',
      timestamp: Date.now(),
      suggestedReplies: ['开始记录运动', '运动后要注意什么？']
    }
  }

  if (lowerText.includes('药')) {
    return {
      role: 'assistant',
      content: '如果偶尔忘记吃药，不要慌张：\n\n**如果距离下次吃药还有4小时以上**：\n立即补服\n\n**如果快到下次吃药时间**：\n不要补服，按时服用下一次的药\n\n**重要提示**：\n- 不要一次吃两次的量\n- 建议设置用药提醒\n- 经常忘记需要咨询医生',
      timestamp: Date.now(),
      dataCard: {
        title: '💊 今日用药',
        content: '已服用 2/3 剂次'
      },
      suggestedReplies: ['设置用药提醒', '查看用药记录']
    }
  }

  // 默认回复
  return {
    role: 'assistant',
    content: '我理解您的问题。作为您的健康助手，我可以帮您：\n\n- 解答健康疑问\n- 提供饮食建议\n- 制定运动计划\n- 用药提醒和指导\n\n请告诉我您具体想了解什么？',
    timestamp: Date.now(),
    suggestedReplies: ['血糖管理', '饮食建议', '运动计划']
  }
}

// 更新上下文快捷回复
const updateContextualReplies = (userText: string) => {
  const lowerText = userText.toLowerCase()

  if (lowerText.includes('血糖')) {
    contextualQuickReplies.value = ['饮食建议', '运动计划', '用药指导']
  } else if (lowerText.includes('饮食') || lowerText.includes('吃')) {
    contextualQuickReplies.value = ['查看食谱', '记录饮食', '计算热量']
  } else if (lowerText.includes('运动')) {
    contextualQuickReplies.value = ['开始记录', '查看进度', '调整计划']
  } else {
    contextualQuickReplies.value = ['血糖情况', '今天吃什么', '运动建议']
  }
}

// 格式化消息
const formatMessage = (content: string) => {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

// 格式化时间
const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// 清空消息
const clearMessages = () => {
  messages.value = []
  contextualQuickReplies.value = []
  showMenu.value = false
  message.success('对话已清空')
}

// 导出对话 — 导出为文本文件
const exportChat = () => {
  if (!messages.value.length) {
    message.warning('暂无对话内容')
    showMenu.value = false
    return
  }
  const text = messages.value.map(m => `[${m.role === 'user' ? '我' : 'AI'}] ${m.content}`).join('\n\n')
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `对话记录_${new Date().toISOString().slice(0, 10)}.txt`
  a.click()
  URL.revokeObjectURL(url)
  message.success('对话已导出')
  showMenu.value = false
}

// 显示帮助
const showHelp = () => {
  message.info('使用帮助：直接输入问题，AI 会为您解答健康相关问题')
  showMenu.value = false
}

// 语音输入
const showVoiceInput = () => {
  message.info('语音输入功能即将上线')
}

// 返回
const goBack = () => {
  router.back()
}

onMounted(() => {
  // 加载健康快照数据
  loadHealthSnapshot()
})
</script>

<style scoped>
.chat-optimized {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 顶部导航 */
.chat-header {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header-left,
.header-right {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 20px;
  border-radius: 50%;
  transition: background 0.2s;
}

.header-left:hover,
.header-right:hover {
  background: rgba(255,255,255,0.1);
}

.header-center {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  justify-content: center;
}

.ai-avatar {
  font-size: 36px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.2);
  border-radius: 50%;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.ai-avatar.thinking {
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.ai-name {
  font-size: 16px;
  font-weight: 700;
}

.ai-status {
  font-size: 12px;
  opacity: 0.9;
}

/* 聊天容器 */
.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  scroll-behavior: smooth;
}

/* 欢迎界面 */
.welcome-screen {
  max-width: 640px;
  margin: 40px auto 0;
  text-align: center;
}

.welcome-avatar {
  font-size: 80px;
  margin-bottom: 20px;
  animation: scaleIn 0.5s ease-out;
}

@keyframes scaleIn {
  from { transform: scale(0); }
  to { transform: scale(1); }
}

.welcome-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 8px;
}

.welcome-subtitle {
  font-size: 16px;
  color: #6b7280;
  margin-bottom: 32px;
}

.health-snapshot-card {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 2px solid #bfdbfe;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 24px;
  text-align: left;
}

.snapshot-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e40af;
  margin-bottom: 16px;
}

.snapshot-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 12px;
}

.snapshot-item {
  background: #fff;
  padding: 12px;
  border-radius: 12px;
}

.snapshot-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
}

.snapshot-value {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.snapshot-hint {
  font-size: 13px;
  color: #1e40af;
  font-style: italic;
}

/* 快速提问 */
.quick-questions {
  margin-top: 24px;
}

.quick-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
  text-align: left;
}

.quick-question {
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.quick-question:hover {
  border-color: #10b981;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(16,185,129,0.15);
}

.question-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.question-text {
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
}

/* 消息列表 */
.messages-list {
  max-width: 640px;
  margin: 0 auto;
}

.message-item {
  margin-bottom: 20px;
}

.message-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message-item.user .message-row {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.message-avatar.ai {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
}

.message-avatar.user {
  background: #f3f4f6;
}

.message-bubble {
  max-width: 70%;
  padding: 14px 18px;
  border-radius: 18px;
  position: relative;
}

.message-bubble.ai {
  background: #fff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.message-bubble.user {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: #fff;
}

.bubble-content {
  font-size: 15px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.message-bubble.user .bubble-content {
  color: #fff;
}

.message-time {
  font-size: 11px;
  opacity: 0.6;
  text-align: right;
}

/* 数据卡片 */
.data-card {
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 12px;
  padding: 12px;
  margin-top: 12px;
}

.data-card-title {
  font-size: 13px;
  font-weight: 600;
  color: #16a34a;
  margin-bottom: 6px;
}

.data-card-content {
  font-size: 14px;
  color: #15803d;
}

/* 快捷回复建议 */
.suggested-replies {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.reply-chip {
  padding: 6px 14px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s;
}

.reply-chip:hover {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
}

/* 正在输入 */
.message-bubble.typing {
  padding: 16px 24px;
}

.typing-indicator {
  display: flex;
  gap: 6px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite;
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
    opacity: 0.5;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

/* 快捷回复栏 */
.quick-reply-bar {
  background: #fff;
  border-top: 1px solid #e5e7eb;
  padding: 12px 16px;
}

.quick-reply-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.quick-reply-scroll::-webkit-scrollbar {
  height: 0;
}

.quick-reply-btn {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.quick-reply-btn:hover {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
}

/* 输入区域 */
.input-container {
  background: #fff;
  border-top: 1px solid #e5e7eb;
  padding: 12px 16px 24px;
}

.input-wrapper {
  max-width: 640px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.input-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  color: #6b7280;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.chat-input {
  flex: 1;
  border: 2px solid #e5e7eb !important;
  border-radius: 20px !important;
  padding: 10px 16px !important;
  font-size: 15px !important;
  resize: none !important;
  transition: border-color 0.2s !important;
}

.chat-input:focus {
  border-color: #10b981 !important;
  box-shadow: 0 0 0 3px rgba(16,185,129,0.1) !important;
}

.send-button {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e5e7eb;
  border-radius: 50%;
  cursor: pointer;
  font-size: 20px;
  color: #9ca3af;
  transition: all 0.3s;
}

.send-button.active {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(16,185,129,0.3);
}

.send-button.active:hover {
  transform: scale(1.1);
}

/* 菜单列表 */
.menu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: #f9fafb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 15px;
  color: #1f2937;
}

.menu-item:hover {
  background: #f3f4f6;
  transform: translateX(4px);
}
</style>
