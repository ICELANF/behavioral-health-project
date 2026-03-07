<template>
  <div class="chat-page">
    <div class="header-mini">对话监控</div>
    <div class="content">
      <div v-if="conversations.length > 0">
        <div v-for="c in conversations" :key="c.id" class="card fu"
          @click="router.push(`/chat/${c.id}`)" style="cursor:pointer;margin-bottom:10px">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
            <div class="s-avatar">{{ (c.seeker_name || '?')[0] }}</div>
            <div style="flex:1">
              <div style="font-size:14px;font-weight:700">{{ c.seeker_name }}</div>
            </div>
            <span v-if="c.expert_intervened" class="chip chip--gold">已介入</span>
            <span v-if="c.rx_triggered" class="chip chip--blue">Rx</span>
          </div>
          <div style="font-size:12px;color:var(--ink);line-height:1.5;margin-bottom:4px">{{ c.summary || '无摘要' }}</div>
          <div style="font-size:10px;color:var(--sub)">{{ formatTime(c.created_at) }}</div>
        </div>
      </div>

      <div v-else class="card fu" style="text-align:center;padding:32px">
        <div style="font-size:40px;margin-bottom:12px">AI</div>
        <div style="font-size:15px;font-weight:700;margin-bottom:6px">AI 智伴对话监控</div>
        <div style="font-size:13px;color:var(--sub);line-height:1.6">
          您的 AI 智伴与求助者的对话将显示在这里。您可以随时介入或发送异步回复。
        </div>
      </div>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listExpertConversations } from '@/api/xzb'

const router = useRouter()

interface Conv {
  id: string; seeker_id: number; seeker_name: string
  summary: string; rx_triggered: boolean; expert_intervened: boolean
  created_at: string | null
}

const conversations = ref<Conv[]>([])

function formatTime(iso: string | null) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(async () => {
  try {
    const res = await listExpertConversations()
    conversations.value = res.data.items || []
  } catch { conversations.value = [] }
})
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 0; }
.s-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--xzb-primary-l); color: var(--xzb-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 900; flex-shrink: 0;
}
</style>
