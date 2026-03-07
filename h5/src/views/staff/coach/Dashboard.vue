<template>
  <div>
    <!-- KPI 卡 -->
    <div class="kpi-grid">
      <div class="kpi-card" style="--accent:#7c3aed">
        <div class="kpi-icon">📋</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.pendingAssessments }}</div>
          <div class="kpi-label">待审评估</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#2563eb">
        <div class="kpi-icon">🔄</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.pendingAiPlans }}</div>
          <div class="kpi-label">待审AI计划</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#dc2626">
        <div class="kpi-icon">❤️</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.pendingHealthReview }}</div>
          <div class="kpi-label">待审健康数据</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#059669">
        <div class="kpi-icon">📤</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.pendingPush }}</div>
          <div class="kpi-label">待审处方</div>
        </div>
      </div>
    </div>

    <div class="two-col">
      <!-- 学员风险列表 -->
      <div class="card">
        <div class="card-header">
          <h2>学员风险一览</h2>
          <router-link to="/staff/coach/students" class="view-all">查看全部 →</router-link>
        </div>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="students.length === 0" class="empty">暂无学员数据</div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th>阶段</th>
              <th>风险</th>
              <th>7日微行动</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in students.slice(0, 8)" :key="s.id">
              <td>{{ s.name }}</td>
              <td><span class="stage-tag">{{ s.stage_label || s.stage }}</span></td>
              <td><span class="risk-tag" :class="riskClass(s.risk_level)">{{ s.risk_level }}</span></td>
              <td>{{ s.micro_action_7d ?? '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 今日待办 -->
      <div class="card">
        <div class="card-header">
          <h2>今日要点</h2>
        </div>
        <div class="todo-list">
          <div v-for="item in todayTodos" :key="item.id" class="todo-item">
            <span class="todo-dot" :style="{ background: item.color }"></span>
            <div class="todo-content">
              <div class="todo-title">{{ item.title }}</div>
              <div class="todo-sub">{{ item.sub }}</div>
            </div>
            <router-link :to="item.link" class="todo-link">→</router-link>
          </div>
          <div v-if="todayTodos.length === 0" class="empty">今日暂无待办</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '@/api/index'

const loading = ref(true)
const stats = ref({ pendingAssessments: 0, pendingAiPlans: 0, pendingHealthReview: 0, pendingPush: 0, studentCount: 0 })
const students = ref<any[]>([])

function riskClass(risk: any) {
  const n = parseInt(String(risk ?? '0').replace(/\D/g, '') || '0')
  if (n >= 4) return 'risk-r4'
  if (n === 3) return 'risk-r3'
  if (n === 2) return 'risk-r2'
  return 'risk-r1'
}

const todayTodos = computed(() => {
  const list = []
  if (stats.value.pendingAssessments > 0) list.push({ id: 'ass', title: `${stats.value.pendingAssessments} 份评估待审核`, sub: '点击前往评估管理', link: '/staff/coach/assessment', color: '#7c3aed' })
  if (stats.value.pendingAiPlans > 0) list.push({ id: 'ai', title: `${stats.value.pendingAiPlans} 个AI计划待审核`, sub: '点击前往AI飞轮', link: '/staff/coach/flywheel', color: '#2563eb' })
  if (stats.value.pendingHealthReview > 0) list.push({ id: 'hr', title: `${stats.value.pendingHealthReview} 条健康数据待审核`, sub: '点击前往健康审核', link: '/staff/coach/health-review', color: '#dc2626' })
  if (stats.value.pendingPush > 0) list.push({ id: 'push', title: `${stats.value.pendingPush} 个处方待审批`, sub: '点击前往推送审批', link: '/staff/coach/push-queue', color: '#059669' })
  return list
})

onMounted(async () => {
  const [dashRes, assRes, aiRes, hrRes, pushRes] = await Promise.allSettled([
    api.get('/api/v1/coach/dashboard'),
    api.get('/api/v1/assessment-assignments/coach-list?status=completed'),
    api.get('/api/v1/coach/review-queue?status=pending'),
    api.get('/api/v1/health-review/queue?reviewer_role=coach'),
    api.get('/api/v1/coach/push-queue?status=pending'),
  ])
  if (dashRes.status === 'fulfilled') {
    const d = dashRes.value as any
    students.value = d.students || []
    stats.value.studentCount = students.value.length
  }
  if (assRes.status === 'fulfilled') {
    const d = assRes.value as any
    stats.value.pendingAssessments = d.total ?? (d.items?.length ?? 0)
  }
  if (aiRes.status === 'fulfilled') {
    const d = aiRes.value as any
    stats.value.pendingAiPlans = d.total_pending ?? d.total ?? (Array.isArray(d) ? d.length : 0)
  }
  if (hrRes.status === 'fulfilled') {
    const d = hrRes.value as any
    stats.value.pendingHealthReview = d.total ?? (Array.isArray(d) ? d.length : (d.items?.length ?? 0))
  }
  if (pushRes.status === 'fulfilled') {
    const d = pushRes.value as any
    stats.value.pendingPush = d.total ?? (Array.isArray(d) ? d.length : (d.items?.length ?? 0))
  }
  loading.value = false
})
</script>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border-left: 4px solid var(--accent);
}

.kpi-icon { font-size: 28px; }
.kpi-num { font-size: 28px; font-weight: 800; color: var(--accent); line-height: 1; }
.kpi-label { font-size: 12px; color: #6b7280; margin-top: 4px; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-header h2 { font-size: 15px; font-weight: 600; color: #111827; margin: 0; }
.view-all { font-size: 13px; color: #3b82f6; text-decoration: none; }
.view-all:hover { text-decoration: underline; }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 8px 10px; color: #6b7280; font-weight: 500; border-bottom: 1px solid #f3f4f6; }
.data-table td { padding: 10px; color: #374151; border-bottom: 1px solid #f9fafb; }
.data-table tr:last-child td { border-bottom: none; }

.stage-tag { background: #eff6ff; color: #1d4ed8; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.risk-tag { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.risk-r4 { background: #fee2e2; color: #dc2626; }
.risk-r3 { background: #ffedd5; color: #ea580c; }
.risk-r2 { background: #fef9c3; color: #ca8a04; }
.risk-r1 { background: #dcfce7; color: #16a34a; }

.todo-list { display: flex; flex-direction: column; gap: 12px; }
.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
}
.todo-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.todo-content { flex: 1; }
.todo-title { font-size: 13px; font-weight: 500; color: #111827; }
.todo-sub { font-size: 11px; color: #9ca3af; margin-top: 2px; }
.todo-link { color: #3b82f6; font-size: 16px; text-decoration: none; padding: 4px 8px; }

.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 24px 0; }
</style>
