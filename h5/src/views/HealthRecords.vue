<template>
  <div class="page-container">
    <van-nav-bar title="健康档案" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <!-- 用户基本信息 -->
      <div class="card info-card">
        <h3>基本信息</h3>
        <van-cell-group :border="false">
          <van-cell title="姓名" :value="userInfo.full_name || '--'" />
          <van-cell title="用户名" :value="userInfo.username || '--'" />
          <van-cell title="邮箱" :value="userInfo.email || '--'" />
          <van-cell title="角色" :value="roleLabel" />
        </van-cell-group>
      </div>

      <!-- 今日健康概览 -->
      <div class="card">
        <h3>今日健康概览</h3>
        <van-loading v-if="loadingHealth" class="loading" />
        <template v-else>
          <van-grid :column-num="3" :border="false">
            <van-grid-item v-for="item in healthItems" :key="item.label">
              <template #icon>
                <van-icon :name="item.icon" :color="item.color" size="24" />
              </template>
              <template #text>
                <div class="data-value">{{ item.value }}</div>
                <div class="data-label">{{ item.label }}</div>
              </template>
            </van-grid-item>
          </van-grid>
        </template>
      </div>

      <!-- 血糖趋势图 -->
      <div class="card">
        <h3>血糖趋势 <span class="sub-text">近14天</span></h3>
        <van-loading v-if="loadingGlucose" class="loading" />
        <div v-else-if="glucoseList.length" ref="glucoseChartRef" class="chart-box"></div>
        <van-empty v-else description="暂无血糖记录" image-size="60" />
      </div>

      <!-- 血压趋势图 -->
      <div class="card">
        <h3>血压趋势 <span class="sub-text">近14天</span></h3>
        <van-loading v-if="loadingBP" class="loading" />
        <div v-else-if="bpList.length" ref="bpChartRef" class="chart-box"></div>
        <van-empty v-else description="暂无血压记录" image-size="60" />
      </div>

      <!-- 体重趋势图 -->
      <div class="card">
        <h3>体重趋势 <span class="sub-text">近14天</span></h3>
        <van-loading v-if="loadingWeight" class="loading" />
        <div v-else-if="weightList.length" ref="weightChartRef" class="chart-box"></div>
        <van-empty v-else description="暂无体重记录" image-size="60" />
      </div>

      <!-- 心率趋势图 -->
      <div class="card">
        <h3>心率趋势 <span class="sub-text">近7天</span></h3>
        <van-loading v-if="loadingHR" class="loading" />
        <div v-else-if="hrData.length" ref="hrChartRef" class="chart-box"></div>
        <van-empty v-else description="暂无心率记录" image-size="60" />
      </div>

      <!-- 睡眠趋势图 -->
      <div class="card">
        <h3>睡眠趋势 <span class="sub-text">近14天</span></h3>
        <van-loading v-if="loadingSleep" class="loading" />
        <div v-else-if="sleepData.length" ref="sleepChartRef" class="chart-box chart-box-tall"></div>
        <van-empty v-else description="暂无睡眠记录" image-size="60" />
      </div>

      <!-- 活动趋势图 -->
      <div class="card">
        <h3>活动趋势 <span class="sub-text">近14天</span></h3>
        <van-loading v-if="loadingActivity" class="loading" />
        <div v-else-if="activityData.length" ref="activityChartRef" class="chart-box"></div>
        <van-empty v-else description="暂无活动记录" image-size="60" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/api/index'
import storage from '@/utils/storage'

const ROLE_MAP: Record<string, string> = {
  admin: '管理员', coach: '健康教练', grower: '成长者',
  observer: '观察员', supervisor: '督导', promoter: '推广者', master: '大师'
}

// 每日配色方案 (14天循环)
const DAY_COLORS = [
  '#1989fa', '#07c160', '#ff976a', '#ee0a24', '#7c3aed',
  '#f59e0b', '#10b981', '#ef4444', '#6366f1', '#ec4899',
  '#14b8a6', '#f97316', '#8b5cf6', '#06b6d4'
]

const userInfo = ref<Record<string, any>>({})
const healthData = ref<any>(null)
const glucoseList = ref<any[]>([])
const bpList = ref<any[]>([])
const weightList = ref<any[]>([])
const hrData = ref<any[]>([])
const sleepData = ref<any[]>([])
const activityData = ref<any[]>([])

