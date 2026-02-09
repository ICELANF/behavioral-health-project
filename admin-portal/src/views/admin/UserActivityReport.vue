<!--
  用户活跃度报告 — KPI 卡片 + ECharts 图表
  路由: /admin/user-activity-report
-->
<template>
  <div class="user-activity-report">
    <a-page-header title="用户活跃度报告" @back="$router.back()">
      <template #extra>
        <a-range-picker
          v-model:value="dateRange"
          :presets="datePresets"
          format="YYYY-MM-DD"
          @change="fetchReport"
        />
        <a-button type="primary" @click="fetchReport" :loading="refreshing">
          <template #icon><ReloadOutlined /></template>
          刷新数据
        </a-button>
      </template>
    </a-page-header>

    <!-- KPI 卡片 -->
    <a-row :gutter="16" class="kpi-row">
      <a-col :span="6">
        <a-card :bordered="false" :loading="loading">
          <a-statistic
            title="活跃用户数"
            :value="kpi.active_users"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix><UserOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false" :loading="loading">
          <a-statistic
            title="总活动次数"
            :value="kpi.total_activities"
            :value-style="{ color: '#52c41a' }"
          >
            <template #prefix><ThunderboltOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false" :loading="loading">
          <a-statistic
            title="日均活动"
            :value="kpi.daily_avg"
            :precision="1"
            :value-style="{ color: '#722ed1' }"
          >
            <template #prefix><RiseOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false" :loading="loading">
          <a-statistic
            title="活跃率"
            :value="kpi.active_rate"
            :precision="1"
            suffix="%"
            :value-style="{ color: '#fa8c16' }"
          >
            <template #prefix><FieldTimeOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 图表行 -->
    <a-row :gutter="[16, 16]" style="margin-top: 16px">
      <!-- 活动类型分布（饼图） -->
      <a-col :span="10">
        <a-card title="活动类型分布" :bordered="false">
          <a-spin :spinning="loading">
            <div v-if="isEmpty.distribution">
              <a-empty description="暂无活动数据" />
            </div>
            <div v-else ref="pieChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>

      <!-- 每日活动趋势（折线图） -->
      <a-col :span="14">
        <a-card title="每日活动趋势" :bordered="false">
          <a-spin :spinning="loading">
            <div v-if="isEmpty.trend">
              <a-empty description="暂无趋势数据" />
            </div>
            <div v-else ref="lineChartRef" class="chart-box"></div>
          </a-spin>
        </a-card>
      </a-col>
    </a-row>

    <!-- 活动明细表 -->
    <a-card title="活动类型明细" :bordered="false" style="margin-top: 16px">
      <a-table
        :dataSource="activityDetails"
        :columns="detailColumns"
        :loading="loading"
        :pagination="false"
        rowKey="type"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="activityColor(record.type)">{{ activityLabel(record.type) }}</a-tag>
          </template>
          <template v-if="column.key === 'percentage'">
            <a-progress
              :percent="record.percentage"
              :stroke-color="activityColor(record.type)"
              size="small"
              style="width: 120px"
            />
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { Dayjs } from 'dayjs'
import dayjs from 'dayjs'
import request from '@/api/request'
import {
  ReloadOutlined,
  UserOutlined,
  ThunderboltOutlined,
  RiseOutlined,
  FieldTimeOutlined,
} from '@ant-design/icons-vue'

// ============ 状态 ============

const loading = ref(false)
const refreshing = ref(false)

const dateRange = ref<[Dayjs, Dayjs]>([
  dayjs().subtract(30, 'day'),
  dayjs(),
])

const datePresets = [
  { label: '近7天', value: [dayjs().subtract(7, 'day'), dayjs()] as [Dayjs, Dayjs] },
  { label: '近30天', value: [dayjs().subtract(30, 'day'), dayjs()] as [Dayjs, Dayjs] },
  { label: '近90天', value: [dayjs().subtract(90, 'day'), dayjs()] as [Dayjs, Dayjs] },
]

const kpi = reactive({
  active_users: 0,
  total_activities: 0,
  daily_avg: 0,
  active_rate: 0,
})

const isEmpty = reactive({
  distribution: false,
  trend: false,
})

// ============ 图表 ============

const pieChartRef = ref<HTMLElement>()
const lineChartRef = ref<HTMLElement>()
const charts: echarts.ECharts[] = []

function initChart(el: HTMLElement | undefined): echarts.ECharts | null {
  if (!el) return null
  const c = echarts.init(el)
  charts.push(c)
  return c
}

function disposeCharts() {
  charts.forEach(c => c?.dispose())
  charts.length = 0
}

// ============ 活动明细 ============

