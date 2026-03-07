<template>
  <div>
    <div class="page-header">
      <h2>评估管理</h2>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button v-for="t in tabs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="switchTab(t.key)">
        {{ t.label }}
        <span v-if="t.count > 0" class="tab-badge">{{ t.count }}</span>
      </button>
    </div>

    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="items.length === 0" class="empty">暂无数据</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>学员</th>
            <th>量表</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.student_name || item.user_name || '—' }}</td>
            <td>{{ item.scale_name || item.scale_id || '—' }}</td>
            <td><span class="status-tag" :class="'st-' + item.status">{{ statusLabel(item.status) }}</span></td>
            <td>{{ item.created_at?.slice(0, 10) || '—' }}</td>
            <td>
              <button v-if="item.status === 'completed'" class="action-btn" @click="reviewItem(item)">审核</button>
              <button v-if="item.status === 'pending'" class="action-btn action-remind" @click="remindItem(item)">催促</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 审核 Modal -->
    <div v-if="reviewing" class="modal-overlay" @click.self="reviewing = null">
      <div class="modal">
        <div class="modal-header">
          <h3>审核评估 — {{ reviewing.student_name }}</h3>
          <button class="modal-close" @click="reviewing = null">✕</button>
        </div>
        <div class="modal-body">
          <div class="review-info">
            <div><strong>量表：</strong>{{ reviewing.scale_name || reviewing.scale_id }}</div>
            <div><strong>状态：</strong>{{ reviewing.status }}</div>
          </div>
          <div v-if="reviewing.pipeline_result" class="pipeline-result">
            <h4>AI分析结果</h4>
            <pre>{{ typeof reviewing.pipeline_result === 'object' ? JSON.stringify(reviewing.pipeline_result, null, 2) : reviewing.pipeline_result }}</pre>
          </div>
          <div v-else class="empty" style="margin-top:12px">暂无AI分析结果</div>
          <div class="review-note-wrap">
            <label>审核备注</label>
            <textarea v-model="reviewNote" rows="3" placeholder="可选备注..." class="note-textarea"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="act-btn act-secondary" @click="reviewing = null">取消</button>
          <button class="act-btn act-primary" @click="submitReview">标记已审核</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/index'

const activeTab = ref('completed')
const loading = ref(true)
const items = ref<any[]>([])
const reviewing = ref<any>(null)
const reviewNote = ref('')

const tabCounts = ref({ completed: 0, pending: 0, reviewed: 0 })
const tabs = computed(() => [
  { key: 'completed', label: '待审核', count: tabCounts.value.completed },
  { key: 'pending',   label: '待完成', count: tabCounts.value.pending },
  { key: 'reviewed',  label: '已完成', count: 0 },
])

function statusLabel(s: string) {
  const m: Record<string, string> = { pending: '待完成', completed: '待审核', reviewed: '已审核', pushed: '已推送' }
  return m[s] || s
}

async function loadData(status: string) {
  loading.value = true
  try {
    const res: any = await api.get(`/api/v1/assessment-assignments/coach-list?status=${status}`)
    items.value = res.items || res || []
    tabCounts.value[status as keyof typeof tabCounts.value] = items.value.length
  } catch { items.value = [] }
  loading.value = false
}

async function switchTab(t: string) {
  activeTab.value = t
  await loadData(t)
}

function reviewItem(item: any) {
  reviewing.value = item
  reviewNote.value = ''
}

async function remindItem(item: any) {
  try {
    await api.post(`/api/v1/assessment-assignments/${item.id}/remind`)
    alert('已发送催促通知')
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

async function submitReview() {
  if (!reviewing.value) return
  try {
    await api.post(`/api/v1/assessment-assignments/${reviewing.value.id}/review`, { note: reviewNote.value })
    reviewing.value = null
    await loadData(activeTab.value)
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

onMounted(() => loadData('completed'))
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }

.tabs { display: flex; gap: 4px; margin-bottom: 16px; }
.tab-btn {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  font-size: 13px;
  cursor: pointer;
  color: #6b7280;
  display: flex; align-items: center; gap: 6px;
}
.tab-btn.active { background: #3b82f6; color: #fff; border-color: #3b82f6; }
.tab-badge {
  background: #ef4444;
  color: #fff;
  border-radius: 10px;
  font-size: 11px;
  padding: 1px 6px;
  font-weight: 600;
}

.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; color: #6b7280; font-weight: 500; border-bottom: 2px solid #f3f4f6; }
.data-table td { padding: 12px; color: #374151; border-bottom: 1px solid #f9fafb; }
.data-table tr:last-child td { border-bottom: none; }

.status-tag { padding: 3px 10px; border-radius: 10px; font-size: 11px; font-weight: 500; }
.st-pending  { background: #fef3c7; color: #d97706; }
.st-completed{ background: #dbeafe; color: #1d4ed8; }
.st-reviewed { background: #d1fae5; color: #065f46; }
.st-pushed   { background: #ede9fe; color: #5b21b6; }

.action-btn { padding: 5px 12px; border-radius: 6px; background: #3b82f6; color: #fff; border: none; font-size: 12px; cursor: pointer; }
.action-btn:hover { background: #2563eb; }
.action-remind { background: #f59e0b; }
.action-remind:hover { background: #d97706; }

/* modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; border-radius: 12px; padding: 24px; width: 560px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.2); max-height: 80vh; overflow-y: auto; }
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-header h3 { font-size: 16px; font-weight: 600; margin: 0; }
.modal-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #9ca3af; }
.modal-body { margin-bottom: 20px; }
.modal-footer { display: flex; gap: 8px; justify-content: flex-end; }

.review-info { background: #f9fafb; border-radius: 8px; padding: 12px; margin-bottom: 12px; font-size: 14px; line-height: 1.8; }
.pipeline-result { background: #1e293b; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
.pipeline-result h4 { color: #94a3b8; font-size: 12px; font-weight: 500; margin: 0 0 8px; }
.pipeline-result pre { color: #e2e8f0; font-size: 12px; margin: 0; white-space: pre-wrap; }
.review-note-wrap label { font-size: 13px; font-weight: 500; color: #374151; display: block; margin-bottom: 6px; }
.note-textarea { width: 100%; padding: 10px; border: 1px solid #e5e7eb; border-radius: 8px; font-size: 14px; resize: vertical; outline: none; box-sizing: border-box; }
.note-textarea:focus { border-color: #3b82f6; }

.act-btn { padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; }
.act-primary { background: #3b82f6; color: #fff; }
.act-primary:hover { background: #2563eb; }
.act-secondary { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }

.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
