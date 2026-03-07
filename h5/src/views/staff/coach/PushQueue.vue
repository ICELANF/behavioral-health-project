<template>
  <div>
    <div class="page-header">
      <h2>推送审批</h2>
      <span class="badge-count">{{ items.length }} 待审</span>
    </div>
    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="items.length === 0" class="empty">暂无待审处方</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>学员</th><th>类型</th><th>内容摘要</th><th>时间</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.student_name || item.user_name || '—' }}</td>
            <td><span class="type-tag">{{ item.push_type || item.type || '—' }}</span></td>
            <td class="summary-cell">{{ (item.content || item.summary || '—').slice(0, 60) }}</td>
            <td>{{ item.created_at?.slice(0, 10) || '—' }}</td>
            <td class="action-cell">
              <button class="action-btn action-approve" @click="approve(item)">通过</button>
              <button class="action-btn action-reject" @click="reject(item)">驳回</button>
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
    const res: any = await api.get('/api/v1/coach/push-queue?status=pending')
    items.value = res.items || (Array.isArray(res) ? res : [])
  } catch { items.value = [] }
  loading.value = false
}

async function approve(item: any) {
  try {
    await api.post(`/api/v1/coach/push-queue/${item.id}/approve`)
    items.value = items.value.filter(i => i.id !== item.id)
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

async function reject(item: any) {
  const reason = prompt('驳回原因（可选）') ?? ''
  try {
    await api.post(`/api/v1/coach/push-queue/${item.id}/reject`, { reason })
    items.value = items.value.filter(i => i.id !== item.id)
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }
.badge-count { background: #ef4444; color: #fff; border-radius: 12px; font-size: 12px; font-weight: 600; padding: 2px 10px; }

.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; color: #6b7280; font-weight: 500; border-bottom: 2px solid #f3f4f6; }
.data-table td { padding: 12px; color: #374151; border-bottom: 1px solid #f9fafb; }
.data-table tr:last-child td { border-bottom: none; }
.type-tag { background: #ede9fe; color: #5b21b6; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.summary-cell { max-width: 320px; color: #6b7280; }
.action-cell { display: flex; gap: 6px; white-space: nowrap; }
.action-btn { padding: 5px 12px; border-radius: 6px; border: none; font-size: 12px; cursor: pointer; }
.action-approve { background: #d1fae5; color: #065f46; }
.action-approve:hover { background: #a7f3d0; }
.action-reject { background: #fee2e2; color: #dc2626; }
.action-reject:hover { background: #fecaca; }
.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
