<template>
  <div class="device-dashboard">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">← 返回</button>
      <h2>穿戴设备数据</h2>
      <div class="period-tabs">
        <button v-for="p in periods" :key="p.key" class="period-tab" :class="{ active: activePeriod === p.key }" @click="activePeriod = p.key">{{ p.label }}</button>
      </div>
    </div>

    <!-- Real-time Cards -->
    <div class="metric-cards">
      <div v-for="card in metricCards" :key="card.key" class="metric-card" :style="{ borderColor: card.color }">
        <div class="card-header">
          <span class="card-icon">{{ card.icon }}</span>
          <span class="card-title">{{ card.title }}</span>
          <span v-if="card.alert" class="card-alert">!</span>
        </div>
        <div class="card-value" :style="{ color: card.color }">{{ card.value }}</div>
        <div class="card-unit">{{ card.unit }}</div>
        <div class="card-range">正常范围: {{ card.normalRange }}</div>
        <div class="card-trend" :class="card.trendClass">{{ card.trend }}</div>
      </div>
    </div>

    <!-- Heart Rate -->
    <div class="chart-section">
      <h3>心率变化 <span class="chart-hint">最近 {{ periodLabel }}</span></h3>
      <div class="simple-chart">
        <div class="chart-area">
          <div v-for="(val, i) in heartRateData" :key="i" class="chart-col">
            <div class="chart-point" :style="{ bottom: ((val - 50) / 60 * 100) + '%' }">
              <div class="point-dot" :style="{ background: val > 100 ? '#ff4d4f' : val < 55 ? '#faad14' : '#52c41a' }"></div>
            </div>
          </div>
        </div>
        <div class="chart-x-labels">
          <span v-for="(l, i) in chartLabels" :key="i">{{ l }}</span>
        </div>
      </div>
    </div>

    <!-- Sleep -->
    <div class="chart-section">
      <h3>睡眠分析</h3>
      <div class="sleep-bars">
        <div v-for="(day, i) in sleepData" :key="i" class="sleep-bar-col">
          <div class="sleep-bar">
            <div class="sleep-deep" :style="{ height: (day.deep / day.total * 100) + '%' }"></div>
            <div class="sleep-light" :style="{ height: (day.light / day.total * 100) + '%' }"></div>
            <div class="sleep-rem" :style="{ height: (day.rem / day.total * 100) + '%' }"></div>
          </div>
          <span class="sleep-label">{{ day.label }}</span>
          <span class="sleep-total">{{ day.total }}h</span>
        </div>
      </div>
      <div class="sleep-legend">
        <span class="legend-item"><span class="legend-dot" style="background: #1a237e"></span>深睡</span>
        <span class="legend-item"><span class="legend-dot" style="background: #5c6bc0"></span>浅睡</span>
        <span class="legend-item"><span class="legend-dot" style="background: #9fa8da"></span>REM</span>
      </div>
    </div>

    <!-- Steps -->
    <div class="chart-section">
      <h3>步数统计</h3>
      <div class="steps-bars">
        <div v-for="(day, i) in stepsData" :key="i" class="steps-bar-col">
          <div class="steps-bar" :style="{ height: (day.steps / 12000 * 100) + '%', background: day.steps >= 8000 ? '#52c41a' : '#faad14' }">
            <span class="steps-val">{{ (day.steps / 1000).toFixed(1) }}k</span>
          </div>
          <span class="steps-label">{{ day.label }}</span>
        </div>
      </div>
      <div class="steps-goal">目标: 8,000 步/天</div>
    </div>

    <!-- Blood Glucose -->
    <div class="chart-section">
      <h3>血糖监测 <span class="chart-hint">mmol/L</span></h3>
      <div class="glucose-timeline">
        <div v-for="(reading, i) in glucoseData" :key="i" class="glucose-item">
          <span class="glucose-time">{{ reading.time }}</span>
          <div class="glucose-bar-wrapper">
            <div class="glucose-bar" :style="{ width: (reading.value / 15 * 100) + '%', background: glucoseColor(reading.value) }"></div>
            <span class="glucose-val">{{ reading.value }}</span>
          </div>
          <span class="glucose-tag">{{ reading.tag }}</span>
        </div>
      </div>
      <div class="glucose-ranges">
        <span class="range-item low">低 &lt;3.9</span>
        <span class="range-item normal">正常 3.9-6.1</span>
        <span class="range-item high">偏高 6.1-7.8</span>
        <span class="range-item danger">危险 &gt;7.8</span>
      </div>
    </div>

    <!-- Blood Pressure -->
    <div class="chart-section">
      <h3>血压记录</h3>
      <div class="bp-records">
        <div v-for="(bp, i) in bpData" :key="i" class="bp-item">
          <span class="bp-date">{{ bp.date }}</span>
          <div class="bp-values">
            <span class="bp-sys" :style="{ color: bp.systolic > 140 ? '#ff4d4f' : '#333' }">{{ bp.systolic }}</span>
            <span class="bp-sep">/</span>
            <span class="bp-dia" :style="{ color: bp.diastolic > 90 ? '#ff4d4f' : '#333' }">{{ bp.diastolic }}</span>
            <span class="bp-unit">mmHg</span>
          </div>
          <span class="bp-pulse">{{ bp.pulse }} bpm</span>
        </div>
      </div>
    </div>

    <!-- Alert Thresholds -->
    <div class="chart-section">
      <h3>告警阈值设置</h3>
      <div class="threshold-list">
        <div v-for="t in thresholds" :key="t.key" class="threshold-item">
          <span class="threshold-name">{{ t.name }}</span>
          <span class="threshold-range">{{ t.low }} ~ {{ t.high }} {{ t.unit }}</span>
          <span class="threshold-status" :class="t.triggered ? 'triggered' : 'normal'">
            {{ t.triggered ? '已触发' : '正常' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { deviceApi } from '@/api/index'

const activePeriod = ref('7d')
const periods = [
  { key: '7d', label: '7天' },
  { key: '30d', label: '30天' },
  { key: '90d', label: '90天' },
]
const periodLabel = computed(() => periods.find(p => p.key === activePeriod.value)?.label || '')
const loading = ref(true)

const metricCards = ref([
  { key: 'hr', icon: '❤️', title: '心率', value: '--', unit: 'bpm', normalRange: '60-100', trend: '', trendClass: '', color: '#cf1322', alert: false },
  { key: 'sleep', icon: '😴', title: '睡眠', value: '--', unit: '小时', normalRange: '7-9h', trend: '', trendClass: '', color: '#1a237e', alert: false },
  { key: 'steps', icon: '🚶', title: '步数', value: '--', unit: '步', normalRange: '≥8000', trend: '', trendClass: '', color: '#389e0d', alert: false },
  { key: 'glucose', icon: '🩸', title: '空腹血糖', value: '--', unit: 'mmol/L', normalRange: '3.9-6.1', trend: '', trendClass: '', color: '#d46b08', alert: false },
  { key: 'bp', icon: '💓', title: '血压', value: '--', unit: 'mmHg', normalRange: '<140/90', trend: '', trendClass: '', color: '#722ed1', alert: false },
  { key: 'calories', icon: '🔥', title: '消耗', value: '--', unit: 'kcal', normalRange: '≥300', trend: '', trendClass: '', color: '#fa541c', alert: false },
])

const heartRateData = ref([])
const chartLabels = ref([])

const sleepData = ref([])

const stepsData = ref([])

const glucoseData = ref([])

const bpData = ref([])

const thresholds = ref([])

const glucoseColor = (val) => {
  if (val < 3.9) return '#faad14'
  if (val <= 6.1) return '#52c41a'
  if (val <= 7.8) return '#fa8c16'
  return '#ff4d4f'
}

function periodDays() {
  return activePeriod.value === '7d' ? 7 : activePeriod.value === '30d' ? 30 : 90
}

async function loadDeviceData() {
  loading.value = true
  const days = periodDays()
  const [summaryR, glucoseR, heartR, sleepR, stepsR] = await Promise.allSettled([
    deviceApi.getSummary(),
    deviceApi.getBloodGlucose(days),
    deviceApi.getHeartRate(days),
    deviceApi.getSleep(days),
    deviceApi.getSteps(days),
  ])

  if (summaryR.status === 'fulfilled' && summaryR.value) {
    const s = summaryR.value
    // Update metric cards from summary if data available
    if (s.heart_rate) metricCards.value[0].value = String(s.heart_rate)
    if (s.sleep_hours) metricCards.value[1].value = String(s.sleep_hours)
    if (s.steps) metricCards.value[2].value = String(s.steps).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
    if (s.fasting_glucose) metricCards.value[3].value = String(s.fasting_glucose)
    if (s.blood_pressure) metricCards.value[4].value = s.blood_pressure
    if (s.calories) metricCards.value[5].value = String(s.calories)
  }

  if (glucoseR.status === 'fulfilled' && Array.isArray(glucoseR.value) && glucoseR.value.length > 0) {
    glucoseData.value = glucoseR.value.map(r => ({
      time: r.time || r.measured_at || '',
      value: r.value ?? r.glucose_value ?? 0,
      tag: r.tag || (r.value <= 6.1 ? '正常' : r.value <= 7.8 ? '偏高' : '危险'),
    }))
  }

  if (heartR.status === 'fulfilled' && Array.isArray(heartR.value) && heartR.value.length > 0) {
    heartRateData.value = heartR.value.map(r => r.value ?? r.heart_rate ?? 70)
  }

  if (sleepR.status === 'fulfilled' && Array.isArray(sleepR.value) && sleepR.value.length > 0) {
    sleepData.value = sleepR.value.map(r => ({
      label: r.label || r.date || '',
      total: r.total ?? r.total_hours ?? 7,
      deep: r.deep ?? r.deep_hours ?? 2,
      light: r.light ?? r.light_hours ?? 3,
      rem: r.rem ?? r.rem_hours ?? 1.5,
    }))
  }

  if (stepsR.status === 'fulfilled' && Array.isArray(stepsR.value) && stepsR.value.length > 0) {
    stepsData.value = stepsR.value.map(r => ({
      label: r.label || r.date || '',
      steps: r.steps ?? r.step_count ?? 0,
    }))
  }

  loading.value = false
}

watch(activePeriod, loadDeviceData)
onMounted(loadDeviceData)
</script>

<style scoped>
.device-dashboard { max-width: 640px; margin: 0 auto; padding: 16px; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.page-header h2 { flex: 1; margin: 0; font-size: 18px; }
.back-btn { padding: 6px 16px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; }
.period-tabs { display: flex; gap: 4px; }
.period-tab { padding: 4px 12px; border: 1px solid #d9d9d9; border-radius: 16px; background: #fff; cursor: pointer; font-size: 12px; }
.period-tab.active { background: #1890ff; color: #fff; border-color: #1890ff; }

.metric-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 16px; }
.metric-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 10px; padding: 12px; border-left: 3px solid; }
.card-header { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; }
.card-icon { font-size: 16px; }
.card-title { font-size: 12px; color: #999; flex: 1; }
.card-alert { width: 18px; height: 18px; background: #ff4d4f; color: #fff; border-radius: 50%; font-size: 11px; text-align: center; line-height: 18px; }
.card-value { font-size: 22px; font-weight: 700; }
.card-unit { font-size: 11px; color: #999; }
.card-range { font-size: 10px; color: #bbb; margin-top: 2px; }
.card-trend { font-size: 11px; margin-top: 2px; }
.card-trend.up { color: #389e0d; }
.card-trend.down-good { color: #389e0d; }
.card-trend.down { color: #cf1322; }

.chart-section { background: #fff; border: 1px solid #f0f0f0; border-radius: 10px; padding: 16px; margin-bottom: 12px; }
.chart-section h3 { font-size: 15px; margin: 0 0 12px; color: #333; }
.chart-hint { font-size: 12px; color: #999; font-weight: 400; }

.simple-chart { height: 120px; position: relative; }
.chart-area { display: flex; height: 100px; align-items: flex-end; gap: 2px; }
.chart-col { flex: 1; height: 100%; position: relative; }
.chart-point { position: absolute; left: 50%; transform: translateX(-50%); }
.point-dot { width: 8px; height: 8px; border-radius: 50%; }
.chart-x-labels { display: flex; justify-content: space-between; font-size: 9px; color: #ccc; }

.sleep-bars { display: flex; gap: 8px; height: 120px; align-items: flex-end; }
.sleep-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.sleep-bar { width: 100%; max-width: 30px; display: flex; flex-direction: column; border-radius: 4px 4px 0 0; overflow: hidden; }
.sleep-deep { background: #1a237e; }
.sleep-light { background: #5c6bc0; }
.sleep-rem { background: #9fa8da; }
.sleep-label { font-size: 10px; color: #999; margin-top: 4px; }
.sleep-total { font-size: 10px; color: #333; font-weight: 500; }
.sleep-legend { display: flex; gap: 12px; justify-content: center; margin-top: 8px; }
.legend-item { font-size: 11px; color: #666; display: flex; align-items: center; gap: 4px; }
.legend-dot { width: 10px; height: 10px; border-radius: 2px; }

.steps-bars { display: flex; gap: 8px; height: 100px; align-items: flex-end; }
.steps-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.steps-bar { width: 100%; max-width: 32px; border-radius: 4px 4px 0 0; position: relative; min-height: 4px; }
.steps-val { position: absolute; top: -16px; left: 50%; transform: translateX(-50%); font-size: 9px; font-weight: 600; white-space: nowrap; }
.steps-label { font-size: 10px; color: #999; margin-top: 4px; }
.steps-goal { font-size: 11px; color: #999; text-align: center; margin-top: 8px; border-top: 1px dashed #e8e8e8; padding-top: 4px; }

.glucose-timeline { display: flex; flex-direction: column; gap: 6px; }
.glucose-item { display: flex; align-items: center; gap: 8px; }
.glucose-time { font-size: 11px; color: #999; min-width: 90px; }
.glucose-bar-wrapper { flex: 1; height: 16px; background: #f5f5f5; border-radius: 4px; overflow: hidden; position: relative; }
.glucose-bar { height: 100%; border-radius: 4px; transition: width 0.3s; }
.glucose-val { position: absolute; right: 4px; top: 50%; transform: translateY(-50%); font-size: 10px; font-weight: 600; }
.glucose-tag { font-size: 11px; min-width: 36px; text-align: center; }
.glucose-ranges { display: flex; gap: 8px; justify-content: center; margin-top: 8px; font-size: 10px; }
.range-item { padding: 2px 6px; border-radius: 3px; }
.range-item.low { background: #fffbe6; color: #ad8b00; }
.range-item.normal { background: #f6ffed; color: #389e0d; }
.range-item.high { background: #fff7e6; color: #d46b08; }
.range-item.danger { background: #fff1f0; color: #cf1322; }

.bp-records { display: flex; flex-direction: column; gap: 8px; }
.bp-item { display: flex; align-items: center; gap: 12px; padding: 8px; background: #fafafa; border-radius: 6px; }
.bp-date { font-size: 12px; color: #999; min-width: 100px; }
.bp-values { flex: 1; }
.bp-sys { font-size: 20px; font-weight: 700; }
.bp-sep { font-size: 16px; color: #999; margin: 0 2px; }
.bp-dia { font-size: 20px; font-weight: 700; }
.bp-unit { font-size: 11px; color: #999; margin-left: 4px; }
.bp-pulse { font-size: 12px; color: #666; }

.threshold-list { display: flex; flex-direction: column; gap: 6px; }
.threshold-item { display: flex; align-items: center; gap: 12px; padding: 8px; background: #fafafa; border-radius: 6px; }
.threshold-name { font-size: 13px; color: #333; min-width: 80px; }
.threshold-range { flex: 1; font-size: 12px; color: #999; }
.threshold-status { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.threshold-status.normal { background: #f6ffed; color: #389e0d; }
.threshold-status.triggered { background: #fff1f0; color: #cf1322; }
</style>
