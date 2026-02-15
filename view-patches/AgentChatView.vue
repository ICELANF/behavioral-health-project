<!--
  AgentChatView.vue — AI助手对话页
  多Agent切换 + 消息流 + SafetyPipeline提示
-->

<template>
  <div class="chat-view">
    <!-- 左侧：Agent列表 -->
    <div class="agent-sidebar">
      <div class="sidebar-header">
        <h3>AI助手</h3>
      </div>
      <div class="agent-list">
        <div
          v-for="agent in agents"
          :key="agent.id"
          class="agent-item"
          :class="{ active: selectedAgent?.id === agent.id }"
          @click="selectAgent(agent)"
        >
          <div class="agent-avatar" :style="{ background: agent.color || '#e0f2fe' }">
            {{ agent.icon || '🤖' }}
          </div>
          <div class="agent-info">
            <div class="agent-name">{{ agent.display_name }}</div>
            <div class="agent-domain">{{ agent.domain || '通用' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：对话区 -->
    <div class="chat-main">
      <!-- 消息列表 -->
      <div class="message-list" ref="messageListRef">
        <div v-if="!messages.length" class="empty-chat">
          <div class="empty-icon">💬</div>
          <h3>开始对话</h3>
          <p>选择一位AI助手，开始您的健康咨询</p>
        </div>
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message-item"
          :class="msg.role"
        >
          <div class="message-bubble">
            <div class="message-text">{{ msg.content }}</div>
            <div class="message-meta">
              <span v-if="msg.blocked" class="safety-tag">
                🛡️ 已过滤
              </span>
              <span class="message-time">{{ formatTime(msg.created_at) }}</span>
            </div>
          </div>
        </div>
        <div v-if="sending" class="message-item assistant">
          <div class="message-bubble typing">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <a-input
          v-model:value="inputText"
          placeholder="输入您的问题..."
          size="large"
          @pressEnter="sendMessage"
          :disabled="sending"
        >
          <template #suffix>
            <a-button
              type="primary"
              shape="circle"
              :loading="sending"
              @click="sendMessage"
              :disabled="!inputText.trim()"
            >
              <template #icon><send-outlined /></template>
            </a-button>
          </template>
        </a-input>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { agentApi } from '@/api'
import { SendOutlined } from '@ant-design/icons-vue'

interface Agent {
  id: string
  display_name: string
  domain?: string
  icon?: string
  color?: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  blocked?: boolean
}

const agents = ref<Agent[]>([])
const selectedAgent = ref<Agent | null>(null)
const messages = ref<Message[]>([])
const inputText = ref('')
const sending = ref(false)
const sessionId = ref<string | null>(null)
const messageListRef = ref<HTMLElement | null>(null)

onMounted(async () => {
  try {
    agents.value = await agentApi.listAgents()
  } catch {
    agents.value = [
      { id: 'default', display_name: '健康助手', domain: '通用', icon: '🧠', color: '#e0f2fe' },
    ]
  }
})

async function selectAgent(agent: Agent) {
  selectedAgent.value = agent
  messages.value = []
  sessionId.value = null
  try {
    const session = await agentApi.createSession(agent.id)
    sessionId.value = session.session_id || session.id
  } catch { /* use agent/run fallback */ }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  inputText.value = ''
  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content: text,
    created_at: new Date().toISOString(),
  })
  scrollToBottom()

  sending.value = true
  try {
    let response: any
    if (sessionId.value) {
      response = await agentApi.sendMessage(sessionId.value, text)
    } else {
      response = await agentApi.runAgent(selectedAgent.value?.id || 'default', text)
    }

    messages.value.push({
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: response.content || response.response || response.message || '收到',
      created_at: new Date().toISOString(),
      blocked: response.blocked || response.filtered,
    })
  } catch (err: any) {
    messages.value.push({
      id: `error-${Date.now()}`,
      role: 'assistant',
      content: err.message || '抱歉，暂时无法回复，请稍后重试。',
      created_at: new Date().toISOString(),
    })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.chat-view {
  display: flex;
  height: calc(100vh - 88px);
  background: white;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid #f0f0f0;
}
.agent-sidebar {
  width: 240px;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}
.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}
.sidebar-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}
.agent-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.agent-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}
.agent-item:hover { background: #f0f0f0; }
.agent-item.active { background: #e8f5e9; }
.agent-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.agent-name { font-size: 13px; font-weight: 500; color: #333; }
.agent-domain { font-size: 11px; color: #999; }
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.empty-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}
.empty-icon { font-size: 48px; opacity: 0.3; margin-bottom: 12px; }
.empty-chat h3 { margin: 0 0 6px; font-size: 16px; color: #666; }
.empty-chat p { margin: 0; font-size: 13px; }
.message-item { display: flex; }
.message-item.user { justify-content: flex-end; }
.message-item.assistant { justify-content: flex-start; }
.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
}
.user .message-bubble {
  background: linear-gradient(135deg, #4aa883, #2d8e69);
  color: white;
  border-bottom-right-radius: 4px;
}
.assistant .message-bubble {
  background: #f5f5f5;
  color: #333;
  border-bottom-left-radius: 4px;
}
.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 11px;
  opacity: 0.6;
}
.safety-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(255, 193, 7, 0.15);
  color: #b45309;
}
.typing {
  display: flex;
  gap: 4px;
  padding: 14px 18px;
}
.dot {
  width: 8px;
  height: 8px;
  background: #ccc;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
.input-area {
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
  background: white;
}
.input-area :deep(.ant-input-affix-wrapper) {
  border-radius: 24px;
  padding: 8px 8px 8px 18px;
}
</style>
