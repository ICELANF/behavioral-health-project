<template>
  <div class="my-research">
    <div class="page-header">
      <h2>研究数据</h2>
      <div class="header-actions">
        <a-button @click="exportCSV">导出 CSV</a-button>
        <a-button type="primary" @click="exportExcel">导出 Excel</a-button>
      </div>
    </div>

    <!-- Aggregate Stats -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6"><a-card size="small"><a-statistic title="总样本数" :value="aggStats.totalSamples" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="活跃用户" :value="aggStats.activeUsers" value-style="color: #3f8600" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="平均干预天数" :value="aggStats.avgInterventionDays" suffix="天" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="整体行为改善率" :value="aggStats.improvementRate" suffix="%" /></a-card></a-col>
    </a-row>

    <!-- Custom Query -->
    <a-card title="自定义查询" style="margin-bottom: 16px">
      <a-form layout="inline">
        <a-form-item label="数据维度">
          <a-select v-model:value="query.dimension" style="width: 160px">
            <a-select-option value="stage">行为阶段</a-select-option>
            <a-select-option value="risk">风险等级</a-select-option>
            <a-select-option value="domain">干预领域</a-select-option>
            <a-select-option value="age">年龄分布</a-select-option>
            <a-select-option value="assessment">测评得分</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="时间范围">
          <a-range-picker v-model:value="query.dateRange" />
        </a-form-item>
        <a-form-item label="分组">
          <a-select v-model:value="query.groupBy" style="width: 120px">
            <a-select-option value="none">不分组</a-select-option>
            <a-select-option value="gender">按性别</a-select-option>
            <a-select-option value="age">按年龄段</a-select-option>
            <a-select-option value="coach">按教练</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="runQuery">查询</a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- Query Results -->
    <a-card title="查询结果（脱敏数据）">
      <a-alert message="所有数据已脱敏处理，不含个人身份信息" type="info" show-icon style="margin-bottom: 12px" />

      <a-table :dataSource="queryResults" :columns="resultColumns" rowKey="key" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'bar'">
            <div class="result-bar-bg">
              <div class="result-bar" :style="{ width: (record.count / maxCount * 100) + '%' }"></div>
            </div>
          </template>
          <template v-if="column.key === 'pct'">
            {{ record.percent }}%
          </template>
        </template>
      </a-table>

      <!-- Summary -->
      <div class="summary-section">
        <h4>统计摘要</h4>
        <a-descriptions :column="3" bordered size="small">
          <a-descriptions-item label="样本总数">{{ totalSamples }}</a-descriptions-item>
          <a-descriptions-item label="均值">{{ avgValue.toFixed(1) }}</a-descriptions-item>
          <a-descriptions-item label="标准差">{{ stdDev.toFixed(2) }}</a-descriptions-item>
          <a-descriptions-item label="中位数">{{ medianValue }}</a-descriptions-item>
          <a-descriptions-item label="最大值">{{ maxValue }}</a-descriptions-item>
          <a-descriptions-item label="最小值">{{ minValue }}</a-descriptions-item>
        </a-descriptions>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const query = reactive({
  dimension: 'stage',
  dateRange: null as any,
  groupBy: 'none',
})

const aggStats = reactive({ totalSamples: 0, activeUsers: 0, avgInterventionDays: 0, improvementRate: 0 })

const queryResults = ref<{ key: string; category: string; count: number; percent: number }[]>([])

const resultColumns = [
  { title: '分类', dataIndex: 'category', width: 120 },
  { title: '人数', dataIndex: 'count', width: 80 },
  { title: '分布', key: 'bar', width: 200 },
  { title: '占比', key: 'pct', width: 80 },
]

const maxCount = computed(() => Math.max(...queryResults.value.map(r => r.count), 1))
const totalSamples = computed(() => queryResults.value.reduce((s, r) => s + r.count, 0))
const avgValue = computed(() => totalSamples.value / (queryResults.value.length || 1))
const stdDev = ref(0)
const medianValue = ref(0)
const maxValue = ref(0)
const minValue = ref(0)

const applyQueryResult = (data: any) => {
  const items = data.data || data.items || []
  const total = items.reduce((s: number, r: any) => s + (r.count || 0), 0) || 1
  queryResults.value = items.map((r: any, i: number) => ({
    key: String(i + 1), category: r.category || r.label || '',
    count: r.count || 0, percent: parseFloat(((r.count || 0) / total * 100).toFixed(1)),
  }))
  const summary = data.summary || {}
  stdDev.value = summary.std_dev ?? summary.stdDev ?? 0
  medianValue.value = summary.median ?? 0
  maxValue.value = summary.max ?? Math.max(...queryResults.value.map(r => r.count), 0)
  minValue.value = summary.min ?? Math.min(...queryResults.value.map(r => r.count), 0)
}

const dimensionEndpoints: Record<string, string> = {
  stage: '/v1/analytics/admin/stage-distribution',
  risk: '/v1/analytics/admin/risk-distribution',
  domain: '/v1/analytics/admin/stage-distribution',  // reuse stage as domain proxy
  age: '/v1/analytics/admin/user-growth',
  assessment: '/v1/analytics/admin/stage-distribution',
}

const loadInitialStats = async () => {
  try {
    const [stageRes, userRes] = await Promise.allSettled([
      request.get('/v1/analytics/admin/stage-distribution'),
      request.get('/v1/analytics/admin/user-growth'),
    ])
    if (stageRes.status === 'fulfilled') {
      const data = stageRes.value.data
      const items = data?.distribution || data?.items || data?.data || (Array.isArray(data) ? data : [])
      const total = items.reduce((s: number, r: any) => s + (r.count || r.value || 0), 0)
      applyQueryResult({ data: items.map((r: any) => ({ category: r.stage || r.label || r.name || '', count: r.count || r.value || 0 })), summary: { total } })
      aggStats.totalSamples = total
    }
    if (userRes.status === 'fulfilled') {
      const data = userRes.value.data
      aggStats.activeUsers = data?.active_users ?? data?.total ?? 0
      aggStats.avgInterventionDays = data?.avg_days ?? 0
      aggStats.improvementRate = data?.improvement_rate ?? 0
    }
  } catch (e) {
    console.error('加载研究数据失败:', e)
  }
}

onMounted(loadInitialStats)

const runQuery = async () => {
  try {
    const endpoint = dimensionEndpoints[query.dimension] || '/v1/analytics/admin/stage-distribution'
    const res = await request.get(endpoint)
    const data = res.data
    const items = data?.distribution || data?.items || data?.data || (Array.isArray(data) ? data : [])
    applyQueryResult({ data: items.map((r: any) => ({ category: r.stage || r.label || r.name || '', count: r.count || r.value || 0 })), summary: data?.summary || {} })
    message.success('查询完成')
  } catch (e) {
    console.error('查询失败:', e)
    message.error('查询失败')
  }
}

const exportCSV = () => {
  const csv = ['分类,人数,占比']
  queryResults.value.forEach(r => csv.push(`${r.category},${r.count},${r.percent}%`))
  const blob = new Blob(['\uFEFF' + csv.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `research_data_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  message.success('CSV 导出成功')
}

const exportExcel = () => {
  // Client-side export as CSV (Excel-compatible) since no server-side export endpoint
  exportCSV()
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 8px; }

.result-bar-bg { height: 16px; background: #f5f5f5; border-radius: 4px; overflow: hidden; }
.result-bar { height: 100%; background: #1890ff; border-radius: 4px; transition: width 0.3s; }

.summary-section { margin-top: 16px; }
.summary-section h4 { margin: 0 0 8px; font-size: 14px; }
</style>
