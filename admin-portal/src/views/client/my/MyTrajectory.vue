<template>
  <div class="my-trajectory">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">← 返回</button>
      <h2>行为轨迹</h2>
    </div>

    <!-- TTM Stage Timeline -->
    <div class="section">
      <h3 class="section-title">TTM 阶段时间线</h3>
      <div class="timeline">
        <div v-for="(stage, i) in ttmTimeline" :key="i" class="timeline-item" :class="{ current: stage.current, completed: stage.completed }">
          <div class="timeline-dot" :style="{ background: stage.color }"></div>
          <div class="timeline-line" v-if="i < ttmTimeline.length - 1"></div>
          <div class="timeline-content">
            <span class="timeline-stage">{{ stage.name }}</span>
            <span class="timeline-date">{{ stage.date }}</span>
            <span v-if="stage.duration" class="timeline-duration">持续 {{ stage.duration }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Combined Data Chart -->
    <div class="section">
      <h3 class="section-title">行为数据组合</h3>
      <div class="chart-tabs">
        <button v-for="tab in chartTabs" :key="tab.key" class="chart-tab" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
          {{ tab.label }}
        </button>
      </div>

      <!-- Implicit data -->
      <div class="data-panel">
        <h4 class="panel-title">隐性数据（自动采集）</h4>
        <div class="data-grid">
          <div v-for="item in implicitData" :key="item.label" class="data-card">
            <span class="data-icon">{{ item.icon }}</span>
            <span class="data-val">{{ item.value }}</span>
            <span class="data-label">{{ item.label }}</span>
            <span class="data-trend" :class="item.trendClass">{{ item.trend }}</span>
          </div>
        </div>
      </div>

      <!-- Explicit data -->
      <div class="data-panel">
        <h4 class="panel-title">显性数据（主动行为）</h4>
        <div class="data-grid">
          <div v-for="item in explicitData" :key="item.label" class="data-card">
            <span class="data-icon">{{ item.icon }}</span>
            <span class="data-val">{{ item.value }}</span>
            <span class="data-label">{{ item.label }}</span>
            <span class="data-trend" :class="item.trendClass">{{ item.trend }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Weekly Activity Heatmap -->
    <div class="section">
      <h3 class="section-title">周活跃热力图</h3>
      <div class="heatmap">
        <div class="heatmap-row" v-for="(week, wi) in heatmapData" :key="wi">
          <span class="heatmap-label">{{ week.label }}</span>
          <div v-for="(val, di) in week.days" :key="di" class="heatmap-cell" :style="{ background: heatColor(val) }" :title="`活跃度: ${val}`"></div>
        </div>
        <div class="heatmap-legend">
          <span>低</span>
          <div class="legend-cells">
            <div v-for="n in 5" :key="n" class="legend-cell" :style="{ background: heatColor((n-1) * 25) }"></div>
          </div>
          <span>高</span>
        </div>
      </div>
    </div>

    <!-- Recent Events -->
    <div class="section">
      <h3 class="section-title">近期行为事件</h3>
      <div v-for="event in recentEvents" :key="event.id" class="event-item">
        <div class="event-dot" :style="{ background: event.color }"></div>
        <div class="event-content">
          <span class="event-text">{{ event.text }}</span>
          <span class="event-time">{{ event.time }}</span>
        </div>
        <span class="event-type">{{ event.type }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/request'

const activeTab = ref('7d')

const chartTabs = [
  { key: '7d', label: '7天' },
  { key: '30d', label: '30天' },
  { key: '90d', label: '90天' },
]

const ttmTimeline = ref([])
const implicitData = ref([])
const explicitData = ref([])
const heatmapData = ref([])
const recentEvents = ref([])

const stageColors = { S0: '#d9d9d9', S1: '#bfbfbf', S2: '#91d5ff', S3: '#69c0ff', S4: '#40a9ff', S5: '#1890ff', S6: '#52c41a' }
const stageNames = { S0: '觉醒期', S1: '松动期', S2: '探索期', S3: '准备期', S4: '行动期', S5: '坚持期', S6: '融入期' }

onMounted(async () => {
  if (!localStorage.getItem('admin_token')) return
  // Load TTM stage from assessment profile
  try {
    const res = await request.get('v1/assessment/profile/me')
    const profile = res.data
    const currentStage = profile?.stage || profile?.current_stage || 'S0'
    const stages = ['S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6']
    const currentIdx = stages.indexOf(currentStage)
    ttmTimeline.value = stages.map((s, i) => ({
      name: stageNames[s] || s,
      date: i <= currentIdx ? (profile?.stage_dates?.[s] || '') : '',
      duration: i < currentIdx ? '' : undefined,
      current: i === currentIdx,
      completed: i < currentIdx,
      color: i <= currentIdx ? (stageColors[s] || '#1890ff') : '#e8e8e8',
    }))
  } catch {
    // Fallback — show empty timeline
    ttmTimeline.value = Object.entries(stageNames).map(([k, v], i) => ({
      name: v, date: '', current: i === 0, completed: false, color: i === 0 ? '#1890ff' : '#e8e8e8',
    }))
  }

  // Load credit events as timeline
  try {
    const res = await request.get('v1/credits/my/records', { params: { page_size: 10 } })
    const records = res.data?.records || res.data?.items || (Array.isArray(res.data) ? res.data : [])
    const eventColors = { learning: '#1890ff', checkin: '#52c41a', assessment: '#722ed1', promotion: '#faad14' }
    recentEvents.value = records.slice(0, 8).map((r, i) => ({
      id: i, text: r.description || r.event_type || '行为事件',
      time: (r.created_at || '').slice(0, 16).replace('T', ' '),
      type: r.event_type || '记录',
      color: eventColors[r.event_type] || '#1890ff',
    }))
  } catch { /* keep empty */ }

  // Load daily task history for heatmap
  try {
    const res = await request.get('v1/daily-tasks/history', { params: { days: 28 } })
    const history = res.data?.history || res.data || []
    const weekLabels = ['本周', '上周', '两周前', '三周前']
    const weeks = []
    for (let w = 0; w < 4; w++) {
      const weekDays = history.slice(w * 7, (w + 1) * 7)
      weeks.push({
        label: weekLabels[w] || `W${w}`,
        days: weekDays.length > 0
          ? weekDays.map(d => Math.round((d.completed || d.done_count || 0) / Math.max(d.total || d.task_count || 1, 1) * 100))
          : [0, 0, 0, 0, 0, 0, 0],
      })
    }
    heatmapData.value = weeks
  } catch {
    heatmapData.value = [
      { label: '本周', days: [0, 0, 0, 0, 0, 0, 0] },
      { label: '上周', days: [0, 0, 0, 0, 0, 0, 0] },
    ]
  }

  // Load device summary for implicit/explicit data
  try {
    const res = await request.get('v1/mp/device/dashboard/today')
    const d = res.data || {}
    implicitData.value = [
      { icon: '🩸', value: d.glucose_latest ?? '--', label: '血糖', trend: '', trendClass: 'stable' },
      { icon: '⚖️', value: d.weight_latest ?? '--', label: '体重', trend: '', trendClass: 'stable' },
      { icon: '❤️', value: d.hr_latest ?? '--', label: '心率', trend: '', trendClass: 'stable' },
      { icon: '😴', value: d.sleep_hours ?? '--', label: '睡眠(h)', trend: '', trendClass: 'stable' },
    ]
    explicitData.value = [
      { icon: '🏃', value: d.activity_minutes ?? '0', label: '运动(min)', trend: '', trendClass: 'stable' },
      { icon: '📝', value: d.checkin_count ?? '0', label: '今日打卡', trend: '', trendClass: 'up' },
    ]
  } catch { /* keep empty */ }
})

const heatColor = (val) => {
  if (val >= 80) return '#389e0d'
  if (val >= 60) return '#95de64'
  if (val >= 40) return '#d9f7be'
  if (val >= 20) return '#f0f5ff'
  return '#f5f5f5'
}
</script>

<style scoped>
.my-trajectory { max-width: 600px; margin: 0 auto; padding: 16px; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { flex: 1; margin: 0; font-size: 18px; }
.back-btn { padding: 6px 16px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; }

.section { margin-bottom: 20px; }
.section-title { font-size: 15px; font-weight: 600; color: #333; margin: 0 0 12px; }

.timeline { position: relative; padding-left: 20px; }
.timeline-item { position: relative; padding-bottom: 16px; padding-left: 16px; }
.timeline-dot { width: 12px; height: 12px; border-radius: 50%; position: absolute; left: -6px; top: 4px; z-index: 1; }
.timeline-item.current .timeline-dot { box-shadow: 0 0 0 4px rgba(82, 196, 26, 0.2); }
.timeline-line { position: absolute; left: -1px; top: 16px; bottom: -4px; width: 2px; background: #e8e8e8; }
.timeline-content { display: flex; flex-direction: column; gap: 2px; }
.timeline-stage { font-size: 14px; font-weight: 500; color: #333; }
.timeline-date { font-size: 12px; color: #999; }
.timeline-duration { font-size: 11px; color: #1890ff; }
.timeline-item:not(.completed):not(.current) .timeline-stage { color: #ccc; }

.chart-tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.chart-tab { padding: 4px 16px; border: 1px solid #d9d9d9; border-radius: 16px; background: #fff; cursor: pointer; font-size: 13px; }
.chart-tab.active { background: #1890ff; color: #fff; border-color: #1890ff; }

.data-panel { margin-bottom: 12px; }
.panel-title { font-size: 13px; color: #666; margin: 0 0 8px; }
.data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.data-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.data-icon { font-size: 20px; }
.data-val { font-size: 16px; font-weight: 600; color: #333; }
.data-label { font-size: 11px; color: #999; }
.data-trend { font-size: 11px; }
.data-trend.up { color: #389e0d; }
.data-trend.down { color: #cf1322; }
.data-trend.down-good { color: #389e0d; }
.data-trend.stable { color: #999; }

.heatmap { background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; padding: 12px; }
.heatmap-row { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; }
.heatmap-label { font-size: 11px; color: #999; min-width: 50px; text-align: right; padding-right: 4px; }
.heatmap-cell { width: 100%; height: 20px; border-radius: 3px; flex: 1; }
.heatmap-legend { display: flex; align-items: center; justify-content: flex-end; gap: 4px; margin-top: 4px; font-size: 10px; color: #999; }
.legend-cells { display: flex; gap: 2px; }
.legend-cell { width: 16px; height: 12px; border-radius: 2px; }

.event-item { display: flex; align-items: center; gap: 10px; padding: 10px; background: #fff; border: 1px solid #f0f0f0; border-radius: 6px; margin-bottom: 6px; }
.event-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.event-content { flex: 1; }
.event-text { display: block; font-size: 13px; color: #333; }
.event-time { font-size: 11px; color: #999; }
.event-type { font-size: 11px; padding: 2px 8px; background: #f5f5f5; border-radius: 4px; color: #666; }
</style>