const loadingHealth = ref(false)
const loadingGlucose = ref(false)
const loadingBP = ref(false)
const loadingWeight = ref(false)
const loadingHR = ref(false)
const loadingSleep = ref(false)
const loadingActivity = ref(false)

const glucoseChartRef = ref<HTMLElement>()
const bpChartRef = ref<HTMLElement>()
const weightChartRef = ref<HTMLElement>()
const hrChartRef = ref<HTMLElement>()
const sleepChartRef = ref<HTMLElement>()
const activityChartRef = ref<HTMLElement>()

const charts: echarts.ECharts[] = []

const roleLabel = computed(() => ROLE_MAP[userInfo.value.role] || userInfo.value.role || '--')

const healthItems = computed(() => {
  const d = healthData.value || {}
  const sleep = d.sleep || {}
  const weight = d.weight || {}
  const glucose = d.glucose || {}
  const activity = d.activity || {}
  return [
    { label: '睡眠', value: sleep.duration_hours ? sleep.duration_hours + 'h' : '--', icon: 'clock-o', color: '#7c3aed' },
    { label: '睡眠评分', value: sleep.score || '--', icon: 'star-o', color: '#6366f1' },
    { label: '血糖', value: glucose.current ? glucose.current + '' : '--', icon: 'column', color: '#ff976a' },
    { label: '体重', value: weight.weight_kg ? weight.weight_kg + 'kg' : '--', icon: 'balance-o', color: '#1989fa' },
    { label: 'BMI', value: weight.bmi || '--', icon: 'chart-trending-o', color: '#07c160' },
    { label: '步数', value: activity.steps || '--', icon: 'guide-o', color: '#10b981' },
  ]
})

function initChart(el: HTMLElement): echarts.ECharts {
  const chart = echarts.init(el)
  charts.push(chart)
  return chart
}

function shortDate(str: string) {
  if (!str) return ''
  return str.slice(5, 10) // MM-DD
}

// ---- 血糖图：按日分组，同一时刻不同天叠加对比 ----
function renderGlucoseChart() {
  if (!glucoseChartRef.value || !glucoseList.value.length) return
  const chart = initChart(glucoseChartRef.value)

  // 按日期分组
  const byDate: Record<string, { time: string; value: number }[]> = {}
  for (const r of glucoseList.value) {
    const dateStr = r.recorded_at.slice(0, 10)
    if (!byDate[dateStr]) byDate[dateStr] = []
    byDate[dateStr].push({
      time: r.recorded_at.slice(11, 16),
      value: r.value
    })
  }

  const dates = Object.keys(byDate).sort()
  const series: any[] = dates.map((d, i) => ({
    name: shortDate(d),
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { width: 2 },
    itemStyle: { color: DAY_COLORS[i % DAY_COLORS.length] },
    data: byDate[d].sort((a, b) => a.time.localeCompare(b.time)).map(p => [p.time, p.value])
  }))

  chart.setOption({
    tooltip: { trigger: 'item', formatter: (p: any) => `${p.seriesName} ${p.data[0]}<br/>血糖: <b>${p.data[1]}</b> mmol/L` },
    legend: { data: dates.map(shortDate), bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 45, right: 15, top: 30, bottom: 40 },
    xAxis: { type: 'category', name: '时间', axisLabel: { fontSize: 10 } },
    yAxis: {
      type: 'value', name: 'mmol/L', min: 3, axisLabel: { fontSize: 10 },
      splitLine: { lineStyle: { type: 'dashed' } },
      // 正常范围标记
    },
    visualMap: { show: false },
    series,
  })

  // 添加正常范围标记带
  chart.setOption({
    yAxis: {
      type: 'value', name: 'mmol/L', min: 3,
    },
    series: [
      ...series,
      {
        name: '正常范围',
        type: 'line',
        markArea: {
          silent: true,
          itemStyle: { color: 'rgba(7, 193, 96, 0.08)' },
          data: [[{ yAxis: 3.9 }, { yAxis: 10.0 }]]
        },
        data: []
      }
    ]
  })
}

