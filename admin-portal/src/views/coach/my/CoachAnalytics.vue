<template>
  <div class="coach-analytics">
    <div class="page-header">
      <h2>数据分析</h2>
      <a-radio-group v-model:value="days" button-style="solid" @change="fetchAll">
        <a-radio-button :value="7">近7天</a-radio-button>
        <a-radio-button :value="14">近14天</a-radio-button>
        <a-radio-button :value="30">近30天</a-radio-button>
      </a-radio-group>
    </div>

    <a-row :gutter="[16, 16]">
      <!-- 学员风险等级趋势 -->
      <a-col :span="12">
        <a-card title="学员风险等级趋势" :bordered="false">
          <a-spin :spinning="loading.risk">
            <div v-if="isEmpty.risk"><a-empty description="暂无风险数据" /></div>
            <div v-else ref="riskChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
      <!-- 微行动完成率趋势 -->
      <a-col :span="12">
        <a-card title="微行动完成率趋势" :bordered="false">
          <a-spin :spinning="loading.micro">
            <div v-if="isEmpty.micro"><a-empty description="暂无微行动数据" /></div>
            <div v-else ref="microChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
      <!-- 领域表现对比 -->
      <a-col :span="12">
        <a-card title="领域表现对比" :bordered="false">
          <a-spin :spinning="loading.domain">
            <div v-if="isEmpty.domain"><a-empty description="暂无领域数据" /></div>
            <div v-else ref="domainChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
      <!-- 预警频率分布 -->
      <a-col :span="12">
        <a-card title="预警频率分布" :bordered="false">
          <a-spin :spinning="loading.alert">
            <div v-if="isEmpty.alert"><a-empty description="暂无预警数据" /></div>
            <div v-else ref="alertChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
      <!-- 挑战报名与完成 -->
      <a-col :span="12">
        <a-card title="挑战报名与完成" :bordered="false">
          <a-spin :spinning="loading.challenge">
            <div v-if="isEmpty.challenge"><a-empty description="暂无挑战数据" /></div>
            <div v-else ref="challengeChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
      <!-- 学员阶段分布 -->
      <a-col :span="12">
        <a-card title="学员阶段分布" :bordered="false">
          <a-spin :spinning="loading.stage">
            <div v-if="isEmpty.stage"><a-empty description="暂无阶段数据" /></div>
            <div v-else ref="stageChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import request from '../../../api/request'

const days = ref(30)

const riskChartRef = ref<HTMLElement>()
const microChartRef = ref<HTMLElement>()
const domainChartRef = ref<HTMLElement>()
const alertChartRef = ref<HTMLElement>()
const challengeChartRef = ref<HTMLElement>()
const stageChartRef = ref<HTMLElement>()

const charts: echarts.ECharts[] = []

const loading = ref({
  risk: false, micro: false, domain: false,
  alert: false, challenge: false, stage: false,
})
const isEmpty = ref({
  risk: false, micro: false, domain: false,
  alert: false, challenge: false, stage: false,
})

function initChart(el: HTMLElement | undefined): echarts.ECharts | null {
  if (!el) return null
  const c = echarts.init(el)
  charts.push(c)
  return c
}

async function fetchRiskTrend() {
  loading.value.risk = true
  try {
    const res = await request.get('v1/analytics/coach/risk-trend', { params: { days: days.value } })
    const d = res.data
    isEmpty.value.risk = !d.dates?.length
    if (isEmpty.value.risk) return
    await nextTick()
    const chart = initChart(riskChartRef.value)
    chart?.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['低风险', '中风险', '高风险'] },
      xAxis: { type: 'category', data: d.dates },
      yAxis: { type: 'value' },
      series: [
        { name: '低风险', type: 'line', stack: 'risk', areaStyle: {}, data: d.low, itemStyle: { color: '#52c41a' } },
        { name: '中风险', type: 'line', stack: 'risk', areaStyle: {}, data: d.medium, itemStyle: { color: '#faad14' } },
        { name: '高风险', type: 'line', stack: 'risk', areaStyle: {}, data: d.high, itemStyle: { color: '#ff4d4f' } },
      ],
    })
  } catch { isEmpty.value.risk = true } finally { loading.value.risk = false }
}

async function fetchMicroTrend() {
  loading.value.micro = true
  try {
    const res = await request.get('v1/analytics/coach/micro-action-trend', { params: { days: days.value } })
    const d = res.data
    isEmpty.value.micro = !d.dates?.length
    if (isEmpty.value.micro) return
    await nextTick()
    const chart = initChart(microChartRef.value)
    chart?.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['完成率(%)'] },
      xAxis: { type: 'category', data: d.dates },
      yAxis: { type: 'value', max: 100 },
      series: [
        {
          name: '完成率(%)', type: 'line',
          data: d.rate,
          areaStyle: { color: 'rgba(24, 144, 255, 0.15)' },
          itemStyle: { color: '#1890ff' },
          smooth: true,
        },
      ],
    })
  } catch { isEmpty.value.micro = true } finally { loading.value.micro = false }
}

