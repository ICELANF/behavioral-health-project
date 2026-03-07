<template>
  <div>
    <div class="kpi-grid">
      <div class="kpi-card" style="--accent:#7c3aed">
        <div class="kpi-icon">👥</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.coachCount }}</div>
          <div class="kpi-label">教练总数</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#2563eb">
        <div class="kpi-icon">🎓</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.studentCount }}</div>
          <div class="kpi-label">学员总数</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#dc2626">
        <div class="kpi-icon">🔍</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.pendingReview }}</div>
          <div class="kpi-label">待审核</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#059669">
        <div class="kpi-icon">📈</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.activeToday }}</div>
          <div class="kpi-label">今日活跃</div>
        </div>
      </div>
    </div>

    <div class="two-col">
      <!-- 教练列表 -->
      <div class="card">
        <div class="card-header">
          <h2>教练团队</h2>
          <router-link to="/staff/supervisor/coaches" class="view-all">查看全部 →</router-link>
        </div>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="coaches.length === 0" class="empty">暂无教练数据</div>
        <div v-else class="coach-rows">
          <div v-for="c in coaches.slice(0, 6)" :key="c.id" class="coach-row">
            <div class="c-avatar">{{ (c.name || c.full_name || '?')[0] }}</div>
            <div class="c-info">
              <div class="c-name">{{ c.name || c.full_name }}</div>
              <div class="c-meta">学员 {{ c.student_count || 0 }} 人 · 平均完成率 {{ c.completion_rate || 0 }}%</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 质量指标 -->
      <div class="card">
        <div class="card-header"><h2>服务质量</h2></div>
        <div class="quality-list">
          <div v-for="q in qualityMetrics" :key="q.label" class="quality-item">
            <div class="q-top">
              <span class="q-label">{{ q.label }}</span>
              <span class="q-val">{{ q.value }}%</span>
            </div>
            <div class="q-bar-wrap">
              <div class="q-bar" :style="{ width: q.value + '%', background: q.color }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'

const loading = ref(true)
const stats = ref({ coachCount: 0, studentCount: 0, pendingReview: 0, activeToday: 0 })
const coaches = ref<any[]>([])
const qualityMetrics = ref([
  { label: '学员满意度', value: 0, color: '#10b981' },
  { label: '任务完成率', value: 0, color: '#3b82f6' },
  { label: '数据上报率', value: 0, color: '#8b5cf6' },
  { label: '90天留存率', value: 0, color: '#f59e0b' },
])

onMounted(async () => {
  const [dashRes, hrRes] = await Promise.allSettled([
    api.get('/api/v1/supervisor/dashboard'),
    api.get('/api/v1/health-review/queue?reviewer_role=supervisor'),
  ])
  if (dashRes.status === 'fulfilled') {
    const d = dashRes.value as any
    stats.value = {
      coachCount: d.coach_count ?? d.total_coaches ?? 0,
      studentCount: d.student_count ?? d.total_students ?? 0,
      activeToday: d.active_today ?? d.active_users ?? 0,
      pendingReview: 0,
    }
    coaches.value = d.coaches || d.coach_list || []
    if (d.quality) {
      qualityMetrics.value[0].value = d.quality.satisfaction ?? 0
      qualityMetrics.value[1].value = d.quality.completion ?? 0
      qualityMetrics.value[2].value = d.quality.data_rate ?? 0
      qualityMetrics.value[3].value = d.quality.retention ?? 0
    }
  }
  if (hrRes.status === 'fulfilled') {
    const d = hrRes.value as any
    stats.value.pendingReview = d.total ?? (Array.isArray(d) ? d.length : (d.items?.length ?? 0))
  }
  loading.value = false
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
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-header h2 { font-size: 15px; font-weight: 600; margin: 0; }
.view-all { font-size: 13px; color: #3b82f6; text-decoration: none; }

.coach-rows { display: flex; flex-direction: column; gap: 10px; }
.coach-row { display: flex; align-items: center; gap: 12px; padding: 10px; background: #f9fafb; border-radius: 8px; }
.c-avatar { width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #7c3aed, #3b82f6); color: #fff; font-size: 14px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.c-name { font-size: 13px; font-weight: 500; color: #111827; }
.c-meta { font-size: 11px; color: #9ca3af; margin-top: 2px; }

.quality-list { display: flex; flex-direction: column; gap: 14px; }
.quality-item {}
.q-top { display: flex; justify-content: space-between; margin-bottom: 6px; }
.q-label { font-size: 13px; color: #374151; }
.q-val { font-size: 13px; font-weight: 600; color: #111827; }
.q-bar-wrap { background: #f3f4f6; border-radius: 4px; height: 8px; overflow: hidden; }
.q-bar { height: 100%; border-radius: 4px; transition: width 0.6s; }

.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 24px 0; }
</style>