// ---- 血压图：收缩压/舒张压双线 ----
function renderBPChart() {
  if (!bpChartRef.value || !bpList.value.length) return
  const chart = initChart(bpChartRef.value)

  const sorted = [...bpList.value].sort((a, b) => a.recorded_at.localeCompare(b.recorded_at))
  const xData = sorted.map(r => shortDate(r.recorded_at))

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        let s = params[0].axisValue
        params.forEach(p => { s += `<br/>${p.marker} ${p.seriesName}: <b>${p.value}</b>` })
        return s
      }
    },
    legend: { data: ['收缩压', '舒张压', '脉搏'], bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 45, right: 15, top: 30, bottom: 40 },
    xAxis: { type: 'category', data: xData, axisLabel: { fontSize: 10, rotate: 30 } },
    yAxis: { type: 'value', name: 'mmHg', axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { type: 'dashed' } } },
    series: [
      {
        name: '收缩压', type: 'line', smooth: true, symbol: 'circle', symbolSize: 5,
        data: sorted.map(r => r.systolic),
        itemStyle: { color: '#ee0a24' }, lineStyle: { width: 2 },
        markLine: { silent: true, symbol: 'none', lineStyle: { type: 'dashed', color: '#ee0a2440' }, data: [{ yAxis: 140, label: { formatter: '高压线 140' } }] }
      },
      {
        name: '舒张压', type: 'line', smooth: true, symbol: 'circle', symbolSize: 5,
        data: sorted.map(r => r.diastolic),
        itemStyle: { color: '#1989fa' }, lineStyle: { width: 2 },
        markLine: { silent: true, symbol: 'none', lineStyle: { type: 'dashed', color: '#1989fa40' }, data: [{ yAxis: 90, label: { formatter: '高压线 90' } }] }
      },
      {
        name: '脉搏', type: 'line', smooth: true, symbol: 'diamond', symbolSize: 4,
        data: sorted.map(r => r.pulse),
        itemStyle: { color: '#ff976a' }, lineStyle: { width: 1.5, type: 'dashed' }
      }
    ]
  })
}

// ---- 体重图：折线 + BMI 双轴 ----
function renderWeightChart() {
  if (!weightChartRef.value || !weightList.value.length) return
  const chart = initChart(weightChartRef.value)

  const sorted = [...weightList.value].sort((a, b) => (a.recorded_at || '').localeCompare(b.recorded_at || ''))
  const xData = sorted.map(r => shortDate(r.recorded_at))

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        let s = params[0].axisValue
        params.forEach(p => {
          const unit = p.seriesName === 'BMI' ? '' : ' kg'
          s += `<br/>${p.marker} ${p.seriesName}: <b>${p.value}</b>${unit}`
        })
        return s
      }
    },
    legend: { data: ['体重', 'BMI', '体脂率'], bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 50, right: 50, top: 30, bottom: 40 },
    xAxis: { type: 'category', data: xData, axisLabel: { fontSize: 10, rotate: 30 } },
    yAxis: [
      { type: 'value', name: 'kg', axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { type: 'dashed' } } },
      { type: 'value', name: 'BMI / %', axisLabel: { fontSize: 10 }, splitLine: { show: false } }
    ],
    series: [
      {
        name: '体重', type: 'line', smooth: true, symbol: 'circle', symbolSize: 6,
        data: sorted.map(r => r.weight_kg),
        itemStyle: { color: '#1989fa' }, lineStyle: { width: 2.5 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#1989fa30' }, { offset: 1, color: '#1989fa05' }]) }
      },
      {
        name: 'BMI', type: 'line', smooth: true, yAxisIndex: 1, symbol: 'diamond', symbolSize: 5,
        data: sorted.map(r => r.bmi),
        itemStyle: { color: '#07c160' }, lineStyle: { width: 1.5, type: 'dashed' }
      },
      {
        name: '体脂率', type: 'line', smooth: true, yAxisIndex: 1, symbol: 'triangle', symbolSize: 5,
        data: sorted.map(r => r.body_fat_percent),
        itemStyle: { color: '#ff976a' }, lineStyle: { width: 1.5, type: 'dotted' }
      }
    ]
  })
}

