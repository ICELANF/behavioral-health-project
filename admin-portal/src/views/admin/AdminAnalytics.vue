<template>
  <div class="admin-analytics">
    <a-page-header title="平台数据分析" @back="$router.back()" style="padding: 0 0 16px">
      <template #extra>
        <a-button type="primary" @click="fetchAll" :loading="refreshing">
          <template #icon><ReloadOutlined /></template>
          刷新数据
        </a-button>
      </template>
    </a-page-header>

    <!-- KPI 卡片行 -->
    <a-row :gutter="16" class="kpi-row">
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card :bordered="false">
          <a-statistic title="注册用户" :value="overview.total_users" :value-style="{ color: '#1890ff' }">
            <template #prefix><UserOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card :bordered="false">
          <a-statistic title="活跃用户" :value="overview.active_users" :value-style="{ color: '#52c41a' }">
            <template #prefix><CheckCircleOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card :bordered="false">
          <a-statistic title="认证教练" :value="overview.coach_count" :value-style="{ color: '#722ed1' }">
            <template #prefix><TeamOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card :bordered="false">
          <a-statistic title="高风险学员" :value="overview.high_risk_count" :value-style="{ color: '#ff4d4f' }">
            <template #prefix><WarningOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 第一行图表: 用户增长(16) + 角色分布(8) -->
    <a-row :gutter="[16, 16]" style="margin-top: 16px">
      <a-col :xs="24" :lg="16">
        <a-card title="用户增长趋势" :bordered="false">
          <a-spin :spinning="loading.growth">
            <div v-if="isEmpty.growth"><a-empty description="暂无增长数据" /></div>
            <div v-else ref="growthChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="8">
        <a-card title="角色分布" :bordered="false">
          <a-spin :spinning="loading.role">
            <div v-if="isEmpty.role"><a-empty description="暂无角色数据" /></div>
            <div v-else ref="roleChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
    </a-row>

    <!-- 第二行: 阶段分布(12) + 风险分布(12) -->
    <a-row :gutter="[16, 16]" style="margin-top: 16px">
      <a-col :xs="24" :md="12">
        <a-card title="行为阶段分布" :bordered="false">
          <a-spin :spinning="loading.stage">
            <div v-if="isEmpty.stage"><a-empty description="暂无阶段数据" /></div>
            <div v-else ref="stageChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="12">
        <a-card title="风险等级分布" :bordered="false">
          <a-spin :spinning="loading.risk">
            <div v-if="isEmpty.risk"><a-empty description="暂无风险数据" /></div>
            <div v-else ref="riskChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
    </a-row>

    <!-- 第三行: 教练排行(14) + 系统概况(10) -->
    <a-row :gutter="[16, 16]" style="margin-top: 16px">
      <a-col :xs="24" :lg="14">
        <a-card title="教练绩效排行" :bordered="false">
          <a-spin :spinning="loading.leaderboard">
            <div v-if="isEmpty.leaderboard"><a-empty description="暂无教练数据" /></div>
            <div v-else ref="leaderboardChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="10">
        <a-card title="系统概况" :bordered="false">
          <a-descriptions :column="1" bordered size="small">
            <a-descriptions-item label="Agent在线数">{{ systemInfo.agent_count }}</a-descriptions-item>
            <a-descriptions-item label="调度任务数">{{ systemInfo.scheduler_jobs }}</a-descriptions-item>
            <a-descriptions-item label="知识库文档">{{ systemInfo.knowledge_chunks }}</a-descriptions-item>
            <a-descriptions-item label="平台版本">{{ systemInfo.platform_version }}</a-descriptions-item>
            <a-descriptions-item label="AI模型">{{ systemInfo.ai_model }}</a-descriptions-item>
            <a-descriptions-item label="视觉模型">{{ systemInfo.vision_model }}</a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
    </a-row>

    <!-- 第四行: 挑战效果(全宽) -->
    <a-row :gutter="[16, 16]" style="margin-top: 16px">
      <a-col :span="24">
        <a-card title="挑战活动效果" :bordered="false">
          <a-spin :spinning="loading.challenge">
            <div v-if="isEmpty.challenge"><a-empty description="暂无挑战数据" /></div>
            <div v-else ref="challengeChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import request from '../../api/request'
import {
  ReloadOutlined, UserOutlined, CheckCircleOutlined,
  TeamOutlined, WarningOutlined,
} from '@ant-design/icons-vue'

