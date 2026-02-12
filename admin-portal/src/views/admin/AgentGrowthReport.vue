<template>
  <div class="agent-growth-report">
    <a-page-header title="Agent 成长报告" sub-title="反馈质量指标、采纳率趋势、Prompt 版本追踪" />

    <!-- 概览统计 -->
    <a-spin :spinning="summaryLoading">
      <a-card title="Agent 概览" :bordered="false" style="margin-bottom: 16px">
        <a-table
          :dataSource="summaryList"
          :columns="summaryColumns"
          :pagination="false"
          rowKey="agent_id"
          size="middle"
          @row-click="(record: any) => selectAgent(record.agent_id)"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'acceptance_rate'">
              <a-progress :percent="Math.round(record.acceptance_rate * 100)" :size="'small'" :strokeColor="record.acceptance_rate >= 0.7 ? '#52c41a' : record.acceptance_rate >= 0.4 ? '#faad14' : '#ff4d4f'" />
            </template>
            <template v-if="column.key === 'avg_rating'">
              <a-rate :value="record.avg_rating" disabled allow-half :style="{ fontSize: '14px' }" />
              <span style="margin-left: 4px; color: #666; font-size: 12px">{{ record.avg_rating }}</span>
            </template>
            <template v-if="column.key === 'action'">
              <a-button type="link" size="small" @click="selectAgent(record.agent_id)">详情</a-button>
            </template>
          </template>
        </a-table>
      </a-card>
    </a-spin>

    <!-- 单 Agent 详情 -->
    <a-card v-if="selectedAgent" :title="`${selectedAgent} 成长详情`" :bordered="false" style="margin-bottom: 16px">
      <template #extra>
        <a-select v-model:value="reportDays" style="width: 120px" @change="loadGrowthReport">
          <a-select-option :value="7">最近7天</a-select-option>
          <a-select-option :value="30">最近30天</a-select-option>
          <a-select-option :value="90">最近90天</a-select-option>
        </a-select>
      </template>

      <a-spin :spinning="reportLoading">
        <!-- 汇总 -->
        <a-row :gutter="16" style="margin-bottom: 16px">
          <a-col :span="6">
            <a-statistic title="总反馈数" :value="report.summary?.total_feedback || 0" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="采纳率" :value="formatPct(report.summary?.acceptance_rate)" suffix="%" :value-style="{ color: (report.summary?.acceptance_rate || 0) >= 0.7 ? '#52c41a' : '#faad14' }" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="平均评分" :value="report.summary?.avg_rating || 0" :precision="1" suffix="/5" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="7日采纳趋势" :value="formatPct(report.summary?.trend_acceptance_7d)" suffix="%" :value-style="{ color: (report.summary?.trend_acceptance_7d || 0) >= 0 ? '#52c41a' : '#ff4d4f' }" :prefix="(report.summary?.trend_acceptance_7d || 0) >= 0 ? '↑' : '↓'" />
          </a-col>
        </a-row>

        <!-- 日指标表格 -->
        <a-table
          :dataSource="report.daily_metrics || []"
          :columns="dailyColumns"
          :pagination="false"
          rowKey="date"
          size="small"
          style="margin-bottom: 16px"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'acceptance_rate'">
              {{ formatPct(record.acceptance_rate) }}%
            </template>
          </template>
        </a-table>

        <!-- Prompt 版本 -->
        <a-divider>Prompt 版本历史</a-divider>
        <a-timeline>
          <a-timeline-item v-for="pv in report.prompt_versions || []" :key="pv.version" :color="pv.is_active ? 'green' : 'gray'">
            <strong>v{{ pv.version }}</strong>
            <a-tag v-if="pv.is_active" color="green" style="margin-left: 8px">激活</a-tag>
            <span style="color: #999; margin-left: 8px">{{ pv.created_at }}</span>
            <div v-if="pv.change_reason" style="color: #666; font-size: 12px; margin-top: 4px">{{ pv.change_reason }}</div>
            <div v-if="pv.prev_avg_rating != null" style="font-size: 12px; color: #999">
              变更前: 评分 {{ pv.prev_avg_rating }}, 采纳率 {{ formatPct(pv.prev_acceptance_rate) }}%
            </div>
          </a-timeline-item>
        </a-timeline>
      </a-spin>
    </a-card>

    <!-- 最近反馈 -->
    <a-card title="最近反馈" :bordered="false">
      <a-table
        :dataSource="feedbackList"
        :columns="feedbackColumns"
        :loading="feedbackLoading"
        :pagination="feedbackPagination"
        @change="handleFeedbackTableChange"
        rowKey="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'feedback_type'">
            <a-tag :color="feedbackColor(record.feedback_type)">{{ feedbackLabel(record.feedback_type) }}</a-tag>
          </template>
          <template v-if="column.key === 'rating'">
            <a-rate v-if="record.rating" :value="record.rating" disabled :style="{ fontSize: '12px' }" />
            <span v-else style="color: #999">-</span>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import request from '../../api/request'

