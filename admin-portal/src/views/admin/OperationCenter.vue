<template>
  <div class="operation-center">
    <a-page-header title="运营中心" sub-title="实时监控平台运行状态" style="padding: 0 0 16px">
      <template #extra>
        <a-space>
          <a-switch v-model:checked="autoRefresh" checked-children="自动刷新" un-checked-children="手动" />
          <a-button type="primary" @click="refreshAll" :loading="refreshing">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- KPI 卡片 -->
    <a-row :gutter="16" class="kpi-row">
      <a-col :xs="12" :sm="8" :lg="4" v-for="kpi in kpiCards" :key="kpi.key">
        <a-card :bordered="false" size="small">
          <a-statistic :title="kpi.title" :value="kpi.value" :value-style="{ color: kpi.color, fontSize: '24px' }">
            <template #suffix><span style="font-size:14px">{{ kpi.suffix }}</span></template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- Tabs -->
    <a-tabs v-model:activeKey="activeTab" style="margin-top: 16px" @change="onTabChange">
      <!-- Tab 1: 商务线索 -->
      <a-tab-pane key="leads" tab="商务线索">
        <a-card :bordered="false">
          <template #extra>
            <a-select v-model:value="leadFilter" style="width: 120px" @change="fetchLeads">
              <a-select-option value="">全部状态</a-select-option>
              <a-select-option value="pending">待处理</a-select-option>
              <a-select-option value="contacted">已联系</a-select-option>
              <a-select-option value="closed">已关闭</a-select-option>
            </a-select>
          </template>
          <a-table
            :columns="leadColumns"
            :data-source="leads"
            :loading="loadingLeads"
            :pagination="{ current: leadPage, pageSize: 15, total: leadTotal, onChange: onLeadPageChange }"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
              </template>
              <template v-if="column.key === 'solution'">
                {{ solutionLabel(record.solution) }}
              </template>
              <template v-if="column.key === 'created_at'">
                {{ formatTime(record.created_at) }}
              </template>
              <template v-if="column.key === 'action'">
                <a-space>
                  <a-button v-if="record.status === 'pending'" size="small" type="link" @click="updateLeadStatus(record.id, 'contacted')">标记已联系</a-button>
                  <a-button v-if="record.status !== 'closed'" size="small" type="link" danger @click="updateLeadStatus(record.id, 'closed')">关闭</a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <!-- Tab 2: 系统日志 -->
      <a-tab-pane key="logs" tab="系统日志">
        <a-card :bordered="false">
          <template #extra>
            <a-space>
              <a-select v-model:value="logLevel" style="width: 100px" @change="fetchLogs" placeholder="级别">
                <a-select-option value="">全部</a-select-option>
                <a-select-option value="ERROR">ERROR</a-select-option>
                <a-select-option value="WARNING">WARNING</a-select-option>
                <a-select-option value="INFO">INFO</a-select-option>
              </a-select>
              <a-select v-model:value="logDate" style="width: 140px" @change="fetchLogs" placeholder="日期">
                <a-select-option v-for="d in availableDates" :key="d" :value="d">{{ d }}</a-select-option>
              </a-select>
              <a-input-search v-model:value="logKeyword" placeholder="搜索关键词" style="width: 180px" @search="fetchLogs" allow-clear />
            </a-space>
          </template>
          <a-table
            :columns="logColumns"
            :data-source="logEntries"
            :loading="loadingLogs"
            :pagination="{ current: logPage, pageSize: 50, total: logTotal, onChange: onLogPageChange }"
            row-key="_idx"
            size="small"
            :row-class-name="logRowClass"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'level'">
                <a-tag :color="levelColor(record.level)">{{ record.level }}</a-tag>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <!-- Tab 3: 事件流 -->
      <a-tab-pane key="events" tab="事件流">
        <a-card :bordered="false">
          <template #extra>
            <a-select v-model:value="eventTypeFilter" style="width: 120px" @change="fetchEvents">
              <a-select-option value="">全部类型</a-select-option>
              <a-select-option value="demo_request">预约请求</a-select-option>
              <a-select-option value="notification">系统通知</a-select-option>
            </a-select>
          </template>
          <a-timeline style="padding: 16px 0">
            <a-timeline-item
              v-for="ev in eventList"
              :key="ev.id"
              :color="eventColor(ev)"
            >
              <div class="ev-row">
                <a-tag :color="ev.type === 'demo_request' ? 'blue' : 'green'" size="small">{{ ev.type === 'demo_request' ? '预约' : '通知' }}</a-tag>
                <span class="ev-title">{{ ev.title }}</span>
                <span class="ev-time">{{ formatTime(ev.time) }}</span>
              </div>
              <div class="ev-detail">{{ ev.detail }}</div>
            </a-timeline-item>
          </a-timeline>
          <div v-if="eventList.length === 0 && !loadingEvents" style="text-align: center; padding: 40px; color: #999">暂无事件</div>
          <div v-if="eventTotal > eventList.length" style="text-align: center; padding: 12px">
            <a-button type="link" @click="loadMoreEvents" :loading="loadingEvents">加载更多</a-button>
          </div>
        </a-card>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import request from '../../api/request'

