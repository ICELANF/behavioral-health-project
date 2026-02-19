<template>
  <div class="coach-copilot border-l bg-gray-50 h-full flex flex-col">
    <!-- Header with connection status -->
    <div class="p-4 border-b bg-white font-bold flex justify-between items-center">
      <span>AI 教练共驾台</span>
      <div class="flex items-center gap-2">
        <span class="status-dot" :class="connectionStatus"></span>
        <span class="text-xs" :class="statusTextClass">{{ statusLabel }}</span>
      </div>
    </div>

    <!-- Tab bar -->
    <div class="tab-bar">
      <button class="tab-btn" :class="{ active: activeTab === 'live' }" @click="activeTab = 'live'">实时处方</button>
      <button class="tab-btn" :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'; loadHistory()">历史记录</button>
    </div>

    <!-- Live prescription stream -->
    <div v-if="activeTab === 'live'" class="flex-1 overflow-y-auto p-4 space-y-4">
      <div v-for="(item, index) in prescriptionStream" :key="index"
           class="p-4 rounded-lg border bg-white shadow-sm">
        <div class="flex items-center mb-2">
          <span :class="riskColor(item.risk_level)" class="w-2 h-2 rounded-full mr-2"></span>
          <span class="text-sm font-medium">风险分级: {{ item.risk_level }}</span>
          <span class="text-xs text-gray-400 ml-auto">{{ item._time || '' }}</span>
        </div>

        <p class="text-gray-700 text-sm mb-3">{{ item.instruction }}</p>

        <!-- Action buttons -->
        <div class="action-buttons mb-2">
          <button
            class="action-btn accept"
            :disabled="item._adopted"
            @click="adoptPrescription(item, index)"
          >{{ item._adopted ? '已采纳' : '采纳' }}</button>
          <button
            class="action-btn ignore"
            :disabled="item._ignored"
            @click="ignorePrescription(item, index)"
          >{{ item._ignored ? '已忽略' : '忽略' }}</button>
        </div>

        <div class="mt-2 pt-2 border-t">
          <p class="text-xs text-gray-400 mb-2">建议干预工具：</p>

          <component
            :is="toolMapper[item.suggested_tool]"
            v-if="toolMapper[item.suggested_tool]"
            v-bind="item.tool_props"
            @action="(data) => handleToolAction(data, item)"
          />
          <div v-else-if="item.suggested_tool && item.suggested_tool !== 'GENERAL_CHAT'" class="text-xs text-orange-500 bg-orange-50 p-2 rounded">
            未定义的工具组件: {{ item.suggested_tool }}
          </div>
        </div>

        <!-- Tool action feedback -->
        <div v-if="item._toolFeedback" class="tool-feedback mt-2">
          <span class="feedback-icon">✓</span>
          <span class="feedback-text">{{ item._toolFeedback }}</span>
        </div>
      </div>

      <div v-if="transitionEvent" class="p-4 rounded-lg border-2 border-green-400 bg-green-50">
        <div class="text-sm font-bold text-green-700 mb-1">阶段迁移通知</div>
        <p class="text-sm text-green-600">
          {{ transitionEvent.from }} → {{ transitionEvent.to }}
        </p>
        <p class="text-xs text-green-500 mt-1">{{ transitionEvent.reason }}</p>
      </div>

      <div v-if="prescriptionStream.length === 0 && !isConnecting" class="text-center text-gray-400 mt-8">
        <p>等待用户对话...</p>
        <p class="text-xs mt-1">命中触发规则后将实时显示教练处方</p>
        <button class="connect-btn mt-4" @click="connectSSE">连接实时推送</button>
      </div>

      <div v-if="isConnecting" class="text-center text-blue-400 mt-8">
        <div class="loading-spinner"></div>
        <p class="text-xs mt-2">正在连接...</p>
      </div>
    </div>

    <!-- History panel -->
    <div v-if="activeTab === 'history'" class="flex-1 overflow-y-auto p-4 space-y-3">
      <div v-if="historyLoading" class="text-center text-gray-400 mt-8">
        <div class="loading-spinner"></div>
        <p class="text-xs mt-2">加载中...</p>
      </div>
      <div v-else-if="historyList.length === 0" class="text-center text-gray-400 mt-8">
        <p>暂无历史记录</p>
      </div>
      <div v-for="(record, i) in historyList" :key="i" class="history-card">
        <div class="history-header">
          <span :class="riskColor(record.risk_level)" class="w-2 h-2 rounded-full mr-2"></span>
          <span class="text-xs font-medium">{{ record.risk_level }}</span>
          <span class="text-xs text-gray-400 ml-auto">{{ record.created_at }}</span>
        </div>
        <p class="text-xs text-gray-600 mt-1">{{ record.instruction }}</p>
        <div class="history-meta mt-1">
          <span v-if="record.adopted" class="meta-tag adopted">已采纳</span>
          <span v-if="record.ignored" class="meta-tag ignored">已忽略</span>
          <span class="meta-tag tool">{{ record.suggested_tool }}</span>
        </div>
      </div>
      <div v-if="historyList.length > 0" class="text-center mt-2">
        <button class="load-more-btn" @click="loadMoreHistory">加载更多</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineAsyncComponent, onBeforeUnmount } from 'vue'
