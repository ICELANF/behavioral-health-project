<template>
  <div class="pending-page">
    <div class="header-mini">
      <span @click="router.back()" style="cursor:pointer">&larr;</span>
      待确认知识
      <span class="chip chip--gold" style="margin-left:auto">{{ items.length }}</span>
    </div>
    <div class="content">
      <div v-if="items.length === 0" class="card fu" style="text-align:center;padding:32px">
        <div style="font-size:40px;margin-bottom:12px">OK</div>
        <div style="font-size:14px;font-weight:700">全部处理完毕！</div>
        <div style="font-size:13px;color:var(--sub)">没有待确认的知识条目。</div>
      </div>

      <div v-for="item in items" :key="item.id" class="card fu">
        <div style="font-size:12px;color:var(--sub);margin-bottom:6px">
          来源: {{ item.source || '对话沉淀' }}
        </div>
        <div style="font-size:13px;color:var(--ink);line-height:1.6;margin-bottom:12px">
          {{ item.content }}
        </div>
        <div style="font-size:11px;color:var(--sub);margin-bottom:10px">
          {{ item.created_at ? new Date(item.created_at).toLocaleDateString('zh-CN') : '' }}
        </div>
        <div style="display:flex;gap:8px">
          <button class="btn-outline" style="flex:1;text-align:center;color:var(--xzb-red);border-color:var(--xzb-red)" @click="handleAction(item.id, 'reject')">
            拒绝
          </button>
          <button class="btn-main" style="flex:1" @click="handleAction(item.id, 'confirm')">
            确认入库
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listPendingConfirm, confirmKnowledge } from '@/api/xzb'

const router = useRouter()

interface PendingItem {
  id: string; content: string; source: string; created_at: string | null
}

const items = ref<PendingItem[]>([])

async function loadData() {
  try {
    const res = await listPendingConfirm()
    items.value = res.data.items || []
  } catch { items.value = [] }
}

async function handleAction(id: string, action: 'confirm' | 'reject') {
  try {
    await confirmKnowledge(id, action)
    items.value = items.value.filter(i => i.id !== id)
  } catch { /* ignore */ }
}

onMounted(loadData)
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 10px;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
</style>
