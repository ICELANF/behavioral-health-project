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
      <a-col :span="6"><a-card size="small"><a-statistic title="总样本数" :value="1248" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="活跃用户" :value="856" value-style="color: #3f8600" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="平均干预天数" :value="45" suffix="天" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="整体行为改善率" :value="62" suffix="%" /></a-card></a-col>
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
import { ref, reactive, computed } from 'vue'
import { message } from 'ant-design-vue'

const query = reactive({
  dimension: 'stage',
  dateRange: null,
  groupBy: 'none',
})

const queryResults = ref([
  { key: '1', category: '前思考期', count: 186, percent: 14.9 },
  { key: '2', category: '思考期', count: 312, percent: 25.0 },
  { key: '3', category: '准备期', count: 268, percent: 21.5 },
  { key: '4', category: '行动期', count: 298, percent: 23.9 },
  { key: '5', category: '维持期', count: 152, percent: 12.2 },
  { key: '6', category: '终止期', count: 32, percent: 2.5 },
])

const resultColumns = [
  { title: '分类', dataIndex: 'category', width: 120 },
  { title: '人数', dataIndex: 'count', width: 80 },
  { title: '分布', key: 'bar', width: 200 },
  { title: '占比', key: 'pct', width: 80 },
]

const maxCount = computed(() => Math.max(...queryResults.value.map(r => r.count), 1))
const totalSamples = computed(() => queryResults.value.reduce((s, r) => s + r.count, 0))
const avgValue = computed(() => totalSamples.value / (queryResults.value.length || 1))
const stdDev = ref(89.45)
const medianValue = ref(275)
const maxValue = ref(312)
const minValue = ref(32)

const runQuery = () => {
  message.success('查询完成')
  // In production, would call API with query params
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
  message.info('Excel 导出功能需要后端支持')
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
