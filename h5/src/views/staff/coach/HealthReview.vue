<template>
  <div>
    <div class="page-header">
      <h2>健康数据审核</h2>
    </div>
    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="items.length === 0" class="empty">暂无待审健康数据</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>学员</th><th>数据类型</th><th>数值</th><th>状态</th><th>时间</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.user_name || item.student_name || '—' }}</td>
            <td>{{ item.data_type || item.type || '—' }}</td>
            <td class="value-cell">{{ item.value ?? item.data_value ?? '—' }}</td>
            <td><span class="status-tag" :class="'st-' + item.review_status">{{ item.review_status || 'pending' }}</span></td>
            <td>{{ item.recorded_at?.slice(0, 10) || item.created_at?.slice(0, 10) || '—' }}</td>
            <td class="action-cell">
              <button class="action-btn action-approve" @click="approve(item)">通过</button>
              <button class="action-btn action-reject" @click="reject(item)">异常</button>
              <button class="action-btn action-revise" @click="revise(item)">修订</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'

const loading = ref(true)
const items = ref<any[]>([])

async function load() {
  loading.value = true
  try {
    const res: any = await api.get('/api/v1/health-review/queue?reviewer_role=coach')
    items.value = res.items || (Array.isArray(res) ? res : [])
  } catch { items.value = [] }
  loading.value = false
}

async function doAction(item: any, action: string, data: any = {}) {
  try {
    await api.post(`/api/v1/health-review/${item.id}/${action}`, data)
    items.value = items.value.filter(i => i.id !== item.id)
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

function approve(item: any) { doAction(item, 'approve') }
function reject(item: any) { doAction(item, 'reject', { reason: '数据异常' }) }
function revise(item: any) {
  const note = prompt('修订备注') ?? ''
  doAction(item, 'revise', { note })
}

onMounted(load)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }
.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; color: #6b7280; font-weight: 500; border-bottom: 2px solid #f3f4f6; }
.data-table td { padding: 12px; color: #374151; border-bottom: 1px solid #f9fafb; }
.data-table tr:last-child td { border-bottom: none; }
.value-cell { font-weight: 600; color: #111827; }
.status-tag { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500; }
.st-pending { background: #fef3c7; color: #d97706; }
.st-approved { background: #d1fae5; color: #065f46; }
.st-rejected { background: #fee2e2; color: #dc2626; }
.action-cell { display: flex; gap: 6px; white-space: nowrap; }
.action-btn { padding: 4px 10px; border-radius: 6px; border: none; font-size: 12px; cursor: pointer; }
.action-approve { background: #d1fae5; color: #065f46; }
.action-reject { background: #fee2e2; color: #dc2626; }
.action-revise { background: #fef9c3; color: #92400e; }
.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
