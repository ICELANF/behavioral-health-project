<template>
  <div class="safety-dashboard">
    <h2>安全管理仪表盘</h2>

    <!-- 统计卡片 -->
    <a-row :gutter="16" style="margin-bottom: 24px">
      <a-col :span="6">
        <a-card>
          <a-statistic title="今日安全事件" :value="stats.today" :value-style="{ color: stats.today > 0 ? '#cf1322' : '#3f8600' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="待审核" :value="stats.pending_review" :value-style="{ color: stats.pending_review > 0 ? '#faad14' : '#3f8600' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="今日危机事件" :value="stats.crisis_today" :value-style="{ color: stats.crisis_today > 0 ? '#cf1322' : '#3f8600' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="本月总计" :value="stats.this_month" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 图表区域 -->
    <a-row :gutter="16" style="margin-bottom: 24px">
      <a-col :span="14">
        <a-card title="7日安全事件趋势">
          <div ref="trendChartRef" style="height: 300px"></div>
        </a-card>
      </a-col>
      <a-col :span="10">
        <a-card title="事件类型分布">
          <div ref="pieChartRef" style="height: 300px"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 最近高危事件 -->
    <a-card title="最近高危事件">
      <a-table
        :dataSource="recentLogs"
        :columns="columns"
        :pagination="false"
        :loading="loading"
        size="small"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'severity'">
            <a-tag :color="severityColor(record.severity)">{{ record.severity }}</a-tag>
          </template>
          <template v-if="column.key === 'event_type'">
            <a-tag>{{ eventTypeLabel(record.event_type) }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-button size="small" type="link" @click="$router.push(`/safety/review`)">查看</a-button>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import request from '@/api/request'

const stats = ref({
  today: 0,
  this_week: 0,
  this_month: 0,
  pending_review: 0,
  crisis_today: 0,
  type_distribution: {} as Record<string, number>,
  trend_7d: [] as { date: string; count: number }[],
})

const recentLogs = ref<any[]>([])
const loading = ref(false)

const trendChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '用户ID', dataIndex: 'user_id', key: 'user_id', width: 80 },
  { title: '类型', key: 'event_type', width: 120 },
  { title: '严重级', key: 'severity', width: 80 },
  { title: '输入摘要', dataIndex: 'input_text', key: 'input_text', ellipsis: true },
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
  { title: '操作', key: 'action', width: 80 },
]

const severityColor = (s: string) => {
  const map: Record<string, string> = { critical: 'red', high: 'orange', medium: 'gold', low: 'green' }
  return map[s] || 'default'
}

const eventTypeLabel = (t: string) => {
  const map: Record<string, string> = {
    input_blocked: '输入拦截',
    output_filtered: '输出过滤',
    crisis_detected: '危机检测',
    daily_report: '日报',
  }
  return map[t] || t
}

const fetchData = async () => {
  loading.value = true
  try {
    const [dashRes, logsRes] = await Promise.all([
      request.get('v1/safety/dashboard'),
      request.get('v1/safety/logs', { params: { page: 1, page_size: 10, severity: 'critical' } }),
    ])
    stats.value = dashRes.data
    recentLogs.value = logsRes.data.items || []

    await nextTick()
    renderCharts()
  } catch (e) {
    console.error('Failed to load safety dashboard', e)
  } finally {
    loading.value = false
  }
}

const renderCharts = () => {
  try {
    // Dynamic import echarts to avoid SSR issues
    import('echarts').then((echarts) => {
      // 趋势图
      if (trendChartRef.value) {
        const trendChart = echarts.init(trendChartRef.value)
        const trend = stats.value.trend_7d || []
        trendChart.setOption({
          tooltip: { trigger: 'axis' },
          xAxis: { type: 'category', data: trend.map((t: any) => t.date) },
          yAxis: { type: 'value', minInterval: 1 },
          series: [{
            data: trend.map((t: any) => t.count),
            type: 'line',
            smooth: true,
            areaStyle: { opacity: 0.3 },
            itemStyle: { color: '#ff4d4f' },
          }],
        })
      }

      // 饼图
      if (pieChartRef.value) {
        const pieChart = echarts.init(pieChartRef.value)
        const dist = stats.value.type_distribution || {}
        const labelMap: Record<string, string> = {
          input_blocked: '输入拦截',
          output_filtered: '输出过滤',
          crisis_detected: '危机检测',
          daily_report: '日报',
        }
        pieChart.setOption({
          tooltip: { trigger: 'item' },
          series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            data: Object.entries(dist).map(([k, v]) => ({
              name: labelMap[k] || k,
              value: v,
            })),
          }],
        })
      }
    }).catch(() => {
      console.warn('echarts not available')
    })
  } catch {
    // echarts optional
  }
}

onMounted(fetchData)
</script>

<style scoped>
.safety-dashboard h2 {
  margin-bottom: 24px;
}
</style>