const refreshing = ref(false)

const overview = ref({ total_users: 0, active_users: 0, coach_count: 0, high_risk_count: 0 })

const systemInfo = ref({
  agent_count: 0,
  scheduler_jobs: 0,
  knowledge_chunks: '-',
  platform_version: '-',
  ai_model: '-',
  vision_model: '-',
})

const growthChartRef = ref<HTMLElement>()
const roleChartRef = ref<HTMLElement>()
const stageChartRef = ref<HTMLElement>()
const riskChartRef = ref<HTMLElement>()
const leaderboardChartRef = ref<HTMLElement>()
const challengeChartRef = ref<HTMLElement>()

const charts: echarts.ECharts[] = []

const loading = ref({
  overview: false, growth: false, role: false,
  stage: false, risk: false, leaderboard: false, challenge: false,
})
const isEmpty = ref({
  growth: false, role: false, stage: false,
  risk: false, leaderboard: false, challenge: false,
})

function initChart(el: HTMLElement | undefined): echarts.ECharts | null {
  if (!el) return null
  const c = echarts.init(el)
  charts.push(c)
  return c
}

async function fetchOverview() {
  loading.value.overview = true
  try {
    const res = await request.get('v1/analytics/admin/overview')
    overview.value = res.data
  } catch { /* keep defaults */ } finally { loading.value.overview = false }
}

async function fetchUserGrowth() {
  loading.value.growth = true
  try {
    const res = await request.get('v1/analytics/admin/user-growth', { params: { months: 12 } })
    const d = res.data
    isEmpty.value.growth = !d.months?.length
    if (isEmpty.value.growth) return
    await nextTick()
    const chart = initChart(growthChartRef.value)
    chart?.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['新增用户', '累计用户'] },
      xAxis: { type: 'category', data: d.months },
      yAxis: [
        { type: 'value', name: '新增' },
        { type: 'value', name: '累计' },
      ],
      series: [
        { name: '新增用户', type: 'bar', data: d.new_users, itemStyle: { color: '#1890ff' } },
        { name: '累计用户', type: 'line', yAxisIndex: 1, data: d.cumulative, itemStyle: { color: '#52c41a' }, smooth: true },
      ],
    })
  } catch { isEmpty.value.growth = true } finally { loading.value.growth = false }
}

async function fetchRoleDistribution() {
  loading.value.role = true
  try {
    const res = await request.get('v1/analytics/admin/role-distribution')
    const d = res.data
    isEmpty.value.role = !d.roles?.length
    if (isEmpty.value.role) return
    await nextTick()
    const chart = initChart(roleChartRef.value)
    const roleColors: Record<string, string> = {
      observer: '#d9d9d9', grower: '#bfbfbf', sharer: '#91d5ff',
      coach: '#1890ff', promoter: '#722ed1', supervisor: '#722ed1',
      master: '#eb2f96', admin: '#fa541c',
    }
    chart?.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        type: 'pie',
        radius: ['35%', '65%'],
        label: { formatter: '{b}\n{d}%' },
        data: d.roles.map((r: string, i: number) => ({
          name: d.labels[i],
          value: d.counts[i],
          itemStyle: { color: roleColors[r] || '#999' },
        })),
      }],
    })
  } catch { isEmpty.value.role = true } finally { loading.value.role = false }
}

async function fetchStageDistribution() {
  loading.value.stage = true
  try {
    const res = await request.get('v1/analytics/admin/stage-distribution')
    const d = res.data
    isEmpty.value.stage = !d.stages?.length
    if (isEmpty.value.stage) return
    await nextTick()
    const chart = initChart(stageChartRef.value)
    const stageColors = ['#d9d9d9', '#bfbfbf', '#faad14', '#fa8c16', '#1890ff', '#52c41a', '#13c2c2']
    chart?.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: {
        type: 'category',
        data: d.stages.map((s: string, i: number) => `${s}\n${d.labels[i]}`),
      },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: d.counts.map((c: number, i: number) => ({
          value: c,
          itemStyle: { color: stageColors[i] || '#999' },
        })),
        barWidth: '50%',
      }],
    })
  } catch { isEmpty.value.stage = true } finally { loading.value.stage = false }
}

