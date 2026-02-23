<template>
  <div class="push-queue-manage">
    <a-page-header title="推送队列" sub-title="审批和管理推送内容" />

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="mb-4">
      <a-col :xs="8" :sm="8">
        <a-card size="small">
          <a-statistic title="待审批" :value="queueStats.pending" :value-style="{ color: '#faad14' }" />
        </a-card>
      </a-col>
      <a-col :xs="8" :sm="8">
        <a-card size="small">
          <a-statistic title="已批准" :value="queueStats.approved" :value-style="{ color: '#52c41a' }" />
        </a-card>
      </a-col>
      <a-col :xs="8" :sm="8">
        <a-card size="small">
          <a-statistic title="已拒绝" :value="queueStats.rejected" :value-style="{ color: '#ff4d4f' }" />
        </a-card>
      </a-col>
    </a-row>

    <!-- Tab 切换 -->
    <a-tabs v-model:activeKey="activeTab">
      <!-- Tab 1: 推送队列 -->
      <a-tab-pane key="queue" tab="推送队列">
        <!-- 操作栏 -->
        <div style="margin-bottom:12px;text-align:right">
          <a-button
            type="primary"
            :disabled="!selectedRowKeys.length"
            @click="handleBatchApprove"
          >
            批量审批 ({{ selectedRowKeys.length }})
          </a-button>
        </div>

        <a-spin :spinning="queueLoading">
          <div class="list-card-container">
            <a-empty v-if="queueItems.length === 0 && !queueLoading" description="暂无推送队列项" />
            <ListCard v-for="record in queueItems" :key="record.id">
              <template #avatar>
                <a-checkbox
                  :checked="selectedRowKeys.includes(record.id)"
                  @change="(e: any) => toggleSelect(record.id, e.target.checked)"
                  @click.stop
                  style="margin-right: 4px"
                />
              </template>
              <template #title>
                <span>{{ record.student_name || '-' }}</span>
                <a-tag :color="statusColor(record.status)" size="small" style="margin-left: 8px">{{ statusLabel(record.status) }}</a-tag>
              </template>
              <template #subtitle>{{ truncate(record.content, 80) }}</template>
              <template #meta>
                <a-tag size="small">{{ record.source_type }}</a-tag>
                <a-tag :color="priorityColor(record.priority)" size="small">{{ record.priority }}</a-tag>
                <span style="color: #999">{{ formatTime(record.scheduled_at) }}</span>
              </template>
              <template #actions>
                <template v-if="record.status === 'pending'">
                  <a-popconfirm title="确定审批通过？" @confirm="handleApprove(record.id)">
                    <a-button type="link" size="small" style="color:#52c41a">通过</a-button>
                  </a-popconfirm>
                  <a-popconfirm title="确定拒绝？" @confirm="handleReject(record.id)">
                    <a-button type="link" size="small" danger>拒绝</a-button>
                  </a-popconfirm>
                  <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
                </template>
                <span v-else style="color:#999; font-size: 12px">{{ statusLabel(record.status) }}</span>
              </template>
            </ListCard>
          </div>
        </a-spin>
        <div style="display: flex; justify-content: flex-end; margin-top: 16px">
          <a-pagination
            v-model:current="queuePage"
            :page-size="20"
            :total="queueTotal"
            :show-total="(t: number) => `共 ${t} 条`"
            @change="onQueuePageChange"
          />
        </div>
      </a-tab-pane>

      <!-- Tab 2: AI 推送建议 -->
      <a-tab-pane key="recommendations" tab="AI 推送建议">
        <!-- 批量操作栏 -->
        <div v-if="recommendations.length" class="rec-toolbar">
          <div class="rec-toolbar-left">
            <a-checkbox
              :checked="recSelectedAll"
              :indeterminate="recSelectedIndeterminate"
              @change="onRecSelectAllChange"
            >全选</a-checkbox>
            <span v-if="recSelectedIds.length" style="color:#999; font-size:12px; margin-left:8px">
              已选 {{ recSelectedIds.length }} 项
            </span>
          </div>
          <a-button
            type="primary"
            :disabled="!recSelectedIds.length"
            @click="openBatchApplyConfirm"
          >
            批量应用 ({{ recSelectedIds.length }})
          </a-button>
        </div>

        <a-spin :spinning="recLoading">
          <a-empty v-if="!recommendations.length && !recLoading" description="暂无推送建议" />
          <div class="list-card-container">
            <div v-for="item in recommendations" :key="item.student_id" class="rec-card">
              <div class="rec-card-header">
                <div class="rec-card-header-left">
                  <a-checkbox
                    :checked="recSelectedIds.includes(item.student_id)"
                    @change="(e: any) => toggleRecSelect(item.student_id, e.target.checked)"
                    @click.stop
                  />
                  <span class="rec-card-student">学员: {{ item.student_name || `ID ${item.student_id}` }}</span>
                  <a-tag :color="priorityColor(item.priority)" size="small">{{ priorityLabel(item.priority) }}</a-tag>
                </div>
                <div class="rec-card-header-actions">
                  <a-button size="small" @click="openDetailDrawer(item)">查看</a-button>
                  <a-button size="small" type="primary" @click="openSingleApplyConfirm(item)">应用</a-button>
                </div>
              </div>

              <!-- AI 判断依据 -->
              <div v-if="item.reasoning" class="rec-card-reasoning">
                <span class="rec-card-label">AI 判断依据:</span> {{ item.reasoning }}
              </div>

              <!-- 关键指标摘要 -->
              <div v-if="item.data_signals" class="rec-card-metrics">
                <span class="rec-card-label">关键指标:</span>
                <template v-for="(val, key) in extractKeyMetrics(item.data_signals)" :key="key">
                  <span class="metric-item">{{ key }} <b>{{ val }}</b></span>
                </template>
              </div>

              <!-- 推荐评估标签 -->
              <div v-if="item.item_labels && item.item_labels.length" class="rec-card-labels">
                <span class="rec-card-label">推荐评估:</span>
                <a-tag v-for="(label, idx) in item.item_labels" :key="idx" color="blue" size="small">{{ label }}</a-tag>
              </div>
            </div>
          </div>
        </a-spin>
      </a-tab-pane>
    </a-tabs>

    <!-- 编辑队列项 Modal -->
    <a-modal v-model:open="showEditModal" title="编辑推送项" @ok="handleUpdateItem" :confirmLoading="updating">
      <a-form layout="vertical" v-if="editRecord">
        <a-form-item label="内容">
          <a-textarea v-model:value="editForm.content" :rows="3" />
        </a-form-item>
        <a-form-item label="优先级">
          <a-select v-model:value="editForm.priority" style="width:100%">
            <a-select-option value="low">低</a-select-option>
            <a-select-option value="normal">普通</a-select-option>
            <a-select-option value="high">高</a-select-option>
            <a-select-option value="urgent">紧急</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 应用确认 Modal（单条 / 批量） -->
    <a-modal
      v-model:open="showApplyConfirm"
      :title="applyConfirmBatch ? `批量应用确认 (${applyConfirmItems.length} 条)` : '应用 AI 建议确认'"
      :confirmLoading="applyConfirmLoading"
      @ok="handleConfirmApply"
      okText="确认应用"
      cancelText="取消"
      :width="560"
    >
      <!-- 单条模式 -->
      <template v-if="!applyConfirmBatch && applyConfirmItems.length === 1">
        <div class="confirm-section">
          <div class="confirm-row">
            <span class="confirm-label">学员:</span>
            <span>{{ applyConfirmItems[0].student_name || `ID ${applyConfirmItems[0].student_id}` }}</span>
            <a-tag :color="priorityColor(applyConfirmItems[0].priority)" size="small" style="margin-left:8px">
              {{ priorityLabel(applyConfirmItems[0].priority) }}
            </a-tag>
          </div>
          <div v-if="applyConfirmItems[0].reasoning" class="confirm-row">
            <span class="confirm-label">AI 判断依据:</span>
            <span>{{ applyConfirmItems[0].reasoning }}</span>
          </div>
          <div v-if="applyConfirmItems[0].item_labels && applyConfirmItems[0].item_labels.length" class="confirm-row">
            <span class="confirm-label">推荐评估:</span>
            <div style="display:inline-flex;flex-wrap:wrap;gap:4px">
              <a-tag v-for="(label, idx) in applyConfirmItems[0].item_labels" :key="idx" color="blue" size="small">{{ label }}</a-tag>
            </div>
          </div>
          <div v-if="applyConfirmItems[0].items && applyConfirmItems[0].items.length" class="confirm-row">
            <span class="confirm-label">评估条目:</span>
            <span>{{ applyConfirmItems[0].items.join(', ') }}</span>
          </div>
        </div>
        <a-form layout="vertical" style="margin-top:12px">
          <a-form-item label="审核备注">
            <a-textarea v-model:value="applyNote" :rows="2" placeholder="可补充备注信息" />
          </a-form-item>
        </a-form>
      </template>

      <!-- 批量模式 -->
      <template v-else>
        <div class="confirm-batch-list">
          <div v-for="item in applyConfirmItems" :key="item.student_id" class="confirm-batch-item">
            <div class="confirm-batch-header">
              <span class="rec-card-student">{{ item.student_name || `ID ${item.student_id}` }}</span>
              <a-tag :color="priorityColor(item.priority)" size="small">{{ priorityLabel(item.priority) }}</a-tag>
            </div>
            <div v-if="item.reasoning" class="confirm-batch-reasoning">{{ truncate(item.reasoning, 60) }}</div>
            <div v-if="item.item_labels && item.item_labels.length" style="margin-top:2px">
              <a-tag v-for="(label, idx) in item.item_labels" :key="idx" color="blue" size="small">{{ label }}</a-tag>
            </div>
          </div>
        </div>
      </template>
    </a-modal>

    <!-- 详情抽屉 -->
    <a-drawer
      v-model:open="showDetailDrawer"
      title="AI 建议详情"
      :width="480"
      placement="right"
    >
      <template v-if="detailItem">
        <!-- 学员信息 -->
        <a-descriptions :column="1" size="small" bordered style="margin-bottom:16px">
          <a-descriptions-item label="学员">
            {{ detailItem.student_name || `ID ${detailItem.student_id}` }}
          </a-descriptions-item>
          <a-descriptions-item label="优先级">
            <a-tag :color="priorityColor(detailItem.priority)" size="small">{{ priorityLabel(detailItem.priority) }}</a-tag>
          </a-descriptions-item>
        </a-descriptions>

        <!-- AI 判断依据 -->
        <div class="drawer-section">
          <h4>AI 判断依据</h4>
          <p>{{ detailItem.reasoning || '—' }}</p>
        </div>

        <!-- 设备数据 -->
        <div v-if="detailItem.data_signals?.device" class="drawer-section">
          <h4>设备数据 (7 天)</h4>
          <a-descriptions :column="1" size="small" bordered>
            <a-descriptions-item
              v-for="(val, key) in detailItem.data_signals.device"
              :key="key"
              :label="deviceFieldLabel(String(key))"
            >
              {{ formatSignalValue(val) }}
            </a-descriptions-item>
          </a-descriptions>
        </div>

        <!-- 行为数据 -->
        <div v-if="detailItem.data_signals?.behavior" class="drawer-section">
          <h4>行为数据</h4>
          <a-descriptions :column="1" size="small" bordered>
            <a-descriptions-item
              v-for="(val, key) in detailItem.data_signals.behavior"
              :key="key"
              :label="behaviorFieldLabel(String(key))"
            >
              {{ formatSignalValue(val) }}
            </a-descriptions-item>
          </a-descriptions>
        </div>

        <!-- 推荐评估条目 -->
        <div v-if="detailItem.items && detailItem.items.length" class="drawer-section">
          <h4>推荐评估条目</h4>
          <a-table
            :dataSource="detailItem.items.map((code: string, i: number) => ({ code, label: detailItem.item_labels?.[i] || code }))"
            :columns="itemColumns"
            :pagination="false"
            size="small"
            rowKey="code"
          />
        </div>

        <!-- 底部操作 -->
        <div class="drawer-footer">
          <a-button type="primary" block @click="openSingleApplyConfirm(detailItem); showDetailDrawer = false">
            应用此建议
          </a-button>
        </div>
      </template>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { pushQueueApi, pushRecommendationApi } from '@/api/push-queue'
