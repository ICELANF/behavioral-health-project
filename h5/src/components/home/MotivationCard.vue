<template>
  <div class="motivation-card" v-if="!loading || hasData">
    <!-- 三个关键指标 -->
    <div class="moti-header">
      <span class="moti-title">执行统计</span>
    </div>
    <div class="moti-kpis">
      <div class="kpi-item">
        <span class="kpi-value fire">{{ currentStreak }}</span>
        <span class="kpi-unit">天</span>
        <span class="kpi-label">连续</span>
      </div>
      <div class="kpi-divider"></div>
      <div class="kpi-item">
        <span class="kpi-value blue">{{ tasksTotal }}</span>
        <span class="kpi-unit">个</span>
        <span class="kpi-label">累计完成</span>
      </div>
      <div class="kpi-divider"></div>
      <div class="kpi-item">
        <span class="kpi-value gold">{{ totalPoints }}</span>
        <span class="kpi-unit">分</span>
        <span class="kpi-label">总积分</span>
      </div>
    </div>

    <!-- 7日迷你折线图 -->
    <div class="moti-trend" v-if="weekTrend.length > 0">
      <div class="trend-header">
        <span class="trend-title">本周完成率</span>
        <span class="trend-pct">{{ latestPct }}%</span>
      </div>
      <div class="trend-chart" ref="chartRef"></div>
    </div>

    <!-- 最近成就 -->
    <div class="moti-badge" v-if="recentBadge">
      <span class="badge-label">最近成就:</span>
      <span class="badge-name">{{ recentBadge.name }}</span>
      <span class="badge-icon" v-if="recentBadge.icon">{{ recentBadge.icon }}</span>
    </div>

    <!-- 空状态 -->
    <div class="moti-empty" v-if="!hasData && !loading">
      <span class="empty-text">开始第一个任务吧</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useMotivation } from '@/composables/useMotivation'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, GridComponent, CanvasRenderer])

const {
  todayPoints, weekPoints, totalPoints, tasksTotal,
  currentStreak, longestStreak, weekTrend, recentBadge,
  loading, reload,
} = useMotivation()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const hasData = computed(() =>
  currentStreak.value > 0 || tasksTotal.value > 0 || totalPoints.value > 0
)

const latestPct = computed(() => {
  if (weekTrend.value.length === 0) return 0
  return weekTrend.value[weekTrend.value.length - 1].pct
})

function renderChart() {
  if (!chartRef.value || weekTrend.value.length === 0) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const dates = weekTrend.value.map(d => {
    const parts = d.date.split('-')
    return `${parts[1]}/${parts[2]}`
  })
  const values = weekTrend.value.map(d => d.pct)

  chartInstance.setOption({
    grid: { top: 4, right: 8, bottom: 4, left: 8, containLabel: false },
    xAxis: { type: 'category', data: dates, show: false },
    yAxis: { type: 'value', min: 0, max: 100, show: false },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: '#10b981' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(16,185,129,0.3)' },
          { offset: 1, color: 'rgba(16,185,129,0.02)' },
        ]),
      },
    }],
  })
}

watch(weekTrend, () => {
  nextTick(renderChart)
}, { deep: true })

onMounted(() => {
  nextTick(renderChart)
})

// expose reload for parent to call after checkin
defineExpose({ reload })
</script>

<style scoped>
.motivation-card {
  margin: 0 20px 16px;
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.moti-header {
  margin-bottom: 12px;
}

.moti-title {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}

/* ── KPI 三列 ── */
.moti-kpis {
  display: flex;
  align-items: center;
  justify-content: space-around;
  margin-bottom: 14px;
}

.kpi-item {
  text-align: center;
  flex: 1;
}

.kpi-value {
  font-size: 24px;
  font-weight: 900;
  line-height: 1;
}

.kpi-value.fire { color: #ef4444; }
.kpi-value.blue { color: #3b82f6; }
.kpi-value.gold { color: #d97706; }

.kpi-unit {
  font-size: 12px;
  color: #9ca3af;
  margin-left: 1px;
}

.kpi-label {
  display: block;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
}

.kpi-divider {
  width: 1px;
  height: 28px;
  background: #e5e7eb;
}

/* ── 趋势图 ── */
.moti-trend {
  margin-bottom: 10px;
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.trend-title {
  font-size: 13px;
  color: #6b7280;
}

.trend-pct {
  font-size: 14px;
  font-weight: 700;
  color: #10b981;
}

.trend-chart {
  width: 100%;
  height: 60px;
}

/* ── 最近成就 ── */
.moti-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fef3c7;
  border-radius: 10px;
  font-size: 13px;
}

.badge-label { color: #92400e; }
.badge-name { font-weight: 600; color: #78350f; }
.badge-icon { font-size: 16px; }

/* ── 空状态 ── */
.moti-empty {
  text-align: center;
  padding: 12px 0;
}

.empty-text {
  font-size: 13px;
  color: #9ca3af;
}
</style>
