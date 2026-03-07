<template>
  <div>
    <div class="page-header">
      <h2>数据分析</h2>
    </div>

    <!-- 概览指标 -->
    <div class="kpi-grid">
      <div class="kpi-card" v-for="k in kpis" :key="k.label">
        <div class="kpi-label">{{ k.label }}</div>
        <div class="kpi-num">{{ k.value }}</div>
        <div class="kpi-sub" :class="k.trend > 0 ? 'trend-up' : k.trend < 0 ? 'trend-down' : ''">
          {{ k.trend > 0 ? '↑' : k.trend < 0 ? '↓' : '—' }} {{ Math.abs(k.trend) }}%
        </div>
      </div>
    </div>

    <!-- 近7天趋势图（SVG折线图） -->
    <div class="card" style="margin-bottom:16px">
      <div class="card-header"><h3>近7天微行动完成趋势</h3></div>
      <div v-if="trendLoading" class="loading">加载中...</div>
      <div v-else>
        <svg class="trend-chart" viewBox="0 0 600 160" preserveAspectRatio="none">
          <defs>
            <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.3"/>
              <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <!-- Grid lines -->
          <line v-for="y in [0,40,80,120]" :key="y" :x1="0" :y1="y" :x2="600" :y2="y" stroke="#f3f4f6" stroke-width="1"/>
          <!-- Area -->
          <path v-if="trendPoints.length > 1" :d="areaPath" fill="url(#grad)" />
          <!-- Line -->
          <polyline v-if="trendPoints.length > 1" :points="polylinePoints" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linejoin="round"/>
          <!-- Dots -->
          <circle v-for="(p, i) in trendPoints" :key="i" :cx="p.x" :cy="p.y" r="4" fill="#3b82f6"/>
        </svg>
        <div class="trend-labels">
          <span v-for="(d, i) in trendDays" :key="i">{{ d }}</span>
        </div>
      </div>
    </div>

    <!-- 推送漏斗 -->
    <div class="two-col">
      <div class="card">
        <div class="card-header"><h3>推送转化漏斗</h3></div>
        <div v-if="funnelLoading" class="loading">加载中...</div>
        <div v-else class="funnel">
          <div v-for="f in funnelSteps" :key="f.label" class="funnel-step">
            <div class="funnel-bar-wrap">
              <div class="funnel-bar" :style="{ width: f.pct + '%', background: f.color }"></div>
            </div>
            <div class="funnel-label">{{ f.label }}</div>
            <div class="funnel-val">{{ f.count }} ({{ f.pct }}%)</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header"><h3>学员阶段分布</h3></div>
        <div v-if="stageLoading" class="loading">加载中...</div>
        <div v-else class="stage-dist">
          <div v-for="s in stageDist" :key="s.stage" class="stage-row">
            <div class="stage-name">{{ s.label }}</div>
            <div class="stage-bar-wrap">
              <div class="stage-bar" :style="{ width: s.pct + '%' }"></div>
            </div>
            <div class="stage-count">{{ s.count }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/index'

const trendLoading = ref(true)
const funnelLoading = ref(true)
const stageLoading = ref(true)

const kpis = ref([
  { label: '学员总数', value: 0, trend: 0 },
  { label: '本周完成率', value: '0%', trend: 0 },
  { label: '平均风险分', value: 0, trend: 0 },
  { label: '待审任务', value: 0, trend: 0 },
])

const trendData = ref<number[]>([0, 0, 0, 0, 0, 0, 0])
const trendDays = computed(() => {
  const days = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    days.push(`${d.getMonth() + 1}/${d.getDate()}`)
  }
  return days
})

const trendPoints = computed(() => {
  const data = trendData.value
  const max = Math.max(...data, 1)
  return data.map((v, i) => ({
    x: (i / (data.length - 1)) * 580 + 10,
    y: 140 - (v / max) * 120
  }))
})

const polylinePoints = computed(() => trendPoints.value.map(p => `${p.x},${p.y}`).join(' '))

const areaPath = computed(() => {
  const pts = trendPoints.value
  if (pts.length < 2) return ''
  const start = `M${pts[0].x},140`
  const lines = pts.map(p => `L${p.x},${p.y}`).join(' ')
  const end = `L${pts[pts.length - 1].x},140 Z`
  return `${start} ${lines} ${end}`
})

