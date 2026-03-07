<template>
  <div>
    <div class="page-header">
      <h2>风险管理</h2>
    </div>

    <!-- 风险分层卡 -->
    <div class="risk-kpi">
      <div v-for="tier in riskTiers" :key="tier.level" class="risk-tier-card" :style="{ '--color': tier.color, '--bg': tier.bg }">
        <div class="tier-label">{{ tier.label }}</div>
        <div class="tier-count">{{ tier.students.length }}</div>
        <div class="tier-desc">{{ tier.level }}</div>
      </div>
    </div>

    <!-- 按风险分组 -->
    <div v-for="tier in riskTiers.filter(t => t.students.length > 0)" :key="tier.level" class="risk-section">
      <div class="risk-section-header" :style="{ borderLeftColor: tier.color }">
        <span class="risk-label-dot" :style="{ background: tier.color }"></span>
        {{ tier.label }} — {{ tier.students.length }} 人
      </div>
      <div class="card">
        <table class="data-table">
          <thead>
            <tr><th>姓名</th><th>阶段</th><th>7日微行动</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in tier.students" :key="s.id">
              <td>{{ s.name || s.full_name }}</td>
              <td><span class="stage-tag">{{ s.stage_label || s.stage }}</span></td>
              <td>{{ s.micro_action_7d ?? '-' }}</td>
              <td>
                <router-link :to="'/staff/coach/students'" class="link-btn">查看详情</router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="allStudents.length === 0" class="empty">暂无学员数据</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/index'

const loading = ref(true)
const allStudents = ref<any[]>([])

function riskNum(s: any) {
  return parseInt(String(s.risk_level ?? '0').replace(/\D/g, '') || '0')
}

const riskTiers = computed(() => [
  { level: 'R4', label: '🔴 高危', color: '#dc2626', bg: '#fee2e2', students: allStudents.value.filter(s => riskNum(s) >= 4) },
  { level: 'R3', label: '🟠 中高危', color: '#ea580c', bg: '#ffedd5', students: allStudents.value.filter(s => riskNum(s) === 3) },
  { level: 'R2', label: '🟡 中危', color: '#ca8a04', bg: '#fef9c3', students: allStudents.value.filter(s => riskNum(s) === 2) },
  { level: 'R1', label: '🟢 低危', color: '#16a34a', bg: '#dcfce7', students: allStudents.value.filter(s => riskNum(s) <= 1) },
])

onMounted(async () => {
  try {
    const res: any = await api.get('/api/v1/coach/dashboard')
    allStudents.value = res.students || []
  } catch { allStudents.value = [] }
  loading.value = false
})
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }

.risk-kpi { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.risk-tier-card {
  background: var(--bg);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  border: 1px solid var(--color, #e5e7eb);
}
.tier-label { font-size: 14px; font-weight: 600; color: var(--color); margin-bottom: 8px; }
.tier-count { font-size: 36px; font-weight: 800; color: var(--color); line-height: 1; }
.tier-desc { font-size: 12px; color: #6b7280; margin-top: 4px; }

.risk-section { margin-bottom: 16px; }
.risk-section-header {
  display: flex; align-items: center; gap: 8px;
  font-size: 14px; font-weight: 600; color: #374151;
  margin-bottom: 8px;
  padding-left: 12px;
  border-left: 3px solid #e5e7eb;
}
.risk-label-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

.card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 8px 12px; color: #6b7280; font-weight: 500; border-bottom: 1px solid #f3f4f6; }
.data-table td { padding: 10px 12px; color: #374151; border-bottom: 1px solid #f9fafb; }
.data-table tr:last-child td { border-bottom: none; }
.stage-tag { background: #eff6ff; color: #1d4ed8; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.link-btn { color: #3b82f6; font-size: 12px; text-decoration: none; }
.link-btn:hover { text-decoration: underline; }

.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
