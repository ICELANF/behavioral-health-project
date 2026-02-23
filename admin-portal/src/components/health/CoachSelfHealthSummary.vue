<template>
  <div class="coach-health-summary">
    <div class="summary-header">
      <span class="summary-title">💚 我的健康</span>
      <a class="detail-link" @click="$router.push('/coach/workbench?tab=profile')">
        查看详细档案 →
      </a>
    </div>

    <!-- 4 指标迷你网格 -->
    <div class="metrics-grid" :class="{ compact: compact }">
      <div class="metric-card" v-for="m in metrics" :key="m.key">
        <div class="metric-icon">{{ m.icon }}</div>
        <div class="metric-body">
          <div class="metric-value">
            {{ m.loading ? '...' : (m.value ?? '--') }}
            <span class="metric-unit">{{ m.unit }}</span>
          </div>
          <div class="metric-label">{{ m.label }}</div>
        </div>
      </div>
    </div>

    <!-- 今日任务进度 -->
    <div class="task-progress" v-if="taskData.total > 0">
      <div class="progress-text">
        今日任务: 已完成 <b>{{ taskData.done }}</b> / {{ taskData.total }}
      </div>
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" :style="{ width: taskData.pct + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

defineProps<{ compact?: boolean }>()

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const token = localStorage.getItem('admin_token') || ''
const headers = { Authorization: `Bearer ${token}` }

const metrics = reactive([
  { key: 'glucose', icon: '🩸', label: '最近血糖', value: null as string | null, unit: 'mmol/L', loading: true },
  { key: 'sleep', icon: '😴', label: '昨晚睡眠', value: null as string | null, unit: '分', loading: true },
  { key: 'steps', icon: '🚶', label: '今日步数', value: null as string | null, unit: '步', loading: true },
  { key: 'weight', icon: '⚖️', label: '体重', value: null as string | null, unit: 'kg', loading: true },
])

const taskData = reactive({ done: 0, total: 0, pct: 0 })

async function loadHealthData() {
  try {
    const res = await fetch(`${API_BASE}/v1/health-data/summary`, { headers })
    if (res.ok) {
      const data = await res.json()
      // Map summary data to metric cards (field names from device_rest_api.py DashboardSummary)
      if (data.latest_glucose?.value != null) metrics[0].value = String(data.latest_glucose.value)
      if (data.sleep_score != null) metrics[1].value = String(data.sleep_score)
      if (data.steps_today != null) metrics[2].value = String(data.steps_today)
      if (data.latest_weight_kg != null) metrics[3].value = String(data.latest_weight_kg)
    }
  } catch { /* silent */ }
  metrics.forEach(m => m.loading = false)
}

async function loadTodayTasks() {
  try {
    const res = await fetch(`${API_BASE}/v1/daily-tasks/today`, { headers })
    if (res.ok) {
      const data = await res.json()
      taskData.done = data.done_count ?? 0
      taskData.total = data.total_count ?? 0
      taskData.pct = data.completion_pct ?? 0
    }
  } catch { /* silent */ }
}

onMounted(() => {
  if (token) {
    loadHealthData()
    loadTodayTasks()
  }
})
</script>

<style scoped>
.coach-health-summary {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 50%, #f0f9ff 100%);
  border: 1px solid #d1fae5;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
}

.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.summary-title {
  font-size: 15px;
  font-weight: 700;
  color: #065f46;
}
.detail-link {
  font-size: 12px;
  color: #059669;
  cursor: pointer;
}
.detail-link:hover { text-decoration: underline; }

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}
.metrics-grid.compact {
  grid-template-columns: repeat(2, 1fr);
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255,255,255,0.75);
  border-radius: 8px;
  padding: 10px 12px;
}
.metric-icon { font-size: 20px; flex-shrink: 0; }
.metric-value {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
}
.metric-unit {
  font-size: 11px;
  font-weight: 400;
  color: #6b7280;
}
.metric-label {
  font-size: 11px;
  color: #6b7280;
}

.task-progress { margin-top: 4px; }
.progress-text {
  font-size: 13px;
  color: #374151;
  margin-bottom: 6px;
}
.progress-bar-bg {
  height: 6px;
  background: #d1fae5;
  border-radius: 3px;
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  background: #059669;
  border-radius: 3px;
  transition: width 0.4s ease;
}

@media (max-width: 640px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
  .coach-health-summary { padding: 12px 14px; }
  .metric-value { font-size: 16px; }
}
</style>
