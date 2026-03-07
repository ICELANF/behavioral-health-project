<template>
  <div class="seekers-page">
    <div class="header-mini">服务对象</div>
    <div class="content">
      <!-- 统计卡 -->
      <div class="stat-row fu">
        <div class="stat-card">
          <div class="stat-num">{{ seekers.length }}</div>
          <div class="stat-label">总求助者</div>
        </div>
        <div class="stat-card">
          <div class="stat-num" style="color:var(--xzb-green)">{{ recentCount }}</div>
          <div class="stat-label">近7天活跃</div>
        </div>
        <div class="stat-card">
          <div class="stat-num" style="color:var(--xzb-blue)">{{ rxCount }}</div>
          <div class="stat-label">已开处方</div>
        </div>
      </div>

      <!-- 快捷入口 -->
      <div style="display:flex;gap:8px" class="fu fu-1">
        <button class="btn-outline" style="flex:1;text-align:center" @click="router.push('/faq')">常见问题库</button>
        <button class="btn-outline" style="flex:1;text-align:center" @click="router.push('/chat')">对话监控</button>
      </div>

      <!-- 求助者列表 -->
      <div class="card fu fu-2" v-if="seekers.length > 0">
        <div class="card-title">求助者列表</div>
        <div v-for="s in seekers" :key="s.seeker_id" class="s-item" @click="router.push(`/seekers/${s.seeker_id}`)">
          <div class="s-avatar">{{ (s.name || '?')[0] }}</div>
          <div class="s-body">
            <div class="s-name">
              {{ s.name }}
              <span v-if="s.stage" class="chip chip--teal">{{ s.stage }}</span>
              <span v-if="s.has_rx" class="chip chip--blue">Rx</span>
            </div>
            <div class="s-meta">
              {{ s.conv_count }} 次对话
              <template v-if="s.adherence_rate != null"> &middot; 依从率 {{ Math.round((s.adherence_rate || 0) * 100) }}%</template>
            </div>
          </div>
          <div class="s-time">{{ formatTime(s.last_conv_at) }}</div>
        </div>
      </div>

      <div class="card fu fu-2" v-else style="text-align:center;padding:32px">
        <div style="font-size:14px;font-weight:700;margin-bottom:6px">暂无服务对象</div>
        <div style="font-size:13px;color:var(--sub);line-height:1.6">
          当求助者通过智伴发起对话后，会自动出现在这里。
        </div>
      </div>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listSeekers } from '@/api/xzb'

const router = useRouter()

interface Seeker {
  seeker_id: number; name: string; conv_count: number
  last_conv_at: string | null; has_rx: boolean
  stage: string | null; adherence_rate: number | null
}

const seekers = ref<Seeker[]>([])

const recentCount = computed(() => {
  const cutoff = Date.now() - 7 * 86400000
  return seekers.value.filter(s => s.last_conv_at && new Date(s.last_conv_at).getTime() > cutoff).length
})

const rxCount = computed(() => seekers.value.filter(s => s.has_rx).length)

function formatTime(iso: string | null) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 86400000) return '今天'
  if (diff < 172800000) return '昨天'
  return `${d.getMonth() + 1}/${d.getDate()}`
}

onMounted(async () => {
  try {
    const res = await listSeekers()
    seekers.value = res.data.items || []
  } catch { seekers.value = [] }
})
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.stat-card {
  background: var(--card); border-radius: var(--radius-sm); padding: 14px 8px;
  text-align: center; box-shadow: var(--shadow-card);
}
.stat-num { font-size: 24px; font-weight: 900; color: var(--ink); }
.stat-label { font-size: 10px; color: var(--sub); margin-top: 4px; font-weight: 600; }
.s-item {
  display: flex; gap: 10px; padding: 12px 0;
  border-bottom: 1px dashed var(--border); cursor: pointer; align-items: center;
}
.s-item:last-child { border-bottom: none; }
.s-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: var(--xzb-primary-l); color: var(--xzb-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 900; flex-shrink: 0;
}
.s-body { flex: 1; min-width: 0; }
.s-name { font-size: 14px; font-weight: 700; display: flex; align-items: center; gap: 4px; }
.s-meta { font-size: 11px; color: var(--sub); margin-top: 2px; }
.s-time { font-size: 10px; color: var(--sub); flex-shrink: 0; }
</style>