// ── State ──
const refreshing = ref(false)
const autoRefresh = ref(true)
const activeTab = ref('leads')
let refreshTimer: ReturnType<typeof setInterval> | null = null

// KPI
const stats = reactive({
  total_requests: 0,
  pending_requests: 0,
  today_requests: 0,
  unread_notifications: 0,
  error_count_today: 0,
})

const kpiCards = computed(() => [
  { key: 'total', title: '预约总数', value: stats.total_requests, color: '#1890ff', suffix: '' },
  { key: 'pending', title: '待处理', value: stats.pending_requests, color: '#faad14', suffix: '' },
  { key: 'today', title: '今日新增', value: stats.today_requests, color: '#52c41a', suffix: '' },
  { key: 'unread', title: '未读通知', value: stats.unread_notifications, color: '#722ed1', suffix: '' },
  { key: 'errors', title: '今日错误', value: stats.error_count_today, color: stats.error_count_today > 0 ? '#ff4d4f' : '#52c41a', suffix: '' },
])

// ── Leads ──
const leads = ref<any[]>([])
const leadTotal = ref(0)
const leadPage = ref(1)
const leadFilter = ref('')
const loadingLeads = ref(false)

const leadColumns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '姓名', dataIndex: 'name', key: 'name', width: 80 },
  { title: '机构', dataIndex: 'organization', key: 'organization', ellipsis: true },
  { title: '职位', dataIndex: 'title', key: 'title', width: 100 },
  { title: '电话', dataIndex: 'phone', key: 'phone', width: 130 },
  { title: '方案', key: 'solution', width: 80 },
  { title: '状态', key: 'status', width: 90 },
  { title: '时间', key: 'created_at', width: 160 },
  { title: '操作', key: 'action', width: 160 },
]

// ── Logs ──
const logEntries = ref<any[]>([])
const logTotal = ref(0)
const logPage = ref(1)
const logLevel = ref('')
const logDate = ref('')
const logKeyword = ref('')
const availableDates = ref<string[]>([])
const loadingLogs = ref(false)

const logColumns = [
  { title: '时间', dataIndex: 'time', key: 'time', width: 180 },
  { title: '级别', key: 'level', width: 80 },
  { title: '来源', dataIndex: 'source', key: 'source', width: 200, ellipsis: true },
  { title: '消息', dataIndex: 'message', key: 'message', ellipsis: true },
]

// ── Events ──
const eventList = ref<any[]>([])
const eventTotal = ref(0)
const eventTypeFilter = ref('')
const loadingEvents = ref(false)
let eventSkip = 0

// ── Fetch functions ──
async function fetchStats() {
  try {
    const res = await request.get('v1/admin/operation-center/stats')
    Object.assign(stats, res.data)
  } catch { /* keep defaults */ }
}

async function fetchLeads() {
  loadingLeads.value = true
  try {
    const skip = (leadPage.value - 1) * 15
    const params: any = { skip, limit: 15 }
    if (leadFilter.value) params.status = leadFilter.value
    const res = await request.get('v1/demo-requests', { params })
    leads.value = res.data.items || []
    leadTotal.value = res.data.total || 0
  } catch { leads.value = [] } finally { loadingLeads.value = false }
}