import ListCard from '@/components/core/ListCard.vue'

const activeTab = ref('queue')

// ── 队列统计 ──
const queueStats = ref({ pending: 0, approved: 0, rejected: 0 })

// ── 队列列表 ──
const queueLoading = ref(false)
const queueItems = ref<any[]>([])
const queueTotal = ref(0)
const queuePage = ref(1)
const selectedRowKeys = ref<string[]>([])

function toggleSelect(id: string, checked: boolean) {
  if (checked) {
    if (!selectedRowKeys.value.includes(id)) selectedRowKeys.value.push(id)
  } else {
    selectedRowKeys.value = selectedRowKeys.value.filter(k => k !== id)
  }
}

function priorityColor(p: string) {
  const map: Record<string, string> = { low: 'default', normal: 'blue', medium: 'blue', high: 'orange', urgent: 'red' }
  return map[p] || 'default'
}

function priorityLabel(p: string) {
  const map: Record<string, string> = { low: '低', normal: '普通', medium: '中', high: '高', urgent: '紧急' }
  return map[p] || p
}

function statusColor(s: string) {
  const map: Record<string, string> = { pending: 'gold', approved: 'green', rejected: 'red', sent: 'cyan' }
  return map[s] || 'default'
}

function statusLabel(s: string) {
  const map: Record<string, string> = { pending: '待审批', approved: '已批准', rejected: '已拒绝', sent: '已发送' }
  return map[s] || s
}

