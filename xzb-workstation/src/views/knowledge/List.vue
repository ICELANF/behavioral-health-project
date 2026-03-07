<template>
  <div class="knowledge-page">
    <div class="header-mini">知识库</div>
    <div class="content">
      <div class="filter-row fu">
        <div v-for="f in filters" :key="f.key"
          class="filter-chip" :class="{ sel: activeFilter === f.key }"
          @click="activeFilter = f.key; loadData()">{{ f.label }}</div>
      </div>

      <div style="display:flex;gap:8px" class="fu fu-1">
        <button class="btn-main" style="flex:1" @click="router.push('/knowledge/upload')">+ 上传知识</button>
        <button class="btn-outline" @click="router.push('/knowledge/pending')">
          待确认 ({{ pendingCount }})
        </button>
      </div>

      <div class="card fu fu-2" v-if="items.length > 0">
        <div v-for="item in items" :key="item.id" class="k-item" @click="viewItem(item)">
          <div class="k-type" :style="{ background: typeColor(item.type) }">{{ typeIcon(item.type) }}</div>
          <div class="k-body">
            <div class="k-tags">
              <span v-for="t in (item.tags || []).slice(0,3)" :key="t" class="chip chip--teal">{{ t }}</span>
              <span class="chip" :class="item.expert_confirmed ? 'chip--teal' : 'chip--red'">
                {{ item.expert_confirmed ? '已确认' : '待确认' }}
              </span>
            </div>
            <div class="k-meta">
              证据等级: {{ item.evidence_tier }} &middot; 使用 {{ item.usage_count }} 次
            </div>
          </div>
        </div>
      </div>

      <div class="card fu fu-2" v-else style="text-align:center;padding:32px">
        <div style="font-size:40px;margin-bottom:12px">KB</div>
        <div style="font-size:14px;font-weight:700;margin-bottom:6px">知识库为空</div>
        <div style="font-size:13px;color:var(--sub);line-height:1.6">
          上传您的第一条临床知识，开始构建专属知识体系。
        </div>
      </div>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listKnowledge, listPendingConfirm } from '@/api/xzb'

const router = useRouter()

interface KItem {
  id: string; type: string; tags: string[]; evidence_tier: string
  usage_count: number; expert_confirmed: boolean
}

const items = ref<KItem[]>([])
const pendingCount = ref(0)
const activeFilter = ref('all')

const filters = [
  { key: 'all', label: '全部' },
  { key: 'clinical_note', label: '临床笔记' },
  { key: 'evidence', label: '循证依据' },
  { key: 'template', label: '处方模板' },
  { key: 'faq', label: '常见问答' },
]

function typeColor(t: string) {
  const m: Record<string, string> = {
    clinical_note: 'var(--xzb-primary-l)', evidence: '#EEF4FF',
    template: 'var(--xzb-gold-l)', faq: '#F3F0FF',
  }
  return m[t] || 'var(--border)'
}

function typeIcon(t: string) {
  const m: Record<string, string> = { clinical_note: '临', evidence: '证', template: '方', faq: '问' }
  return m[t] || '知'
}

async function loadData() {
  try {
    const params: Record<string, unknown> = {}
    if (activeFilter.value !== 'all') params.type = activeFilter.value
    const res = await listKnowledge(params)
    items.value = res.data.items || []
  } catch { items.value = [] }
}

async function loadPending() {
  try {
    const res = await listPendingConfirm()
    pendingCount.value = res.data.count || 0
  } catch { /* ignore */ }
}

function viewItem(item: KItem) {
  router.push(`/knowledge?id=${item.id}`)
}

onMounted(() => { loadData(); loadPending() })
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.filter-row { display: flex; gap: 6px; overflow-x: auto; }
.filter-chip {
  padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;
  border: 1.5px solid var(--border); color: var(--sub); cursor: pointer;
  white-space: nowrap; transition: all .2s;
}
.filter-chip.sel { border-color: var(--xzb-primary); background: var(--xzb-primary-l); color: var(--xzb-primary); }
.k-item {
  display: flex; gap: 10px; padding: 12px 0;
  border-bottom: 1px dashed var(--border); cursor: pointer;
}
.k-item:last-child { border-bottom: none; }
.k-type {
  width: 42px; height: 42px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 900; flex-shrink: 0;
}
.k-body { flex: 1; min-width: 0; }
.k-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 4px; }
.k-meta { font-size: 11px; color: var(--sub); }
</style>