async function fetchLogs() {
  loadingLogs.value = true
  try {
    const skip = (logPage.value - 1) * 50
    const params: any = { skip, limit: 50 }
    if (logLevel.value) params.level = logLevel.value
    if (logDate.value) params.date = logDate.value
    if (logKeyword.value) params.keyword = logKeyword.value
    const res = await request.get('v1/admin/operation-center/logs', { params })
    logEntries.value = (res.data.items || []).map((e: any, i: number) => ({ ...e, _idx: skip + i }))
    logTotal.value = res.data.total || 0
    if (res.data.available_dates?.length) {
      availableDates.value = res.data.available_dates
      if (!logDate.value && availableDates.value.length) {
        logDate.value = availableDates.value[0]
      }
    }
  } catch { logEntries.value = [] } finally { loadingLogs.value = false }
}

async function fetchEvents(reset = true) {
  loadingEvents.value = true
  if (reset) { eventList.value = []; eventSkip = 0 }
  try {
    const params: any = { skip: eventSkip, limit: 30 }
    if (eventTypeFilter.value) params.event_type = eventTypeFilter.value
    const res = await request.get('v1/admin/operation-center/events', { params })
    const items = res.data.items || []
    if (reset) {
      eventList.value = items
    } else {
      eventList.value.push(...items)
    }
    eventTotal.value = res.data.total || 0
  } catch { /* keep existing */ } finally { loadingEvents.value = false }
}

function loadMoreEvents() {
  eventSkip += 30
  fetchEvents(false)
}

async function updateLeadStatus(id: number, status: string) {
  try {
    await request.put(`v1/demo-requests/${id}/status`, { status })
    message.success('状态已更新')
    fetchLeads()
    fetchStats()
  } catch {
    message.error('更新失败')
  }
}

// ── Tab / Page change ──
function onTabChange(key: string) {
  if (key === 'leads') fetchLeads()
  else if (key === 'logs') fetchLogs()
  else if (key === 'events') fetchEvents()
}

function onLeadPageChange(page: number) {
  leadPage.value = page
  fetchLeads()
}

function onLogPageChange(page: number) {
  logPage.value = page
  fetchLogs()
}

// ── Refresh ──
async function refreshAll() {
  refreshing.value = true
  await Promise.all([fetchStats(), fetchLeads()])
  refreshing.value = false
}

// ── Helpers ──
function statusColor(s: string) {
  return { pending: 'orange', contacted: 'blue', closed: 'default' }[s] || 'default'
}
function statusLabel(s: string) {
  return { pending: '待处理', contacted: '已联系', closed: '已关闭' }[s] || s
}
function solutionLabel(s: string) {
  return { hospital: '医院', insurance: '商保', government: '政府', rwe: 'RWE' }[s] || s || '-'
}
function levelColor(l: string) {
  return { ERROR: 'red', CRITICAL: 'red', WARNING: 'orange', INFO: 'blue', DEBUG: 'default' }[l] || 'default'
}
function logRowClass(record: any) {
  if (record.level === 'ERROR' || record.level === 'CRITICAL') return 'log-row-error'
  if (record.level === 'WARNING') return 'log-row-warn'
  return ''
}
function eventColor(ev: any) {
  if (ev.priority === 'high') return 'red'
  if (ev.type === 'demo_request') return 'blue'
  return 'green'
}
function formatTime(t: string) {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}

// ── Lifecycle ──
onMounted(() => {
  fetchStats()
  fetchLeads()
  // Auto-refresh every 30s
  refreshTimer = setInterval(() => {
    if (autoRefresh.value) {
      fetchStats()
      if (activeTab.value === 'leads') fetchLeads()
      else if (activeTab.value === 'logs') fetchLogs()
      else if (activeTab.value === 'events') fetchEvents()
    }
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.operation-center {
  padding: 0;
}
.kpi-row {
  margin-bottom: 8px;
}
.ev-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ev-title {
  font-weight: 500;
}
.ev-time {
  margin-left: auto;
  color: #999;
  font-size: 12px;
}
.ev-detail {
  color: #666;
  font-size: 13px;
  margin-top: 4px;
  padding-left: 4px;
}
:deep(.log-row-error) {
  background-color: #fff2f0 !important;
}
:deep(.log-row-warn) {
  background-color: #fffbe6 !important;
}
</style>
