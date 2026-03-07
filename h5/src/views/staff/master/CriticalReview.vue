<template>
  <div>
    <div class="page-header"><h2>危急病例审核</h2></div>
    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="items.length === 0" class="empty">暂无危急病例</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>患者/学员</th><th>数据类型</th><th>数值</th><th>严重程度</th><th>上报时间</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id" :class="{ 'row-critical': isCritical(item) }">
            <td>{{ item.user_name || item.student_name || '—' }}</td>
            <td>{{ item.data_type || item.type || '—' }}</td>
            <td class="value-cell">{{ item.value ?? item.data_value ?? '—' }}</td>
            <td><span class="severity-tag" :class="'sev-' + (item.severity || 'high')">{{ item.severity || '危急' }}</span></td>
            <td>{{ item.created_at?.slice(0, 16)?.replace('T', ' ') || '—' }}</td>
            <td class="action-cell">
              <button class="action-btn action-approve" @click="doAction(item, 'approve')">已处置</button>
              <button class="action-btn action-reject" @click="doAction(item, 'revise')">转介</button>
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

function isCritical(item: any) {
  return (item.severity || '').toLowerCase() === 'critical'
}

async function doAction(item: any, action: string) {
  const data: any = action === 'revise' ? { note: prompt('转介说明') ?? '' } : {}
  try {
    await api.post(`/api/v1/health-review/${item.id}/${action}`, data)
    items.value = items.value.filter(i => i.id !== item.id)
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

onMounted(async () => {
  try {
    const res: any = await api.get('/api/v1/health-review/queue?reviewer_role=master')
    items.value = res.items || (Array.isArray(res) ? res : [])
  } catch { items.value = [] }
  loading.value = false
})
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }
.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; color: #6b7280; font-weight: 500; border-bottom: 2px solid #f3f4f6; }
.data-table td { padding: 12px; color: #374151; border-bottom: 1px solid #f9fafb; }
.data-table tr:last-child td { border-bottom: none; }
.row-critical { background: #fff5f5; }
.value-cell { font-weight: 700; color: #dc2626; }
.severity-tag { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.sev-critical { background: #fee2e2; color: #dc2626; }
.sev-high { background: #ffedd5; color: #ea580c; }
.sev-medium { background: #fef9c3; color: #ca8a04; }
.action-cell { display: flex; gap: 6px; white-space: nowrap; }
.action-btn { padding: 5px 12px; border-radius: 6px; border: none; font-size: 12px; cursor: pointer; }
.action-approve { background: #d1fae5; color: #065f46; }
.action-reject { background: #ede9fe; color: #5b21b6; }
.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