async function fetchDomainPerformance() {
  loading.value.domain = true
  try {
    const res = await request.get('v1/analytics/coach/domain-performance', { params: { days: days.value } })
    const d = res.data
    isEmpty.value.domain = !d.domains?.length
    if (isEmpty.value.domain) return
    await nextTick()
    const chart = initChart(domainChartRef.value)
    const domainLabels: Record<string, string> = {
      nutrition: '营养', exercise: '运动', sleep: '睡眠', emotion: '情绪',
      stress: '压力', cognitive: '认知', social: '社交',
    }
    chart?.setOption({
      tooltip: {},
      radar: {
        indicator: d.domains.map((dom: string) => ({
          name: domainLabels[dom] || dom, max: 100,
        })),
      },
      series: [{
        type: 'radar',
        data: [{
          value: d.rates,
          name: '完成率',
          areaStyle: { color: 'rgba(24, 144, 255, 0.2)' },
          lineStyle: { color: '#1890ff' },
          itemStyle: { color: '#1890ff' },
        }],
      }],
    })
  } catch { isEmpty.value.domain = true } finally { loading.value.domain = false }
}

async function fetchAlertFrequency() {
  loading.value.alert = true
  try {
    const res = await request.get('v1/analytics/coach/alert-frequency', { params: { days: days.value } })
    const d = res.data
    isEmpty.value.alert = !d.types?.length
    if (isEmpty.value.alert) return
    await nextTick()
    const chart = initChart(alertChartRef.value)
    chart?.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: ['警告', '危险'] },
      grid: { left: '20%', right: '10%' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: d.types },
      series: [
        { name: '警告', type: 'bar', data: d.warning, itemStyle: { color: '#faad14' } },
        { name: '危险', type: 'bar', data: d.danger, itemStyle: { color: '#ff4d4f' } },
      ],
    })
  } catch { isEmpty.value.alert = true } finally { loading.value.alert = false }
}

async function fetchChallengeStats() {
  loading.value.challenge = true
  try {
    const res = await request.get('v1/analytics/coach/challenge-stats')
    const d = res.data
    isEmpty.value.challenge = !d.challenges?.length
    if (isEmpty.value.challenge) return
    await nextTick()
    const chart = initChart(challengeChartRef.value)
    chart?.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: ['报名', '完成'] },
      xAxis: { type: 'category', data: d.challenges, axisLabel: { rotate: 15, fontSize: 11 } },
      yAxis: { type: 'value' },
      series: [
        { name: '报名', type: 'bar', data: d.enrolled, itemStyle: { color: '#1890ff' } },
        { name: '完成', type: 'bar', data: d.completed, itemStyle: { color: '#52c41a' } },
      ],
    })
  } catch { isEmpty.value.challenge = true } finally { loading.value.challenge = false }
}

async function fetchStageDistribution() {
  loading.value.stage = true
  try {
    const res = await request.get('v1/analytics/coach/stage-distribution')
    const d = res.data
    isEmpty.value.stage = !d.stages?.length
    if (isEmpty.value.stage) return
    await nextTick()
    const chart = initChart(stageChartRef.value)
    const stageColors = ['#d9d9d9', '#bfbfbf', '#faad14', '#fa8c16', '#1890ff', '#52c41a', '#13c2c2']
    chart?.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: 10, top: 'center' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        label: { show: true, formatter: '{b}\n{c}人' },
        data: d.stages.map((s: string, i: number) => ({
          name: `${s} ${d.labels[i]}`,
          value: d.counts[i],
          itemStyle: { color: stageColors[i] || '#999' },
        })),
      }],
    })
  } catch { isEmpty.value.stage = true } finally { loading.value.stage = false }
}

function disposeCharts() {
  charts.forEach(c => c?.dispose())
  charts.length = 0
}

function fetchAll() {
  disposeCharts()
  // Reset empty states
  Object.keys(isEmpty.value).forEach(k => {
    (isEmpty.value as any)[k] = false
  })
  fetchRiskTrend()
  fetchMicroTrend()
  fetchDomainPerformance()
  fetchAlertFrequency()
  fetchChallengeStats()
  fetchStageDistribution()
}

onMounted(() => fetchAll())
onUnmounted(() => disposeCharts())
</script>

<style scoped>
.coach-analytics {
  padding: 0;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
}
.chart-box {
  width: 100%;
  height: 320px;
}
</style>