const summaryLoading = ref(false)
const reportLoading = ref(false)
const feedbackLoading = ref(false)

const summaryList = ref<any[]>([])
const selectedAgent = ref<string | null>(null)
const reportDays = ref(30)
const report = ref<any>({})
const feedbackList = ref<any[]>([])
const feedbackPagination = reactive({ current: 1, pageSize: 20, total: 0 })

const summaryColumns = [
  { title: 'Agent', dataIndex: 'display_name', width: 140 },
  { title: 'agent_id', dataIndex: 'agent_id', width: 120 },
  { title: '反馈数', dataIndex: 'total_feedback', width: 80 },
  { title: '采纳率', key: 'acceptance_rate', width: 180 },
  { title: '平均评分', key: 'avg_rating', width: 180 },
  { title: '平均耗时(ms)', dataIndex: 'avg_processing_ms', width: 110 },
  { title: '操作', key: 'action', width: 80 },
]

const dailyColumns = [
  { title: '日期', dataIndex: 'date', width: 100 },
  { title: '反馈数', dataIndex: 'feedback_count', width: 70 },
  { title: '采纳', dataIndex: 'accept_count', width: 60 },
  { title: '拒绝', dataIndex: 'reject_count', width: 60 },
  { title: '采纳率', key: 'acceptance_rate', width: 80 },
  { title: '评分', dataIndex: 'avg_rating', width: 60 },
  { title: '耗时(ms)', dataIndex: 'avg_processing_ms', width: 90 },
]

const feedbackColumns = [
  { title: 'ID', dataIndex: 'id', width: 50 },
  { title: 'Agent', dataIndex: 'agent_id', width: 100 },
  { title: '类型', key: 'feedback_type', width: 80 },
  { title: '评分', key: 'rating', width: 120 },
  { title: '评论', dataIndex: 'comment', ellipsis: true, width: 200 },
  { title: '用户消息', dataIndex: 'user_message', ellipsis: true, width: 160 },
  { title: '时间', dataIndex: 'created_at', width: 150 },
]

function formatPct(val: number | null | undefined): string {
  if (val == null) return '0'
  return (val * 100).toFixed(1)
}

function feedbackColor(t: string) {
  return { accept: 'green', reject: 'red', modify: 'orange', rate: 'blue' }[t] || 'default'
}

function feedbackLabel(t: string) {
  return { accept: '采纳', reject: '拒绝', modify: '修改', rate: '评分' }[t] || t
}

async function loadSummary() {
  summaryLoading.value = true
  try {
    const res = await request.get('/v1/agent-feedback/summary', { params: { days: 30 } })
    summaryList.value = res.data.data || []
  } catch {} finally { summaryLoading.value = false }
}

function selectAgent(agentId: string) {
  selectedAgent.value = agentId
  loadGrowthReport()
}

async function loadGrowthReport() {
  if (!selectedAgent.value) return
  reportLoading.value = true
  try {
    const res = await request.get(`/v1/agent-feedback/growth/${selectedAgent.value}`, {
      params: { days: reportDays.value },
    })
    report.value = res.data.data || {}
  } catch {} finally { reportLoading.value = false }
}

async function loadFeedbackList() {
  feedbackLoading.value = true
  try {
    const params: any = {
      skip: (feedbackPagination.current - 1) * feedbackPagination.pageSize,
      limit: feedbackPagination.pageSize,
    }
    if (selectedAgent.value) params.agent_id = selectedAgent.value
    const res = await request.get('/v1/agent-feedback/list', { params })
    feedbackList.value = res.data.data?.items || []
    feedbackPagination.total = res.data.data?.total || 0
  } catch {} finally { feedbackLoading.value = false }
}

function handleFeedbackTableChange(p: any) {
  feedbackPagination.current = p.current
  loadFeedbackList()
}

onMounted(() => {
  loadSummary()
  loadFeedbackList()
})
</script>

<style scoped>
.agent-growth-report { padding: 0; }
</style>
