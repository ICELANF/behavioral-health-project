<template>
  <div class="detail-page">
    <div class="header-mini">
      <span @click="router.back()" style="cursor:pointer">&larr;</span>
      {{ seeker?.name || '加载中...' }}
    </div>
    <div class="content" v-if="seeker">
      <!-- 基本信息 -->
      <div class="card fu">
        <div class="card-title">基本信息</div>
        <div class="info-grid">
          <div class="info-item">
            <div class="info-val">{{ seeker.stage || '-' }}</div>
            <div class="info-lbl">TTM阶段</div>
          </div>
          <div class="info-item">
            <div class="info-val">{{ seeker.adherence_rate != null ? Math.round(seeker.adherence_rate * 100) + '%' : '-' }}</div>
            <div class="info-lbl">依从率</div>
          </div>
          <div class="info-item">
            <div class="info-val">{{ seeker.health_competency || '-' }}</div>
            <div class="info-lbl">健康素养</div>
          </div>
          <div class="info-item">
            <div class="info-val">{{ seeker.trust_score != null ? Math.round(seeker.trust_score * 100) : '-' }}</div>
            <div class="info-lbl">信任分</div>
          </div>
        </div>
        <div v-if="seeker.chronic_conditions?.length" style="margin-top:10px">
          <div style="font-size:11px;color:var(--sub);margin-bottom:4px">慢性病</div>
          <div style="display:flex;gap:4px;flex-wrap:wrap">
            <span v-for="c in seeker.chronic_conditions" :key="c" class="chip chip--red">{{ c }}</span>
          </div>
        </div>
        <div v-if="seeker.goals?.length" style="margin-top:8px">
          <div style="font-size:11px;color:var(--sub);margin-bottom:4px">健康目标</div>
          <div style="display:flex;gap:4px;flex-wrap:wrap">
            <span v-for="g in seeker.goals" :key="g" class="chip chip--teal">{{ g }}</span>
          </div>
        </div>
      </div>

      <!-- 快捷操作 -->
      <div class="action-row fu fu-1">
        <button class="btn-main" style="flex:1" @click="router.push(`/rx/trigger/${seeker.seeker_id}`)">开处方</button>
        <button class="btn-outline" style="flex:1;text-align:center" @click="showConvs = !showConvs">
          {{ showConvs ? '收起对话' : `查看对话 (${seeker.conv_count})` }}
        </button>
      </div>

      <!-- 健康数据 -->
      <div class="card fu fu-1">
        <div class="card-title">健康数据摘要</div>
        <template v-if="health && health.has_data">
          <div v-if="health.glucose?.length" style="margin-bottom:10px">
            <div class="data-label">血糖 (近7次)</div>
            <div class="data-row">
              <div v-for="(g, i) in health.glucose" :key="i" class="data-point">
                <div class="data-val" :style="{ color: g.value > 10 ? 'var(--xzb-red)' : 'var(--xzb-green)' }">{{ g.value }}</div>
                <div class="data-time">{{ shortTime(g.time) }}</div>
              </div>
            </div>
          </div>
          <div v-if="health.weight?.length" style="margin-bottom:10px">
            <div class="data-label">体重 (近7次, kg)</div>
            <div class="data-row">
              <div v-for="(w, i) in health.weight" :key="i" class="data-point">
                <div class="data-val">{{ w.value }}</div>
                <div class="data-time">{{ shortTime(w.time) }}</div>
              </div>
            </div>
          </div>
          <div v-if="health.sleep?.length">
            <div class="data-label">睡眠 (近7次)</div>
            <div class="data-row">
              <div v-for="(s, i) in health.sleep" :key="i" class="data-point">
                <div class="data-val">{{ s.duration }}m</div>
                <div class="data-time">{{ shortTime(s.time) }}</div>
              </div>
            </div>
          </div>
        </template>
        <div v-else style="font-size:13px;color:var(--sub);text-align:center;padding:16px">
          暂无健康数据
        </div>
      </div>

      <!-- 对话列表 -->
      <div class="card fu fu-2" v-if="showConvs">
        <div class="card-title">对话记录</div>
        <div v-for="c in conversations" :key="c.id" class="conv-item" @click="router.push(`/chat/${c.id}`)">
          <div style="display:flex;align-items:center;gap:4px;margin-bottom:4px">
            <span v-if="c.ttm_stage" class="chip chip--teal">{{ c.ttm_stage }}</span>
            <span v-if="c.rx_triggered" class="chip chip--blue">Rx</span>
            <span v-if="c.expert_intervened" class="chip chip--gold">已介入</span>
            <span style="flex:1" />
            <span style="font-size:10px;color:var(--sub)">{{ shortTime(c.created_at) }}</span>
          </div>
          <div style="font-size:12px;color:var(--ink);line-height:1.5">{{ c.summary || '无摘要' }}</div>
        </div>
        <div v-if="conversations.length === 0" style="font-size:13px;color:var(--sub);text-align:center;padding:16px">
          暂无对话记录
        </div>
      </div>
    </div>
    <div style="height:20px" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSeekerDetail, getSeekerHealthSummary, listSeekerConversations } from '@/api/xzb'

const route = useRoute()
const router = useRouter()
const showConvs = ref(false)

interface SeekerInfo {
  seeker_id: number; name: string; gender: string | null
  stage: string | null; adherence_rate: number | null
  health_competency: string | null; trust_score: number | null
  chronic_conditions: string[]; goals: string[]
  conv_count: number; rx_count: number
}

interface HealthSummary {
  has_data: boolean
  glucose?: { value: number; time: string }[]
  weight?: { value: number; time: string }[]
  sleep?: { duration: number; quality: number; time: string }[]
}

interface Conv {
  id: string; summary: string; rx_triggered: boolean
  expert_intervened: boolean; ttm_stage: string | null
  created_at: string | null
}

const seeker = ref<SeekerInfo | null>(null)
const health = ref<HealthSummary | null>(null)
const conversations = ref<Conv[]>([])

function shortTime(iso: string | null) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

onMounted(async () => {
  const sid = Number(route.params.id)
  const [detailRes, healthRes, convsRes] = await Promise.allSettled([
    getSeekerDetail(sid),
    getSeekerHealthSummary(sid),
    listSeekerConversations(sid),
  ])
  if (detailRes.status === 'fulfilled') seeker.value = detailRes.value.data
  if (healthRes.status === 'fulfilled') health.value = healthRes.value.data
  if (convsRes.status === 'fulfilled') conversations.value = convsRes.value.data.items || []
})
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 10px;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.info-item { text-align: center; padding: 8px 0; }
.info-val { font-size: 18px; font-weight: 900; color: var(--xzb-primary); }
.info-lbl { font-size: 10px; color: var(--sub); margin-top: 2px; font-weight: 600; }
.action-row { display: flex; gap: 8px; }
.data-label { font-size: 12px; font-weight: 700; color: var(--sub); margin-bottom: 6px; }
.data-row { display: flex; gap: 6px; overflow-x: auto; }
.data-point {
  min-width: 44px; text-align: center; padding: 6px 4px;
  background: var(--bg); border-radius: 8px;
}
.data-val { font-size: 14px; font-weight: 800; }
.data-time { font-size: 9px; color: var(--sub); margin-top: 2px; }
.conv-item {
  padding: 10px 0; border-bottom: 1px dashed var(--border); cursor: pointer;
}
.conv-item:last-child { border-bottom: none; }
</style>
