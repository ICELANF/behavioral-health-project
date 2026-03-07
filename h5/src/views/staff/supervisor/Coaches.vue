<template>
  <div>
    <div class="page-header"><h2>教练管理</h2></div>
    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="coaches.length === 0" class="empty">暂无教练数据</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>教练</th><th>阶段/等级</th><th>学员数</th><th>完成率</th><th>高危学员</th><th>加入时间</th></tr>
        </thead>
        <tbody>
          <tr v-for="c in coaches" :key="c.id">
            <td>
              <div class="coach-cell">
                <div class="c-avatar">{{ (c.name || c.full_name || '?')[0] }}</div>
                <div>
                  <div class="c-name">{{ c.name || c.full_name }}</div>
                  <div class="c-id">ID: {{ c.id }}</div>
                </div>
              </div>
            </td>
            <td>{{ c.stage || c.level || '—' }}</td>
            <td>{{ c.student_count ?? '—' }}</td>
            <td>
              <div class="pct-bar-wrap">
                <div class="pct-bar" :style="{ width: (c.completion_rate || 0) + '%' }"></div>
              </div>
              <span class="pct-label">{{ c.completion_rate || 0 }}%</span>
            </td>
            <td>
              <span v-if="(c.high_risk_count || 0) > 0" class="risk-badge">{{ c.high_risk_count }}</span>
              <span v-else class="risk-ok">—</span>
            </td>
            <td>{{ c.created_at?.slice(0, 10) || '—' }}</td>
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
const coaches = ref<any[]>([])

onMounted(async () => {
  try {
    const res: any = await api.get('/api/v1/supervisor/coaches')
    coaches.value = res.items || res.coaches || (Array.isArray(res) ? res : [])
  } catch { coaches.value = [] }
  loading.value = false
})
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }
.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; color: #6b7280; font-weight: 500; border-bottom: 2px solid #f3f4f6; }
.data-table td { padding: 12px; color: #374151; border-bottom: 1px solid #f9fafb; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.coach-cell { display: flex; align-items: center; gap: 10px; }
.c-avatar { width: 34px; height: 34px; border-radius: 50%; background: linear-gradient(135deg, #7c3aed, #3b82f6); color: #fff; font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.c-name { font-size: 13px; font-weight: 500; color: #111827; }
.c-id { font-size: 11px; color: #9ca3af; }
.pct-bar-wrap { width: 80px; background: #f3f4f6; border-radius: 3px; height: 6px; display: inline-block; margin-right: 6px; vertical-align: middle; }
.pct-bar { height: 100%; background: linear-gradient(90deg, #3b82f6, #10b981); border-radius: 3px; }
.pct-label { font-size: 12px; color: #374151; }
.risk-badge { background: #fee2e2; color: #dc2626; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 600; }
.risk-ok { color: #9ca3af; }
.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
