<template>
  <div class="chat-detail">
    <div class="header-mini">
      <span @click="router.back()" style="cursor:pointer">&larr;</span>
      会话 {{ (route.params.id as string).slice(0, 8) }}
      <span v-if="conv?.expert_intervened" class="chip chip--gold" style="margin-left:auto">已介入</span>
    </div>
    <div class="content">
      <div class="card fu">
        <div class="card-title">对话摘要</div>
        <div style="font-size:13px;color:var(--ink);line-height:1.6">
          {{ conv?.summary || '加载中...' }}
        </div>
      </div>

      <div class="card fu fu-1">
        <div class="card-title">专家操作</div>
        <textarea class="text-input" rows="3" v-model="replyContent" placeholder="输入您的回复或介入内容..." />
        <div style="display:flex;gap:8px;margin-top:10px">
          <button class="btn-outline" style="flex:1;text-align:center" @click="sendReply">异步回复</button>
          <button class="btn-main" style="flex:1" @click="intervene">接管对话</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getChatHistory, expertIntervene, asyncReply } from '@/api/xzb'

const route = useRoute()
const router = useRouter()
const replyContent = ref('')

interface ConvData {
  conversation_id: string; summary: string; rx_triggered: boolean; expert_intervened: boolean
}

const conv = ref<ConvData | null>(null)

onMounted(async () => {
  try {
    const res = await getChatHistory(route.params.id as string)
    conv.value = res.data
  } catch { /* not found */ }
})

async function sendReply() {
  if (!replyContent.value.trim()) return
  try {
    await asyncReply(route.params.id as string, replyContent.value)
    replyContent.value = ''
    alert('回复已发送')
  } catch { alert('发送失败') }
}

async function intervene() {
  if (!replyContent.value.trim()) return
  try {
    await expertIntervene(route.params.id as string, replyContent.value)
    replyContent.value = ''
    if (conv.value) conv.value.expert_intervened = true
    alert('已接管对话')
  } catch { alert('操作失败') }
}
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 10px;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.text-input {
  width: 100%; border: 1.5px solid var(--border); border-radius: 12px;
  padding: 12px; font-size: 13px; resize: none; outline: none;
  color: var(--ink); line-height: 1.6;
}
</style>