async function fetchRiskDistribution() {
  loading.value.risk = true
  try {
    const res = await request.get('v1/analytics/admin/risk-distribution')
    const d = res.data
    isEmpty.value.risk = !d.levels?.length
    if (isEmpty.value.risk) return
    await nextTick()
    const chart = initChart(riskChartRef.value)
    const riskColors: Record<string, string> = {
      R0: '#52c41a', R1: '#a0d911', R2: '#faad14', R3: '#fa8c16', R4: '#ff4d4f',
    }
    chart?.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: 10, top: 'center' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        label: { show: true, formatter: '{b}\n{c}人' },
        data: d.levels.map((l: string, i: number) => ({
          name: `${l} ${d.labels[i]}`,
          value: d.counts[i],
          itemStyle: { color: riskColors[l] || '#999' },
        })),
      }],
    })
  } catch { isEmpty.value.risk = true } finally { loading.value.risk = false }
}

async function fetchCoachLeaderboard() {
  loading.value.leaderboard = true
  try {
    const res = await request.get('v1/analytics/admin/coach-leaderboard', { params: { limit: 10 } })
    const d = res.data
    isEmpty.value.leaderboard = !d.leaderboard?.length
    if (isEmpty.value.leaderboard) return
    await nextTick()
    const chart = initChart(leaderboardChartRef.value)
    const items = [...d.leaderboard].reverse()
    chart?.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '20%', right: '10%' },
      xAxis: { type: 'value', max: 100, name: '完成率(%)' },
      yAxis: { type: 'category', data: items.map((c: any) => c.name) },
      series: [{
        type: 'bar',
        data: items.map((c: any) => ({
          value: c.completion_rate,
          itemStyle: {
            color: c.completion_rate >= 80 ? '#52c41a' : c.completion_rate >= 50 ? '#1890ff' : '#faad14',
          },
        })),
        label: { show: true, position: 'right', formatter: '{c}%' },
      }],
    })
  } catch { isEmpty.value.leaderboard = true } finally { loading.value.leaderboard = false }
}

async function fetchChallengeEffectiveness() {
  loading.value.challenge = true
  try {
    const res = await request.get('v1/analytics/admin/challenge-effectiveness')
    const d = res.data
    isEmpty.value.challenge = !d.challenges?.length
    if (isEmpty.value.challenge) return
    await nextTick()
    const chart = initChart(challengeChartRef.value)
    const titles = d.challenges.map((c: any) => c.title)
    chart?.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: ['报名', '进行中', '完成', '退出'] },
      xAxis: { type: 'category', data: titles, axisLabel: { rotate: 15, fontSize: 11 } },
      yAxis: { type: 'value' },
      series: [
        { name: '报名', type: 'bar', data: d.challenges.map((c: any) => c.enrolled), itemStyle: { color: '#1890ff' } },
        { name: '进行中', type: 'bar', data: d.challenges.map((c: any) => c.active), itemStyle: { color: '#722ed1' } },
        { name: '完成', type: 'bar', data: d.challenges.map((c: any) => c.completed), itemStyle: { color: '#52c41a' } },
        { name: '退出', type: 'bar', data: d.challenges.map((c: any) => c.dropped), itemStyle: { color: '#ff4d4f' } },
      ],
    })
  } catch { isEmpty.value.challenge = true } finally { loading.value.challenge = false }
}

async function fetchSystemInfo() {
  try {
    const res = await request.get('v1/analytics/admin/system-info')
    systemInfo.value = { ...systemInfo.value, ...res.data }
  } catch { /* keep defaults */ }
}

function disposeCharts() {
  charts.forEach(c => c?.dispose())
  charts.length = 0
}

async function fetchAll() {
  refreshing.value = true
  disposeCharts()
  Object.keys(isEmpty.value).forEach(k => { (isEmpty.value as any)[k] = false })
  await Promise.all([
    fetchOverview(),
    fetchUserGrowth(),
    fetchRoleDistribution(),
    fetchStageDistribution(),
    fetchRiskDistribution(),
    fetchCoachLeaderboard(),
    fetchChallengeEffectiveness(),
    fetchSystemInfo(),
  ])
  refreshing.value = false
}

onMounted(() => fetchAll())
onUnmounted(() => disposeCharts())
</script>

<style scoped>
.admin-analytics {
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
.kpi-row :deep(.ant-card-body) {
  padding: 20px 24px;
}
.chart-box {
  width: 100%;
  height: 320px;
}
</style>
