<template>
  <div>
    <div class="kpi-grid">
      <div class="kpi-card" style="--accent:#7c3aed">
        <div class="kpi-icon">👥</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.supervisorCount }}</div>
          <div class="kpi-label">督导总数</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#dc2626">
        <div class="kpi-icon">🚨</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.criticalCases }}</div>
          <div class="kpi-label">危急病例</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#f59e0b">
        <div class="kpi-icon">📚</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.pendingKnowledge }}</div>
          <div class="kpi-label">待审知识</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#059669">
        <div class="kpi-icon">⬆️</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.pendingPromotion }}</div>
          <div class="kpi-label">待终审晋级</div>
        </div>
      </div>
    </div>

    <div class="two-col">
      <div class="card">
        <div class="card-header">
          <h2>系统全貌</h2>
        </div>
        <div class="stat-list">
          <div v-for="s in systemStats" :key="s.label" class="stat-item">
            <span class="stat-icon">{{ s.icon }}</span>
            <span class="stat-label">{{ s.label }}</span>
            <span class="stat-val">{{ s.value }}</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>快速入口</h2>
        </div>
        <div class="quick-links">
          <router-link to="/staff/master/critical-review" class="ql-item ql-red">
            <span class="ql-icon">🚨</span>
            <span>危急病例审核</span>
          </router-link>
          <router-link to="/staff/master/knowledge" class="ql-item ql-amber">
            <span class="ql-icon">📚</span>
            <span>知识库管理</span>
          </router-link>
          <router-link to="/staff/master/promotion" class="ql-item ql-green">
            <span class="ql-icon">⬆️</span>
            <span>晋级终审</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'

const stats = ref({ supervisorCount: 0, criticalCases: 0, pendingKnowledge: 0, pendingPromotion: 0 })
const systemStats = ref<{ icon: string; label: string; value: string | number }[]>([
  { icon: '👤', label: '平台总用户', value: 0 },
  { icon: '📋', label: '已评估学员', value: 0 },
  { icon: '🤖', label: 'AI生成计划', value: 0 },
  { icon: '📚', label: '知识库条目', value: 0 },
])

onMounted(async () => {
  const [dashRes, hrRes] = await Promise.allSettled([
    api.get('/api/v1/master/dashboard'),
    api.get('/api/v1/health-review/queue?reviewer_role=master'),
  ])
  if (dashRes.status === 'fulfilled') {
    const d = dashRes.value as any
    stats.value.supervisorCount = d.supervisor_count ?? 0
    stats.value.pendingKnowledge = d.pending_knowledge ?? 0
    stats.value.pendingPromotion = d.pending_promotion ?? 0
    if (d.total_users) systemStats.value[0].value = d.total_users
    if (d.assessed_users) systemStats.value[1].value = d.assessed_users
    if (d.ai_plans) systemStats.value[2].value = d.ai_plans
    if (d.knowledge_items) systemStats.value[3].value = d.knowledge_items
  }
  if (hrRes.status === 'fulfilled') {
    const d = hrRes.value as any
    stats.value.criticalCases = d.total ?? (Array.isArray(d) ? d.length : (d.items?.length ?? 0))
  }
})
</script>

<style scoped>
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.kpi-card {
  background: #fff; border-radius: 12px; padding: 20px;
  display: flex; align-items: center; gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06); border-left: 4px solid var(--accent);
}
.kpi-icon { font-size: 28px; }
.kpi-num { font-size: 28px; font-weight: 800; color: var(--accent); line-height: 1; }
.kpi-label { font-size: 12px; color: #6b7280; margin-top: 4px; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.card-header { margin-bottom: 16px; }
.card-header h2 { font-size: 15px; font-weight: 600; margin: 0; }

.stat-list { display: flex; flex-direction: column; gap: 12px; }
.stat-item { display: flex; align-items: center; gap: 10px; padding: 10px; background: #f9fafb; border-radius: 8px; }
.stat-icon { font-size: 20px; }
.stat-label { flex: 1; font-size: 13px; color: #6b7280; }
.stat-val { font-size: 18px; font-weight: 700; color: #111827; }

.quick-links { display: flex; flex-direction: column; gap: 10px; }
.ql-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-radius: 10px;
  text-decoration: none; font-size: 14px; font-weight: 500;
  transition: opacity 0.15s;
}
.ql-item:hover { opacity: 0.85; }
.ql-red { background: #fee2e2; color: #dc2626; }
.ql-amber { background: #fef9c3; color: #92400e; }
.ql-green { background: #dcfce7; color: #166534; }
.ql-icon { font-size: 20px; }
</style>