import { copilotApi } from '../../api/copilot'

const toolMapper = {
  "STRESS_ASSESSMENT_FORM": defineAsyncComponent(() => import('./tools/StressForm.vue')),
  "EMPATHY_MODULE_01": defineAsyncComponent(() => import('./tools/EmpathyGuide.vue')),
  "HABIT_DESIGNER": defineAsyncComponent(() => import('./tools/HabitCard.vue')),
  "GENERAL_CHAT": null
}

const activeTab = ref('live')
const prescriptionStream = ref([])
const transitionEvent = ref(null)
const connectionStatus = ref('disconnected')
const isConnecting = ref(false)
let eventSource = null

// History
const historyList = ref([])
const historyLoading = ref(false)
const historyPage = ref(1)

const statusLabel = computed(() => {
  const map = { connected: '已连接', connecting: '连接中...', disconnected: '未连接', error: '连接异常' }
  return map[connectionStatus.value] || '未知'
})

const statusTextClass = computed(() => {
  const map = { connected: 'text-green-500', connecting: 'text-blue-500', disconnected: 'text-gray-400', error: 'text-red-500' }
  return map[connectionStatus.value] || 'text-gray-400'
})

const riskColor = (level) => {
  if (level === 'L2') return 'bg-red-500'
  if (level === 'L1') return 'bg-yellow-500'
  return 'bg-green-500'
}

const connectSSE = async () => {
  const userId = localStorage.getItem('admin_username') || 'coach1'
  isConnecting.value = true
  connectionStatus.value = 'connecting'

  try {
    const stream = await copilotApi.streamPrescription(userId)
    if (stream && typeof stream.onmessage !== 'undefined') {
      eventSource = stream
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'prescription') {
            const items = (data.outputs?.to_coach || []).map(item => ({
              ...item,
              _time: new Date().toLocaleTimeString(),
              _adopted: false,
              _ignored: false,
              _toolFeedback: null,
            }))
            prescriptionStream.value.push(...items)
          }
          if (data.transition_event) {
            transitionEvent.value = data.transition_event
          }
        } catch (e) { /* parse error */ }
      }
      eventSource.onerror = () => {
        connectionStatus.value = 'error'
        isConnecting.value = false
      }
      connectionStatus.value = 'connected'
    }
  } catch (e) {
    connectionStatus.value = 'error'
  }
  isConnecting.value = false
}

const adoptPrescription = async (item, index) => {
  prescriptionStream.value[index]._adopted = true
  prescriptionStream.value[index]._ignored = false
  try {
    await copilotApi.submitToolAction(item._prescriptionId || `rx_${index}`, { action: 'adopt', instruction: item.instruction })
  } catch (e) { /* fallback */ }
}

const ignorePrescription = async (item, index) => {
  prescriptionStream.value[index]._ignored = true
  prescriptionStream.value[index]._adopted = false
  try {
    await copilotApi.submitToolAction(item._prescriptionId || `rx_${index}`, { action: 'ignore', instruction: item.instruction })
  } catch (e) { /* fallback */ }
}