// ---- 心率图：按日分组多色线 ----
function renderHRChart() {
  if (!hrChartRef.value || !hrData.value.length) return
  const chart = initChart(hrChartRef.value)

  // 按日期分组
  const byDate: Record<string, { time: string; hr: number }[]> = {}
  for (const r of hrData.value) {
    const dateStr = r.timestamp.slice(0, 10)
    if (!byDate[dateStr]) byDate[dateStr] = []
    byDate[dateStr].push({ time: r.timestamp.slice(11, 16), hr: r.hr })
  }

  const dates = Object.keys(byDate).sort()
  const series: any[] = dates.map((d, i) => ({
    name: shortDate(d),
    type: 'line',
    smooth: true,
    symbol: 'none',
    lineStyle: { width: 2 },
    itemStyle: { color: DAY_COLORS[i % DAY_COLORS.length] },
    data: byDate[d].sort((a, b) => a.time.localeCompare(b.time)).map(p => [p.time, p.hr])
  }))

  chart.setOption({
    tooltip: { trigger: 'item', formatter: (p: any) => `${p.seriesName} ${p.data[0]}<br/>心率: <b>${p.data[1]}</b> bpm` },
    legend: { data: dates.map(shortDate), bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 45, right: 15, top: 30, bottom: 40 },
    xAxis: { type: 'category', name: '时间', axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: 'bpm', min: 50, axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { type: 'dashed' } } },
    series
  })
}

// ---- 睡眠图：堆叠柱状图（深睡/浅睡/REM/清醒）+ 评分折线 ----
function renderSleepChart() {
  if (!sleepChartRef.value || !sleepData.value.length) return
  const chart = initChart(sleepChartRef.value)

  const sorted = [...sleepData.value].sort((a, b) => (a.date || '').localeCompare(b.date || ''))
  const xData = sorted.map(r => shortDate(r.date))

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        let s = params[0].axisValue
        params.forEach(p => {
          const unit = p.seriesName === '评分' ? '分' : '分钟'
          s += `<br/>${p.marker} ${p.seriesName}: <b>${p.value || 0}</b> ${unit}`
        })
        return s
      }
    },
    legend: { data: ['深睡', '浅睡', 'REM', '清醒', '评分'], bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 45, right: 45, top: 30, bottom: 45 },
    xAxis: { type: 'category', data: xData, axisLabel: { fontSize: 10, rotate: 30 } },
    yAxis: [
      { type: 'value', name: '分钟', axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { type: 'dashed' } } },
      { type: 'value', name: '评分', min: 0, max: 100, axisLabel: { fontSize: 10 }, splitLine: { show: false } }
    ],
    series: [
      { name: '深睡', type: 'bar', stack: 'sleep', data: sorted.map(r => r.stages?.deep_min || 0), itemStyle: { color: '#3b3f9f' } },
      { name: '浅睡', type: 'bar', stack: 'sleep', data: sorted.map(r => r.stages?.light_min || 0), itemStyle: { color: '#7986cb' } },
      { name: 'REM', type: 'bar', stack: 'sleep', data: sorted.map(r => r.stages?.rem_min || 0), itemStyle: { color: '#ce93d8' } },
      { name: '清醒', type: 'bar', stack: 'sleep', data: sorted.map(r => r.stages?.awake_min || 0), itemStyle: { color: '#ffcc80' } },
      {
        name: '评分', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'circle', symbolSize: 6,
        data: sorted.map(r => r.sleep_score),
        itemStyle: { color: '#ee0a24' }, lineStyle: { width: 2 }
      }
    ]
  })
}

