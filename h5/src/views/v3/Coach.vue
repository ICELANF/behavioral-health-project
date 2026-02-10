<template>
  <div class="coach-page">
    <van-nav-bar title="AI 健康教练" left-arrow @click-left="$router.back()" />

    <div class="messages" ref="msgBox">
      <div v-for="(m, i) in messages" :key="i" :class="['bubble-row', m.role]">
        <div class="bubble">
          <div class="text">{{ m.content }}</div>
          <div class="meta" v-if="m.model">
            <span>{{ m.model }}</span>
            <span v-if="m.latency">· {{ m.latency }}ms</span>
          </div>
        </div>
      </div>
      <div v-if="loading" class="bubble-row assistant">
        <div class="bubble typing">
          <van-loading size="18" />
          <span style="margin-left:8px;">思考中...</span>
        </div>
      </div>
    </div>

    <div class="input-bar">
      <van-field v-model="input" placeholder="输入消息..." @keyup.enter="send" class="msg-input">
        <template #button>
          <van-button size="small" type="primary" @click="send" :disabled="!input.trim() || loading">
            发送
          </van-button>
        </template>
      </van-field>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
// v3 store stub
const useUserStore = () => ({ userId: 0, token: localStorage.getItem('access_token') })
// v3 API stub - TODO: wire up
const chatApi = { message: async () => ({ data: { data: { answer: '功能开发中...', intent: 'pending', model: '', sources: [] } } }) }

const store = useUserStore()
const input = ref('')
const loading = ref(false)
const msgBox = ref(null)
const messages = ref([
  { role: 'assistant', content: `你好 ${store.nickname}！我是你的 AI 健康教练，有什么可以帮助你的？` },
])

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  scrollBottom()

  loading.value = true
  try {
    // 构建历史 (最近 10 轮)
    const history = messages.value.slice(-20).map(m => ({
      role: m.role, content: m.content,
    }))
    history.pop() // 去掉刚加的 user 消息 (会在 message 参数传)

    const res = await chatApi.send(store.userId, text, {
      history: history.length > 1 ? history.slice(0, -1) : undefined,
      behavioral_stage: store.stage,
    })

    if (res.ok) {
      messages.value.push({
        role: 'assistant',
        content: res.data.answer,
        model: res.data.model,
        latency: res.data.latency_ms,
        intent: res.data.intent,
      })
    } else {
      messages.value.push({ role: 'assistant', content: '抱歉，遇到了问题，请稍后再试。' })
    }
  } catch {
    messages.value.push({ role: 'assistant', content: '网络错误，请检查连接。' })
  } finally {
    loading.value = false
    scrollBottom()
  }
}

function scrollBottom() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}
</script>

<style scoped>
.coach-page { display: flex; flex-direction: column; height: 100vh; background: #f0f2f5; }
.messages { flex: 1; overflow-y: auto; padding: 12px; padding-bottom: 70px; }
.bubble-row { display: flex; margin-bottom: 12px; }
.bubble-row.user { justify-content: flex-end; }
.bubble-row.assistant { justify-content: flex-start; }
.bubble { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 15px; line-height: 1.5; }
.user .bubble { background: #667eea; color: #fff; border-bottom-right-radius: 4px; }
.assistant .bubble { background: #fff; color: #333; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
.meta { font-size: 11px; color: #999; margin-top: 4px; }
.user .meta { color: rgba(255,255,255,0.7); }
.typing { display: flex; align-items: center; }
.input-bar { position: fixed; bottom: 50px; left: 0; right: 0; background: #fff; border-top: 1px solid #eee; padding: 6px 8px; }
.msg-input { background: #f7f8fa; border-radius: 20px; }
</style>