const handleToolAction = async (data, item) => {
  console.log('执行工具动作:', data)
  const idx = prescriptionStream.value.indexOf(item)
  if (idx > -1) {
    const feedbackMap = {
      start: '已开始测评',
      skip: '已跳过',
      submit: '结果已提交',
      start_listen: '进入倾听模式',
      end_listen: '倾听已结束',
      create: '习惯卡已生成',
      template: '正在选择模板',
    }
    prescriptionStream.value[idx]._toolFeedback = feedbackMap[data.action] || '操作完成'
  }
  try {
    await copilotApi.submitToolAction(item._prescriptionId || 'unknown', { action: data.action, tool: data.tool, data: data.data })
  } catch (e) { /* fallback */ }
}

const loadHistory = async () => {
  historyLoading.value = true
  historyPage.value = 1
  try {
    const coachId = localStorage.getItem('admin_username') || 'coach1'
    const res = await copilotApi.getPrescriptionHistory(coachId, { page: 1, pageSize: 20 })
    historyList.value = res?.data?.list || res?.list || []
  } catch (e) {
    console.warn('加载处方历史失败:', e)
  }
  historyLoading.value = false
}

const loadMoreHistory = async () => {
  historyPage.value++
  try {
    const coachId = localStorage.getItem('admin_username') || 'coach1'
    const res = await copilotApi.getPrescriptionHistory(coachId, { page: historyPage.value, pageSize: 20 })
    const newItems = res?.data?.list || res?.list || []
    historyList.value.push(...newItems)
  } catch (e) { /* no more */ }
}

const pushPrescription = (data) => {
  const items = (data.outputs?.to_coach || []).map(item => ({
    ...item,
    _time: new Date().toLocaleTimeString(),
    _adopted: false,
    _ignored: false,
    _toolFeedback: null,
  }))
  prescriptionStream.value = items
  transitionEvent.value = data.transition_event || null
}

onBeforeUnmount(() => {
  if (eventSource) { eventSource.close(); eventSource = null }
})

defineExpose({ pushPrescription })
</script>

<style scoped>
.coach-copilot { width: 380px; }
.tab-bar { display: flex; border-bottom: 1px solid #e5e7eb; background: #fff; }
.tab-btn { flex: 1; padding: 8px; font-size: 13px; border: none; background: none; cursor: pointer; color: #666; border-bottom: 2px solid transparent; }
.tab-btn.active { color: #1890ff; border-bottom-color: #1890ff; font-weight: 500; }

.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-dot.connected { background: #16a34a; }
.status-dot.connecting { background: #3b82f6; animation: blink 1s infinite; }
.status-dot.disconnected { background: #9ca3af; }
.status-dot.error { background: #dc2626; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.action-buttons { display: flex; gap: 8px; }
.action-btn { font-size: 11px; padding: 3px 10px; border-radius: 4px; border: 1px solid #ddd; cursor: pointer; background: #fff; }
.action-btn.accept { color: #16a34a; border-color: #bbf7d0; }
.action-btn.accept:hover { background: #f0fdf4; }
.action-btn.accept:disabled { background: #dcfce7; color: #16a34a; cursor: default; }
.action-btn.ignore { color: #9ca3af; border-color: #e5e7eb; }
.action-btn.ignore:hover { background: #f9fafb; }
.action-btn.ignore:disabled { background: #f3f4f6; cursor: default; }

.tool-feedback { display: flex; align-items: center; gap: 4px; padding: 4px 8px; background: #f0fdf4; border-radius: 4px; }
.feedback-icon { color: #16a34a; font-size: 12px; }
.feedback-text { font-size: 11px; color: #16a34a; }

.connect-btn { font-size: 12px; padding: 6px 16px; background: #1890ff; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.connect-btn:hover { background: #096dd9; }

.loading-spinner { width: 24px; height: 24px; border: 2px solid #e5e7eb; border-top-color: #1890ff; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto; }
@keyframes spin { to { transform: rotate(360deg); } }

.history-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; }
.history-header { display: flex; align-items: center; }
.history-meta { display: flex; gap: 4px; }
.meta-tag { font-size: 10px; padding: 1px 6px; border-radius: 3px; }
.meta-tag.adopted { background: #dcfce7; color: #16a34a; }
.meta-tag.ignored { background: #f3f4f6; color: #9ca3af; }
.meta-tag.tool { background: #eff6ff; color: #3b82f6; }

.load-more-btn { font-size: 12px; padding: 4px 16px; background: none; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer; color: #666; }
</style>