interface ActivityDetail {
  type: string
  count: number
  percentage: number
}

const activityDetails = ref<ActivityDetail[]>([])

const detailColumns = [
  { title: '活动类型', key: 'type', width: 140 },
  { title: '次数', dataIndex: 'count', key: 'count', width: 100, sorter: (a: ActivityDetail, b: ActivityDetail) => a.count - b.count },
  { title: '占比', key: 'percentage', width: 180 },
]

// ============ 数据加载 ============

const fetchReport = async () => {
  loading.value = true
  refreshing.value = true
  disposeCharts()
  isEmpty.distribution = false
  isEmpty.trend = false

  try {
    const params: Record<string, string> = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0].format('YYYY-MM-DD')
      params.end_date = dateRange.value[1].format('YYYY-MM-DD')
    }

    const { data } = await request.get('v1/stats/admin/activity-report', { params })

    // KPI
    kpi.active_users = data.active_users ?? 0
    kpi.total_activities = data.total_activities ?? 0
    kpi.daily_avg = data.daily_avg ?? 0
    kpi.active_rate = data.active_rate ?? 0

    // 饼图数据
    const distData: { type: string; count: number }[] = data.distribution ?? []
    isEmpty.distribution = distData.length === 0

    if (!isEmpty.distribution) {
      const total = distData.reduce((sum, d) => sum + d.count, 0)
      activityDetails.value = distData.map(d => ({
        type: d.type,
        count: d.count,
        percentage: total > 0 ? Math.round((d.count / total) * 1000) / 10 : 0,
      }))

      await nextTick()
      const pieChart = initChart(pieChartRef.value)
      pieChart?.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { orient: 'vertical', right: 10, top: 'center' },
        series: [{
          type: 'pie',
          radius: ['35%', '65%'],
          center: ['40%', '50%'],
          label: { formatter: '{b}\n{d}%' },
          data: distData.map(d => ({
            name: activityLabel(d.type),
            value: d.count,
            itemStyle: { color: activityColor(d.type) },
          })),
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' },
          },
        }],
      })
    }

    // 折线图数据
    const trendData: { date: string; count: number; active_users: number }[] = data.trend ?? []
    isEmpty.trend = trendData.length === 0

    if (!isEmpty.trend) {
      await nextTick()
      const lineChart = initChart(lineChartRef.value)
      lineChart?.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['活动次数', '活跃用户'] },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: trendData.map(d => d.date),
          axisLabel: { rotate: 30, fontSize: 11 },
        },
        yAxis: [
          { type: 'value', name: '活动次数' },
          { type: 'value', name: '活跃用户' },
        ],
        series: [
          {
            name: '活动次数',
            type: 'line',
            data: trendData.map(d => d.count),
            smooth: true,
            areaStyle: { opacity: 0.15 },
            itemStyle: { color: '#1890ff' },
          },
          {
            name: '活跃用户',
            type: 'line',
            yAxisIndex: 1,
            data: trendData.map(d => d.active_users),
            smooth: true,
            areaStyle: { opacity: 0.1 },
            itemStyle: { color: '#52c41a' },
          },
        ],
      })
    }
  } catch (e: any) {
    console.error('加载活跃度报告失败:', e)
    isEmpty.distribution = true
    isEmpty.trend = true
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// ============ 工具函数 ============

const activityColorMap: Record<string, string> = {
  login: '#1890ff',
  assessment: '#722ed1',
  micro_action: '#52c41a',
  chat: '#13c2c2',
  challenge: '#fa8c16',
  device_sync: '#eb2f96',
  food_recognition: '#faad14',
  learning: '#2f54eb',
  content_view: '#a0d911',
}

const activityLabelMap: Record<string, string> = {
  login: '登录',
  assessment: '评估',
  micro_action: '微行动',
  chat: '对话',
  challenge: '挑战',
  device_sync: '设备同步',
  food_recognition: '食物识别',
  learning: '学习',
  content_view: '内容浏览',
}

const activityColor = (t: string): string => activityColorMap[t] || '#999'
const activityLabel = (t: string): string => activityLabelMap[t] || t

const formatDate = (d: string): string => {
  if (!d) return '--'
  return new Date(d).toLocaleString('zh-CN')
}

// ============ 生命周期 ============

onMounted(() => {
  fetchReport()
})

onUnmounted(() => {
  disposeCharts()
})
</script>

<style scoped>
.user-activity-report {
  padding: 0;
}

:deep(.ant-page-header) {
  padding: 0 0 16px 0;
}

.kpi-row :deep(.ant-card-body) {
  padding: 20px 24px;
}

.chart-box {
  width: 100%;
  height: 360px;
}
</style>