// ---- 活动图：步数柱状 + 卡路里折线 ----
function renderActivityChart() {
  if (!activityChartRef.value || !activityData.value.length) return
  const chart = initChart(activityChartRef.value)

  const sorted = [...activityData.value].sort((a, b) => (a.date || '').localeCompare(b.date || ''))
  const xData = sorted.map(r => shortDate(r.date))

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        let s = params[0].axisValue
        params.forEach(p => {
          const unit = p.seriesName === '步数' ? '步' : (p.seriesName === '活动分钟' ? '分钟' : 'kcal')
          s += `<br/>${p.marker} ${p.seriesName}: <b>${p.value || 0}</b> ${unit}`
        })
        return s
      }
    },
    legend: { data: ['步数', '活跃卡路里', '活动分钟'], bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 50, right: 50, top: 30, bottom: 40 },
    xAxis: { type: 'category', data: xData, axisLabel: { fontSize: 10, rotate: 30 } },
    yAxis: [
      { type: 'value', name: '步', axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { type: 'dashed' } } },
      { type: 'value', name: 'kcal/min', axisLabel: { fontSize: 10 }, splitLine: { show: false } }
    ],
    series: [
      {
        name: '步数', type: 'bar', data: sorted.map(r => r.steps),
        itemStyle: {
          color: (params: any) => {
            const v = params.value
            if (v >= 10000) return '#07c160'
            if (v >= 6000) return '#1989fa'
            return '#ff976a'
          }
        },
        markLine: { silent: true, symbol: 'none', lineStyle: { type: 'dashed', color: '#07c16060' }, data: [{ yAxis: 10000, label: { formatter: '目标 1万步' } }] }
      },
      {
        name: '活跃卡路里', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'circle', symbolSize: 5,
        data: sorted.map(r => r.calories_active),
        itemStyle: { color: '#ee0a24' }, lineStyle: { width: 2 }
      },
      {
        name: '活动分钟', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'diamond', symbolSize: 5,
        data: sorted.map(r => r.active_minutes),
        itemStyle: { color: '#7c3aed' }, lineStyle: { width: 1.5, type: 'dashed' }
      }
    ]
  })
}

// ---- resize handler ----
function handleResize() {
  charts.forEach(c => c.resize())
}

onMounted(async () => {
  window.addEventListener('resize', handleResize)

  // 用户信息
  const cached = storage.getAuthUser()
  if (cached) userInfo.value = cached
  try {
    const res: any = await api.get('/api/v1/auth/me')
    userInfo.value = res
  } catch {}

  // 今日健康概览
  loadingHealth.value = true
  try {
    const res: any = await api.get('/api/v1/mp/device/dashboard/today')
    healthData.value = res
  } catch {} finally { loadingHealth.value = false }

  // 血糖
  loadingGlucose.value = true
  try {
    const res: any = await api.get('/api/v1/mp/device/glucose', { params: { limit: 200 } })
    glucoseList.value = res.readings || res.data || res || []
  } catch {} finally { loadingGlucose.value = false }

  // 血压
  loadingBP.value = true
  try {
    const res: any = await api.get('/api/v1/mp/device/blood-pressure', { params: { limit: 50 } })
    bpList.value = res.records || res.data || res || []
  } catch {} finally { loadingBP.value = false }

  // 体重
  loadingWeight.value = true
  try {
    const res: any = await api.get('/api/v1/mp/device/weight', { params: { limit: 30 } })
    weightList.value = res.records || res.data || res || []
  } catch {} finally { loadingWeight.value = false }

  // 心率
  loadingHR.value = true
  try {
    const res: any = await api.get('/api/v1/mp/device/heart-rate', { params: { limit: 200 } })
    hrData.value = res.readings || res.data || res || []
  } catch {} finally { loadingHR.value = false }

  // 睡眠
  loadingSleep.value = true
  try {
    const res: any = await api.get('/api/v1/mp/device/sleep', { params: { limit: 14 } })
    sleepData.value = res.records || res.data || res || []
  } catch {} finally { loadingSleep.value = false }

  // 活动
  loadingActivity.value = true
  try {
    const res: any = await api.get('/api/v1/mp/device/activity')
    activityData.value = res.records || res.data || res || []
  } catch {} finally { loadingActivity.value = false }

  // 数据加载完后渲染图表
  await nextTick()
  renderGlucoseChart()
  renderBPChart()
  renderWeightChart()
  renderHRChart()
  renderSleepChart()
  renderActivityChart()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  charts.forEach(c => c.dispose())
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.card {
  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
    display: flex;
    align-items: baseline;
    gap: 6px;

    .sub-text {
      font-size: $font-size-xs;
      color: $text-color-secondary;
      font-weight: 400;
    }
  }
}

.loading {
  text-align: center;
  padding: $spacing-lg 0;
}

.chart-box {
  width: 100%;
  height: 260px;
}

.chart-box-tall {
  height: 300px;
}

.data-value {
  font-size: $font-size-md;
  font-weight: bold;
  color: $text-color;
}

.data-label {
  font-size: $font-size-xs;
  color: $text-color-secondary;
}
</style>