function truncate(text: string, len: number) {
  if (!text) return '—'
  return text.length > len ? text.substring(0, len) + '...' : text
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadStats() {
  try {
    const res = await pushQueueApi.stats()
    const data = res.data
    queueStats.value = {
      pending: data.pending || data.stats?.pending || 0,
      approved: data.approved || data.stats?.approved || 0,
      rejected: data.rejected || data.stats?.rejected || 0,
    }
  } catch { /* ignore */ }
}

async function loadQueue() {
  queueLoading.value = true
  try {
    const res = await pushQueueApi.list({
      skip: (queuePage.value - 1) * 20,
      limit: 20,
    })
    const data = res.data
    queueItems.value = data.items || data.queue || []
    queueTotal.value = data.total || queueItems.value.length
  } catch (e) {
    console.error('加载推送队列失败', e)
  } finally {
    queueLoading.value = false
  }
}

function onQueuePageChange(p: number) {
  queuePage.value = p
  loadQueue()
}

// ── 审批操作 ──
async function handleApprove(itemId: string) {
  try {
    await pushQueueApi.approve(itemId)
    message.success('已审批通过')
    loadQueue()
    loadStats()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '审批失败')
  }
}

async function handleReject(itemId: string) {
  try {
    await pushQueueApi.reject(itemId)
    message.success('已拒绝')
    loadQueue()
    loadStats()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '拒绝失败')
  }
}

