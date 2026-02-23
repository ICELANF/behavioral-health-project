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
        <a-spin :spinning="recLoading">
          <a-empty v-if="!recommendations.length && !recLoading" description="暂无推送建议" />
          <a-list :data-source="recommendations" item-layout="horizontal">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <span>学员: {{ item.student_name || `ID ${item.student_id}` }}</span>
                    <a-tag :color="priorityColor(item.priority)" style="margin-left:8px">{{ item.priority }}</a-tag>
                  </template>
                  <template #description>
                    <div>{{ item.reason || item.recommendation_text || '—' }}</div>
                    <div v-if="item.suggested_scale" style="margin-top:4px;color:#999;font-size:12px">
                      建议量表: {{ item.suggested_scale }}
                    </div>
                  </template>
                </a-list-item-meta>
                <template #actions>
                  <a-button size="small" type="primary" :loading="item._applying" @click="handleApplyRecommendation(item)">
                    一键应用
                  </a-button>
                </template>
              </a-list-item>
            </template>
          </a-list>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
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

// columns removed — now using ListCard layout

function toggleSelect(id: string, checked: boolean) {
  if (checked) {
    if (!selectedRowKeys.value.includes(id)) selectedRowKeys.value.push(id)
  } else {
    selectedRowKeys.value = selectedRowKeys.value.filter(k => k !== id)
  }
}

function priorityColor(p: string) {
  const map: Record<string, string> = { low: 'default', normal: 'blue', high: 'orange', urgent: 'red' }
  return map[p] || 'default'
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

// onSelectChange removed — now using toggleSelect with ListCard checkboxes

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

async function handleApplyRecommendation(item: any) {
  item._applying = true
  try {
    const res = await pushRecommendationApi.apply(item.student_id)
    message.success('已应用推荐，队列已更新')
    // Refresh both tabs
    loadQueue()
    loadStats()
    loadRecommendations()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '应用失败')
  } finally {
    item._applying = false
  }
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
</style>
