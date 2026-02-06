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
import { ref } from 'vue'

const activeTab = ref('7d')

const chartTabs = [
  { key: '7d', label: '7天' },
  { key: '30d', label: '30天' },
  { key: '90d', label: '90天' },
]

const ttmTimeline = ref([
  { name: '前思考期', date: '2024-10-01', duration: '45天', color: '#ff4d4f', completed: true },
  { name: '思考期', date: '2024-11-15', duration: '30天', color: '#fa8c16', completed: true },
  { name: '准备期', date: '2024-12-15', duration: '15天', color: '#fadb14', completed: true },
  { name: '行动期', date: '2025-01-01', duration: '至今', color: '#52c41a', current: true },
  { name: '维持期', date: '', color: '#d9d9d9' },
  { name: '终止期', date: '', color: '#d9d9d9' },
])

const implicitData = ref([
  { icon: '📱', value: '45min', label: 'App日均使用', trend: '↑ 12%', trendClass: 'up' },
  { icon: '🚶', value: '6,850', label: '日均步数', trend: '↑ 8%', trendClass: 'up' },
  { icon: '😴', value: '6.8h', label: '平均睡眠', trend: '↑ 5%', trendClass: 'up' },
  { icon: '❤️', value: '72', label: '静息心率', trend: '↓ 3%', trendClass: 'down-good' },
])

const explicitData = ref([
  { icon: '📋', value: '3次', label: '本周测评', trend: '持平', trendClass: 'stable' },
  { icon: '✅', value: '85%', label: '任务完成率', trend: '↑ 10%', trendClass: 'up' },
  { icon: '💬', value: '12条', label: '本周对话', trend: '↑ 20%', trendClass: 'up' },
  { icon: '📖', value: '2篇', label: '阅读课程', trend: '↓ 1篇', trendClass: 'down' },
])

const heatmapData = ref([
  { label: '本周', days: [80, 65, 90, 45, 70, 85, 30] },
  { label: '上周', days: [60, 50, 75, 80, 55, 40, 20] },
  { label: '2周前', days: [40, 30, 55, 60, 45, 35, 15] },
  { label: '3周前', days: [25, 20, 40, 35, 30, 20, 10] },
])

const recentEvents = ref([
  { id: 1, text: '完成 PHQ-9 抑郁筛查测评', time: '今天 10:30', type: '测评', color: '#1890ff' },
  { id: 2, text: '连续第7天完成运动打卡', time: '今天 08:15', type: '打卡', color: '#52c41a' },
  { id: 3, text: '与AI教练完成一次对话', time: '昨天 20:00', type: '对话', color: '#722ed1' },
  { id: 4, text: '血糖值超过阈值告警', time: '昨天 14:30', type: '告警', color: '#ff4d4f' },
  { id: 5, text: '完成《压力管理入门》课程', time: '前天 16:00', type: '学习', color: '#fa8c16' },
])

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