async function handleBatchApprove() {
  if (!selectedRowKeys.value.length) return
  try {
    await pushQueueApi.batchApprove(selectedRowKeys.value)
    message.success(`批量审批 ${selectedRowKeys.value.length} 项`)
    selectedRowKeys.value = []
    loadQueue()
    loadStats()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '批量审批失败')
  }
}

// ── 编辑推送项 ──
const showEditModal = ref(false)
const editRecord = ref<any>(null)
const updating = ref(false)
const editForm = ref({ content: '', priority: 'normal' })

function openEditModal(record: any) {
  editRecord.value = record
  editForm.value = {
    content: record.content || '',
    priority: record.priority || 'normal',
  }
  showEditModal.value = true
}

async function handleUpdateItem() {
  if (!editRecord.value) return
  updating.value = true
  try {
    await pushQueueApi.update(editRecord.value.id, editForm.value)
    message.success('更新成功')
    showEditModal.value = false
    loadQueue()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '更新失败')
  } finally {
    updating.value = false
  }
}

// ── AI 推送建议 ──
const recLoading = ref(false)
const recommendations = ref<any[]>([])
const recSelectedIds = ref<number[]>([])

const recSelectedAll = computed(() =>
  recommendations.value.length > 0 && recSelectedIds.value.length === recommendations.value.length
)
const recSelectedIndeterminate = computed(() =>
  recSelectedIds.value.length > 0 && recSelectedIds.value.length < recommendations.value.length
)