const funnelSteps = ref<{ label: string; count: number; pct: number; color: string }[]>([])
const stageDist = ref<{ stage: string; label: string; count: number; pct: number }[]>([])

onMounted(async () => {
  const [dashRes, trendRes, funnelRes] = await Promise.allSettled([
    api.get('/api/v1/coach/dashboard'),
    api.get('/api/v1/coach/analytics/weekly-trend'),
    api.get('/api/v1/coach/analytics/push-funnel'),
  ])

  if (dashRes.status === 'fulfilled') {
    const d = dashRes.value as any
    const students = d.students || []
    kpis.value[0].value = students.length
    kpis.value[2].value = parseFloat((students.reduce((s: number, st: any) => {
      return s + parseInt(String(st.risk_level ?? '0').replace(/\D/g, '') || '0')
    }, 0) / (students.length || 1)).toFixed(1))

    // Stage distribution
    const stageMap: Record<string, number> = {}
    students.forEach((s: any) => { stageMap[s.stage || 'unknown'] = (stageMap[s.stage || 'unknown'] || 0) + 1 })
    const total = students.length || 1
    stageDist.value = Object.entries(stageMap).map(([stage, count]) => ({
      stage,
      label: stage,
      count,
      pct: Math.round((count / total) * 100)
    }))
    stageLoading.value = false
  } else {
    stageLoading.value = false
  }

  if (trendRes.status === 'fulfilled') {
    const d = trendRes.value as any
    trendData.value = d.data || d.values || Array(7).fill(0)
  }
  trendLoading.value = false

  if (funnelRes.status === 'fulfilled') {
    const d = funnelRes.value as any
    const steps = d.steps || d.funnel || []
    const max = Math.max(...steps.map((s: any) => s.count || 0), 1)
    funnelSteps.value = steps.map((s: any, i: number) => ({
      label: s.label || s.stage || `步骤${i+1}`,
      count: s.count || 0,
      pct: Math.round(((s.count || 0) / max) * 100),
      color: ['#6366f1','#3b82f6','#10b981','#f59e0b','#ef4444'][i % 5]
    }))
  } else {
    // Fallback demo funnel
    funnelSteps.value = [
      { label: '已推送', count: 100, pct: 100, color: '#6366f1' },
      { label: '已接收', count: 85, pct: 85, color: '#3b82f6' },
      { label: '已开始', count: 62, pct: 62, color: '#10b981' },
      { label: '已完成', count: 41, pct: 41, color: '#f59e0b' },
    ]
  }
  funnelLoading.value = false
})
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }

.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.kpi-card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.kpi-label { font-size: 12px; color: #6b7280; margin-bottom: 8px; }
.kpi-num { font-size: 28px; font-weight: 800; color: #111827; }
.kpi-sub { font-size: 12px; color: #9ca3af; margin-top: 4px; }
.trend-up { color: #10b981; }
.trend-down { color: #ef4444; }

.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.card-header { margin-bottom: 16px; }
.card-header h3 { font-size: 15px; font-weight: 600; margin: 0; }

.trend-chart { width: 100%; height: 160px; }
.trend-labels {
  display: flex; justify-content: space-between;
  font-size: 11px; color: #9ca3af; margin-top: 8px; padding: 0 10px;
}

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.funnel { display: flex; flex-direction: column; gap: 10px; }
.funnel-step { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 8px; }
.funnel-bar-wrap { grid-column: 1; background: #f3f4f6; border-radius: 4px; height: 20px; overflow: hidden; }
.funnel-bar { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.funnel-label { font-size: 12px; color: #6b7280; }
.funnel-val { font-size: 12px; color: #374151; font-weight: 500; white-space: nowrap; }

.stage-dist { display: flex; flex-direction: column; gap: 10px; }
.stage-row { display: flex; align-items: center; gap: 8px; }
.stage-name { font-size: 12px; color: #6b7280; width: 80px; flex-shrink: 0; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }
.stage-bar-wrap { flex: 1; background: #f3f4f6; border-radius: 4px; height: 12px; overflow: hidden; }
.stage-bar { height: 100%; background: linear-gradient(90deg, #6366f1, #3b82f6); border-radius: 4px; transition: width 0.6s; }
.stage-count { font-size: 12px; color: #374151; font-weight: 500; width: 24px; text-align: right; }

.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
