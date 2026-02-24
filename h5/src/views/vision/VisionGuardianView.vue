<template>
  <div class="vision-guardian">
    <van-nav-bar title="孩子视力报告" left-arrow @click-left="$router.back()" />

    <!-- 孩子选择器 -->
    <div class="student-selector" v-if="students.length > 0">
      <van-tabs v-model:active="activeStudentIdx" @change="onStudentChange" shrink>
        <van-tab v-for="(s, i) in students" :key="s.student_id" :title="s.student_name" :name="i" />
      </van-tabs>
    </div>
    <van-empty v-else-if="!loading" description="暂无监护的孩子" />

    <template v-if="currentStudent">
      <!-- 风险卡片 -->
      <div class="risk-card" :class="`risk-${currentStudent.risk_level}`">
        <div class="risk-header">
          <span class="risk-label">当前风险等级</span>
          <van-tag :type="riskTagType" size="large">{{ riskText }}</van-tag>
        </div>
        <div class="risk-stage">TTM 阶段: {{ stageText(currentStudent.ttm_stage) }}</div>
      </div>

      <!-- 仪表盘数据 -->
      <template v-if="dashboard">
        <div class="stat-row">
          <div class="stat-item">
            <div class="stat-value">{{ dashboard.streak_days }}</div>
            <div class="stat-label">连续打卡</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ dashboard.today?.score ?? '-' }}</div>
            <div class="stat-label">今日评分</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ avgScore }}</div>
            <div class="stat-label">周均评分</div>
          </div>
        </div>

        <!-- 周趋势图 -->
        <div class="trend-section">
          <div class="section-title">近 7 天评分趋势</div>
          <div class="trend-chart">
            <svg viewBox="0 0 350 120" class="chart-svg">
              <line x1="25" y1="100" x2="340" y2="100" stroke="#eee" stroke-width="1" />
              <line x1="25" y1="50" x2="340" y2="50" stroke="#eee" stroke-width="1" stroke-dasharray="4" />
              <polyline
                v-if="chartPoints.length > 1"
                :points="chartPointsStr"
                fill="none"
                stroke="#1890ff"
                stroke-width="2"
                stroke-linejoin="round"
              />
              <circle
                v-for="(p, i) in chartPoints" :key="i"
                :cx="p.x" :cy="p.y" r="4"
                fill="#1890ff"
              />
              <text
                v-for="(p, i) in chartPoints" :key="'t' + i"
                :x="p.x" :y="115"
                text-anchor="middle" font-size="10" fill="#999"
              >{{ p.label }}</text>
            </svg>
          </div>
        </div>

        <!-- 行动建议 -->
        <div class="advice-section">
          <div class="section-title">行动建议</div>
          <div class="advice-list">
            <div v-for="(a, i) in adviceList" :key="i" class="advice-item">
              <van-icon name="point" :color="a.color" />
              <span>{{ a.text }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- 查看详细日志 -->
      <div class="action-area">
        <van-button plain type="primary" block @click="viewLogs">查看详细行为日志</van-button>
      </div>
    </template>

    <van-loading v-if="loading" class="page-loading" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { visionApi } from '@/api/vision'

const router = useRouter()
const loading = ref(true)
const students = ref<any[]>([])
const activeStudentIdx = ref(0)
const dashboard = ref<any>(null)

const currentStudent = computed(() => students.value[activeStudentIdx.value] || null)

const riskTagType = computed(() => {
  const r = currentStudent.value?.risk_level
  if (r === 'urgent') return 'danger'
  if (r === 'alert') return 'warning'
  if (r === 'watch') return 'primary'
  return 'success'
})

const riskText = computed(() => {
  const map: Record<string, string> = { normal: '正常', watch: '关注', alert: '警惕', urgent: '紧急' }
  return map[currentStudent.value?.risk_level] || '正常'
})

function stageText(s: string) {
  const map: Record<string, string> = { S0: '前意向', S1: '意向', S2: '准备', S3: '行动', S4: '维持' }
  return map[s] || s || '-'
}

const avgScore = computed(() => {
  const scores = dashboard.value?.week_scores || []
  if (!scores.length) return '-'
  const sum = scores.reduce((a: number, s: any) => a + (s.score || 0), 0)
  return Math.round(sum / scores.length)
})

const chartPoints = computed(() => {
  const scores = dashboard.value?.week_scores || []
  if (!scores.length) return []
  const maxScore = Math.max(...scores.map((s: any) => s.score || 0)) || 1
  return scores.map((s: any, i: number) => ({
    x: 40 + i * (300 / Math.max(scores.length - 1, 1)),
    y: 95 - ((s.score || 0) / maxScore) * 80,
    label: s.date?.slice(5) || '',
  }))
})

const chartPointsStr = computed(() =>
  chartPoints.value.map((p: any) => `${p.x},${p.y}`).join(' ')
)

const adviceList = computed(() => {
  const advice: { text: string; color: string }[] = []
  const d = dashboard.value
  if (!d) return advice
  const risk = currentStudent.value?.risk_level || 'normal'
  if (risk === 'urgent' || risk === 'alert') {
    advice.push({ text: '建议尽快预约眼科检查', color: '#ff4d4f' })
  }
  if (d.today && !d.today.logged) {
    advice.push({ text: '今天还没打卡，提醒孩子记录', color: '#fa8c16' })
  }
  if (d.goals) {
    const lastLog = d.week_scores?.[d.week_scores.length - 1]
    if (lastLog && lastLog.score < 50) {
      advice.push({ text: '最近评分偏低，关注用眼习惯', color: '#fa8c16' })
    }
  }
  if (d.streak_days >= 7) {
    advice.push({ text: `连续打卡 ${d.streak_days} 天，表扬孩子的坚持！`, color: '#52c41a' })
  }
  if (!advice.length) {
    advice.push({ text: '数据正常，继续保持', color: '#52c41a' })
  }
  return advice
})

async function loadStudents() {
  try {
    const res: any = await visionApi.getMyStudents()
    students.value = res?.students || []
    if (students.value.length > 0) {
      await loadDashboard(students.value[0].student_id)
    }
  } catch { /* ignore */ }
  loading.value = false
}

async function loadDashboard(studentId: number) {
  try {
    dashboard.value = await visionApi.getDashboard(studentId)
  } catch {
    dashboard.value = null
  }
}

function onStudentChange(idx: number) {
  const s = students.value[idx]
  if (s) loadDashboard(s.student_id)
}

function viewLogs() {
  // Navigate to daily log or use router
  if (currentStudent.value) {
    router.push('/vision/daily')
  }
}

onMounted(loadStudents)
</script>

<style scoped>
.vision-guardian {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 60px;
}
.student-selector {
  background: #fff;
  padding: 0 16px;
}
.risk-card {
  margin: 16px;
  padding: 16px;
  border-radius: 12px;
  background: #fff;
}
.risk-normal { border-left: 4px solid #52c41a; }
.risk-watch { border-left: 4px solid #1890ff; }
.risk-alert { border-left: 4px solid #fa8c16; }
.risk-urgent { border-left: 4px solid #ff4d4f; }
.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.risk-label { font-size: 14px; color: #666; }
.risk-stage { font-size: 13px; color: #999; margin-top: 8px; }
.stat-row {
  display: flex;
  justify-content: space-around;
  padding: 16px;
  background: #fff;
  margin: 0 16px;
  border-radius: 12px;
}
.stat-item { text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; color: #333; }
.stat-label { font-size: 12px; color: #999; margin-top: 4px; }
.trend-section, .advice-section {
  margin: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
}
.section-title {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 12px;
}
.trend-chart { overflow-x: auto; }
.chart-svg { width: 100%; min-width: 300px; }
.advice-list { display: flex; flex-direction: column; gap: 8px; }
.advice-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #333;
}
.action-area { padding: 16px; }
.page-loading {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}
</style>