function toggleRecSelect(studentId: number, checked: boolean) {
  if (checked) {
    if (!recSelectedIds.value.includes(studentId)) recSelectedIds.value.push(studentId)
  } else {
    recSelectedIds.value = recSelectedIds.value.filter(id => id !== studentId)
  }
}

function onRecSelectAllChange(e: any) {
  if (e.target.checked) {
    recSelectedIds.value = recommendations.value.map(r => r.student_id)
  } else {
    recSelectedIds.value = []
  }
}

function extractKeyMetrics(signals: any): Record<string, string> {
  const result: Record<string, string> = {}
  if (!signals) return result
  const device = signals.device || {}
  const behavior = signals.behavior || {}
  if (device.glucose_avg != null) result['血糖均值'] = String(device.glucose_avg)
  if (device.sleep_score != null) result['睡眠'] = String(device.sleep_score)
  if (device.steps_avg != null) result['步数'] = String(device.steps_avg)
  if (device.heart_rate_avg != null) result['心率'] = String(device.heart_rate_avg)
  if (device.hrv_avg != null) result['HRV'] = String(device.hrv_avg)
  if (device.blood_pressure != null) result['血压'] = String(device.blood_pressure)
  if (device.weight != null) result['体重'] = String(device.weight)
  if (behavior.completion_rate != null) result['完成率'] = behavior.completion_rate + '%'
  if (behavior.interruption != null) result['中断'] = behavior.interruption ? '是' : '否'
  if (behavior.streak_days != null) result['连续天数'] = String(behavior.streak_days)
  if (behavior.active_days != null) result['活跃天数'] = String(behavior.active_days)
  return result
}

function deviceFieldLabel(key: string): string {
  const map: Record<string, string> = {
    glucose_avg: '血糖均值', glucose_min: '血糖最低', glucose_max: '血糖最高',
    heart_rate_avg: '心率均值', hrv_avg: 'HRV 均值',
    sleep_score: '睡眠评分', sleep_duration: '睡眠时长',
    steps_avg: '平均步数', blood_pressure: '血压', weight: '体重',
  }
  return map[key] || key
}

function behaviorFieldLabel(key: string): string {
  const map: Record<string, string> = {
    completion_rate: '完成率', interruption: '行为中断', streak_days: '连续天数',
    active_days: '活跃天数', last_active: '最近活跃', total_sessions: '总会话数',
  }
  return map[key] || key
}

function formatSignalValue(val: any): string {
  if (val == null) return '—'
  if (typeof val === 'boolean') return val ? '是' : '否'
  return String(val)
}

const itemColumns = [
  { title: '条目编码', dataIndex: 'code', key: 'code' },
  { title: '条目名称', dataIndex: 'label', key: 'label' },
]

