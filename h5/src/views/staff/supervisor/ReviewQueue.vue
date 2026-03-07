<template>
  <div>
    <div class="page-header"><h2>审核队列</h2></div>
    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="items.length === 0" class="empty">暂无待审数据</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>学员</th><th>数据类型</th><th>数值</th><th>上报教练</th><th>时间</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.user_name || item.student_name || '—' }}</td>
            <td>{{ item.data_type || item.type || '—' }}</td>
            <td class="value-cell">{{ item.value ?? item.data_value ?? '—' }}</td>
            <td>{{ item.coach_name || '—' }}</td>
            <td>{{ item.created_at?.slice(0, 10) || '—' }}</td>
            <td class="action-cell">
              <button class="action-btn action-approve" @click="doAction(item, 'approve')">通过</button>
              <button class="action-btn action-reject" @click="doAction(item, 'reject')">异常</button>
              <button class="action-btn action-revise" @click="doAction(item, 'revise')">修订</button>
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

async function doAction(item: any, action: string) {
  let data: any = {}
  if (action === 'reject') data.reason = '数据异常'
  if (action === 'revise') data.note = prompt('修订备注') ?? ''
  try {
    await api.post(`/api/v1/health-review/${item.id}/${action}`, data)
    items.value = items.value.filter(i => i.id !== item.id)
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

onMounted(async () => {
  try {
    const res: any = await api.get('/api/v1/health-review/queue?reviewer_role=supervisor')
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
.value-cell { font-weight: 600; }
.action-cell { display: flex; gap: 6px; white-space: nowrap; }
.action-btn { padding: 4px 10px; border-radius: 6px; border: none; font-size: 12px; cursor: pointer; }
.action-approve { background: #d1fae5; color: #065f46; }
.action-reject { background: #fee2e2; color: #dc2626; }
.action-revise { background: #fef9c3; color: #92400e; }
.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
