<template>
  <div class="my-assessments">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">← 返回</button>
      <h2>我的测评记录</h2>
    </div>

    <!-- Pending assessments -->
    <div v-if="pendingAssessments.length > 0" class="section">
      <h3 class="section-title">待完成测评</h3>
      <div v-for="item in pendingAssessments" :key="item.id" class="pending-card" @click="$router.push(`/client/assessment/take/${item.id}`)">
        <div class="pending-icon">📝</div>
        <div class="pending-info">
          <span class="pending-name">{{ item.name }}</span>
          <span class="pending-desc">{{ item.description }}</span>
        </div>
        <span class="pending-arrow">→</span>
      </div>
    </div>

    <!-- Score trend -->
    <div class="section">
      <h3 class="section-title">得分趋势</h3>
      <div class="trend-chart">
        <div class="chart-labels">
          <span v-for="n in 5" :key="n" class="chart-label">{{ (5 - n) * 25 }}</span>
        </div>
        <div class="chart-bars">
          <div v-for="(record, i) in completedAssessments.slice(-6)" :key="i" class="chart-bar-col">
            <div class="chart-bar" :style="{ height: (record.score / record.maxScore * 100) + '%', background: barColor(record.score, record.maxScore) }">
              <span class="bar-score">{{ record.score }}</span>
            </div>
            <span class="bar-label">{{ record.shortDate }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Completed assessments -->
    <div class="section">
      <h3 class="section-title">已完成测评</h3>
      <div v-for="item in completedAssessments" :key="item.id" class="completed-card" @click="$router.push(`/client/assessment/result/${item.id}`)">
        <div class="completed-left">
          <span class="completed-name">{{ item.name }}</span>
          <span class="completed-date">{{ item.date }}</span>
        </div>
        <div class="completed-right">
          <span class="completed-score" :style="{ color: barColor(item.score, item.maxScore) }">{{ item.score }}/{{ item.maxScore }}</span>
          <span class="completed-level" :class="item.levelClass">{{ item.level }}</span>
        </div>
      </div>
      <p v-if="completedAssessments.length === 0" class="empty-text">暂无已完成测评</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { assessmentApi } from '@/api/index'

const loading = ref(true)

const pendingAssessments = ref([])
const completedAssessments = ref([])

function scoreLevelClass(score, maxScore) {
  const pct = score / maxScore
  if (pct >= 0.7) return 'level-severe'
  if (pct >= 0.4) return 'level-moderate'
  if (pct >= 0.2) return 'level-mild'
  return 'level-normal'
}

async function loadAssessments() {
  if (!localStorage.getItem('admin_token')) return
  loading.value = true
  try {
    const assignments = await assessmentApi.getAssignments()
    if (Array.isArray(assignments) && assignments.length > 0) {
      // Separate pending vs completed
      const pending = []
      const completed = []
      for (const a of assignments) {
        if (a.status === 'completed' || a.completed_at) {
          const date = a.completed_at || a.date || ''
          const shortDate = date ? `${new Date(date).getMonth()+1}/${new Date(date).getDate()}` : ''
          completed.push({
            id: String(a.id), name: a.assessment_name || a.name || '',
            date, shortDate,
            score: a.score ?? 0, maxScore: a.max_score ?? 100,
            level: a.level || a.interpretation || '',
            levelClass: scoreLevelClass(a.score ?? 0, a.max_score ?? 100),
          })
        } else {
          pending.push({
            id: String(a.id),
            name: a.assessment_name || a.name || '',
            description: a.description || '',
          })
        }
      }
      pendingAssessments.value = pending
      completedAssessments.value = completed
    }
  } catch (e) {
    console.error('加载测评记录失败:', e)
  }
  loading.value = false
}

onMounted(loadAssessments)

const barColor = (score, max) => {
  const pct = score / max
  if (pct >= 0.7) return '#cf1322'
  if (pct >= 0.4) return '#d4b106'
  return '#389e0d'
}
</script>

<style scoped>
.my-assessments { max-width: 600px; margin: 0 auto; padding: 16px; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { flex: 1; margin: 0; font-size: 18px; }
.back-btn { padding: 6px 16px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; }

.section { margin-bottom: 20px; }
.section-title { font-size: 15px; font-weight: 600; color: #333; margin: 0 0 12px; }

.pending-card { display: flex; align-items: center; gap: 12px; padding: 14px; background: #fffbe6; border: 1px solid #ffe58f; border-radius: 8px; margin-bottom: 8px; cursor: pointer; }
.pending-card:hover { background: #fff7cc; }
.pending-icon { font-size: 24px; }
.pending-info { flex: 1; }
.pending-name { display: block; font-size: 14px; font-weight: 500; color: #333; }
.pending-desc { font-size: 12px; color: #999; }
.pending-arrow { font-size: 18px; color: #999; }

.trend-chart { display: flex; gap: 8px; padding: 16px; background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; height: 160px; }
.chart-labels { display: flex; flex-direction: column; justify-content: space-between; padding-right: 4px; }
.chart-label { font-size: 10px; color: #ccc; }
.chart-bars { flex: 1; display: flex; gap: 8px; align-items: flex-end; }
.chart-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.chart-bar { width: 100%; max-width: 36px; border-radius: 4px 4px 0 0; min-height: 4px; position: relative; transition: height 0.3s; }
.bar-score { position: absolute; top: -16px; left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: 600; color: #333; white-space: nowrap; }
.bar-label { font-size: 10px; color: #999; margin-top: 4px; }

.completed-card { display: flex; align-items: center; justify-content: space-between; padding: 12px; background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; margin-bottom: 6px; cursor: pointer; }
.completed-card:hover { background: #fafafa; }
.completed-left { display: flex; flex-direction: column; gap: 2px; }
.completed-name { font-size: 14px; font-weight: 500; color: #333; }
.completed-date { font-size: 12px; color: #999; }
.completed-right { display: flex; align-items: center; gap: 8px; }
.completed-score { font-size: 16px; font-weight: 600; }
.completed-level { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.level-normal { background: #f6ffed; color: #389e0d; }
.level-mild { background: #fffbe6; color: #d4b106; }
.level-moderate { background: #fff2e8; color: #d46b08; }
.level-severe { background: #fff1f0; color: #cf1322; }
.empty-text { text-align: center; color: #ccc; font-size: 13px; padding: 16px 0; }
</style>