async function loadRecommendations() {
  recLoading.value = true
  try {
    const res = await pushRecommendationApi.getAll()
    const data = res.data
    recommendations.value = (data.recommendations || data || []).map((r: any) => ({ ...r, _applying: false }))
  } catch (e) {
    console.error('加载推送建议失败', e)
  } finally {
    recLoading.value = false
  }
}

// ── 应用确认弹窗 ──
const showApplyConfirm = ref(false)
const applyConfirmBatch = ref(false)
const applyConfirmItems = ref<any[]>([])
const applyConfirmLoading = ref(false)
const applyNote = ref('')

function openSingleApplyConfirm(item: any) {
  applyConfirmBatch.value = false
  applyConfirmItems.value = [item]
  applyNote.value = `[AI建议] ${item.reasoning || ''}`
  showApplyConfirm.value = true
}

function openBatchApplyConfirm() {
  const selected = recommendations.value.filter(r => recSelectedIds.value.includes(r.student_id))
  if (!selected.length) return
  applyConfirmBatch.value = true
  applyConfirmItems.value = selected
  applyNote.value = ''
  showApplyConfirm.value = true
}

async function handleConfirmApply() {
  applyConfirmLoading.value = true
  let successCount = 0
  let failCount = 0
  try {
    for (const item of applyConfirmItems.value) {
      try {
        await pushRecommendationApi.apply(item.student_id)
        successCount++
      } catch {
        failCount++
      }
    }
    if (failCount === 0) {
      message.success(`已成功应用 ${successCount} 条建议`)
    } else {
      message.warning(`应用完成: ${successCount} 成功, ${failCount} 失败`)
    }
    showApplyConfirm.value = false
    recSelectedIds.value = []
    loadQueue()
    loadStats()
    loadRecommendations()
  } finally {
    applyConfirmLoading.value = false
  }
}

// ── 详情抽屉 ──
const showDetailDrawer = ref(false)
const detailItem = ref<any>(null)

function openDetailDrawer(item: any) {
  detailItem.value = item
  showDetailDrawer.value = true
}

onMounted(() => {
  loadStats()
  loadQueue()
  loadRecommendations()
})
</script>

<style scoped>
.push-queue-manage { padding: 16px; }
.mb-4 { margin-bottom: 16px; }
.list-card-container { display: flex; flex-direction: column; gap: 10px; }

/* AI 建议 - 操作栏 */
.rec-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 8px;
}
.rec-toolbar-left {
  display: flex;
  align-items: center;
}

/* AI 建议 - 卡片 */
.rec-card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  padding: 14px 16px;
  transition: box-shadow 0.2s;
}
.rec-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
.rec-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.rec-card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rec-card-header-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.rec-card-student {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}
.rec-card-reasoning {
  margin-top: 8px;
  font-size: 13px;
  color: #555;
  line-height: 1.5;
}
.rec-card-metrics {
  margin-top: 6px;
  font-size: 12px;
  color: #666;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}
.metric-item {
  padding: 2px 8px;
  background: #f6f6f6;
  border-radius: 4px;
  white-space: nowrap;
}
.metric-item b {
  color: #333;
}
.rec-card-labels {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}
.rec-card-label {
  font-size: 12px;
  color: #999;
  margin-right: 4px;
  white-space: nowrap;
}

/* 确认弹窗 */
.confirm-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.confirm-row {
  font-size: 13px;
  line-height: 1.6;
}
.confirm-label {
  color: #999;
  margin-right: 6px;
}
.confirm-batch-list {
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.confirm-batch-item {
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}
.confirm-batch-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.confirm-batch-reasoning {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
}

/* 详情抽屉 */
.drawer-section {
  margin-bottom: 16px;
}
.drawer-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #f0f0f0;
}
.drawer-section p {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
  margin: 0;
}
.drawer-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

@media (max-width: 640px) {
  .rec-card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .rec-card-header-actions {
    width: 100%;
  }
  .rec-card-header-actions .ant-btn {
    flex: 1;
  }
  .rec-toolbar {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
}
</style>
