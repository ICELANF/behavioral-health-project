<template>
  <div class="my-performance">
    <div class="page-header">
      <h2>我的绩效</h2>
      <a-range-picker v-model:value="dateRange" style="width: 240px" />
    </div>

    <a-alert v-if="error" :message="error" type="error" show-icon style="margin-bottom: 16px" />

    <!-- Key metrics -->
    <a-row :gutter="16" style="margin-bottom: 20px">
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card>
          <a-statistic title="管理学员数" :value="performance.total_students" :loading="loading">
            <template #prefix><span style="font-size: 14px">👥</span></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card>
          <a-statistic title="平均完成率" :value="performance.avg_adherence_rate" suffix="%" :loading="loading" :value-style="{ color: performance.avg_adherence_rate >= 70 ? '#3f8600' : '#cf1322' }">
            <template #prefix><span style="font-size: 14px">📈</span></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card>
          <a-statistic title="高风险学员" :value="performance.risk_distribution?.high || 0" :loading="loading" value-style="color: #cf1322">
            <template #prefix><span style="font-size: 14px">⚠️</span></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card>
          <a-statistic title="低风险学员" :value="performance.risk_distribution?.low || 0" :loading="loading" value-style="color: #389e0d">
            <template #prefix><span style="font-size: 14px">✅</span></template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- Monthly comparison chart -->
    <a-card title="月度绩效对比" style="margin-bottom: 16px">
      <div class="bar-chart">
        <div class="chart-row" v-for="(month, i) in monthlyData" :key="i">
          <span class="chart-month">{{ month.label }}</span>
          <div class="chart-bars-row">
            <div class="bar-group">
              <div class="bar success" :style="{ width: month.success + '%' }">
                <span class="bar-val">{{ month.success }}%</span>
              </div>
            </div>
            <div class="bar-group">
              <div class="bar retention" :style="{ width: month.retention + '%' }">
                <span class="bar-val">{{ month.retention }}%</span>
              </div>
            </div>
          </div>
        </div>
        <div class="chart-legend">
          <span class="legend-item"><span class="legend-dot success"></span>干预成功率</span>
          <span class="legend-item"><span class="legend-dot retention"></span>学员留存率</span>
        </div>
      </div>
    </a-card>

    <!-- Detailed breakdown -->
    <a-row :gutter="16">
      <a-col :xs="24" :md="12">
        <a-card title="干预工具使用统计">
          <div v-for="tool in toolStats" :key="tool.name" class="tool-stat-item">
            <span class="tool-name">{{ tool.name }}</span>
            <a-progress :percent="tool.percent" :stroke-color="tool.color" size="small" />
            <span class="tool-count">{{ tool.count }}次</span>
          </div>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="12">
        <a-card title="学员风险分布">
          <div class="risk-summary">
            <div class="risk-item">
              <span class="risk-label">低风险</span>
              <a-progress
                :percent="riskPercent('low')"
                stroke-color="#52c41a"
                size="small"
              />
              <span class="risk-count">{{ performance.risk_distribution?.low || 0 }}人</span>
            </div>
            <div class="risk-item">
              <span class="risk-label">中风险</span>
              <a-progress
                :percent="riskPercent('medium')"
                stroke-color="#faad14"
                size="small"
              />
              <span class="risk-count">{{ performance.risk_distribution?.medium || 0 }}人</span>
            </div>
            <div class="risk-item">
              <span class="risk-label">高风险</span>
              <a-progress
                :percent="riskPercent('high')"
                stroke-color="#ff4d4f"
                size="small"
              />
              <span class="risk-count">{{ performance.risk_distribution?.high || 0 }}人</span>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'

const dateRange = ref(null)
const loading = ref(false)

const performance = ref<any>({
  total_students: 0,
  avg_adherence_rate: 0,
  risk_distribution: { low: 0, medium: 0, high: 0 },
})

const monthlyData = ref<{ label: string; success: number; retention: number }[]>([])

const toolStats = ref<{ name: string; count: number; percent: number; color: string }[]>([])

const riskPercent = (level: string) => {
  const dist = performance.value.risk_distribution || {}
  const total = (dist.low || 0) + (dist.medium || 0) + (dist.high || 0)
  if (total === 0) return 0
  return Math.round(((dist[level] || 0) / total) * 100)
}

const error = ref('')

const loadPerformance = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await request.get('/v1/coach/performance')
    performance.value = data
  } catch (e: any) {
    console.error('加载绩效数据失败:', e)
    error.value = '加载绩效数据失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPerformance()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }

.bar-chart { padding: 8px 0; }
.chart-row { display: flex; align-items: center; margin-bottom: 8px; }
.chart-month { min-width: 40px; font-size: 13px; color: #666; }
.chart-bars-row { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.bar-group { height: 18px; background: #f5f5f5; border-radius: 4px; overflow: hidden; }
.bar { height: 100%; border-radius: 4px; display: flex; align-items: center; padding-left: 8px; min-width: 30px; transition: width 0.3s; }
.bar.success { background: #52c41a; }
.bar.retention { background: #1890ff; }
.bar-val { font-size: 11px; color: #fff; font-weight: 500; }
.chart-legend { display: flex; gap: 16px; margin-top: 12px; justify-content: center; }
.legend-item { font-size: 12px; color: #666; display: flex; align-items: center; gap: 4px; }
.legend-dot { width: 10px; height: 10px; border-radius: 2px; }
.legend-dot.success { background: #52c41a; }
.legend-dot.retention { background: #1890ff; }

.tool-stat-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.tool-name { min-width: 80px; font-size: 13px; color: #333; }
.tool-count { min-width: 40px; text-align: right; font-size: 12px; color: #999; }

.risk-summary { display: flex; flex-direction: column; gap: 12px; }
.risk-item { display: flex; align-items: center; gap: 8px; }
.risk-label { min-width: 50px; font-size: 13px; color: #333; }
.risk-count { min-width: 40px; text-align: right; font-size: 12px; color: #999; }
</style>
