<template>
  <div>
    <div class="page-header"><h2>晋级终审（L3）</h2></div>
    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="items.length === 0" class="empty">暂无待终审晋级申请</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>申请人</th><th>当前等级</th><th>目标等级</th><th>L1教练</th><th>L2督导</th><th>时间</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.user_name || item.applicant_name || '—' }}</td>
            <td>{{ item.current_level || item.from_level || '—' }}</td>
            <td>{{ item.target_level || item.to_level || '—' }}</td>
            <td>{{ item.l1_reviewer || item.coach_name || '—' }}</td>
            <td>{{ item.l2_reviewer || item.supervisor_name || '—' }}</td>
            <td>{{ item.created_at?.slice(0, 10) || '—' }}</td>
            <td class="action-cell">
              <button class="action-btn action-approve" @click="approve(item)">终审通过</button>
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
    const res: any = await api.get('/api/v1/promotion/applications?stage=L3')
    items.value = res.items || (Array.isArray(res) ? res : [])
  } catch { items.value = [] }
  loading.value = false
}

async function approve(item: any) {
  try {
    await api.post(`/api/v1/promotion/applications/${item.id}/approve`)
    item.status = 'final_approved'
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

async function reject(item: any) {
  const reason = prompt('驳回原因') ?? ''
  try {
    await api.post(`/api/v1/promotion/applications/${item.id}/reject`, { reason })
    item.status = 'rejected'
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
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
.action-cell { display: flex; gap: 6px; }
.action-btn { padding: 5px 12px; border-radius: 6px; border: none; font-size: 12px; cursor: pointer; }
.action-approve { background: #d1fae5; color: #065f46; }
.action-approve:hover { background: #a7f3d0; }
.action-reject { background: #fee2e2; color: #dc2626; }
.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
