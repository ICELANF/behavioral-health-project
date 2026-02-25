<!-- ═══════════════════════════════════════════════════════════ -->
<!-- CoachDashboard.vue — 教练首页（Admin Portal :5174）        -->
<!-- 核心：风险优先级自动排序 + AI 副驾驶入口                    -->
<!-- 文件路径: admin-portal/src/views/coach-portal/main.vue     -->
<!-- ═══════════════════════════════════════════════════════════ -->
<template>
  <div class="coach-dashboard">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">教练工作台</h1>
        <p class="page-date">{{ today }}</p>
      </div>
      <div class="header-right">
        <a-badge :count="urgentCount" :offset="[-2, 2]">
          <a-button type="primary" @click="router.push('/rx/dashboard')">
            <template #icon><ThunderboltOutlined /></template>
            AI 副驾驶
          </a-button>
        </a-badge>
      </div>
    </div>

    <!-- KPI 看板 -->
    <a-row :gutter="[16, 16]" class="kpi-row">
      <a-col :xs="12" :sm="6" v-for="kpi in kpiCards" :key="kpi.label">
        <div class="kpi-card" :class="`kpi-card--${kpi.color}`">
          <div class="kpi-icon">{{ kpi.icon }}</div>
          <div class="kpi-val">{{ kpi.value }}</div>
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-trend" v-if="kpi.trend">
            <span :class="kpi.trend > 0 ? 'trend-up' : 'trend-dn'">
              {{ kpi.trend > 0 ? '↑' : '↓' }} {{ Math.abs(kpi.trend) }}%
            </span>
          </div>
        </div>
      </a-col>
    </a-row>

    <!-- 高风险学员列表（自动排序） -->
    <div class="risk-section">
      <div class="section-header">
        <h3 class="sec-title">
          <span class="alert-dot" />
          需要优先关注
        </h3>
        <a-button size="small" @click="router.push('/coach/my/students')">
          查看全部学员
        </a-button>
      </div>

      <div v-if="urgentStudents.length === 0" class="empty-tip">
        <CheckCircleOutlined style="color:#4CAF50; font-size:28px" />
        <p>今日无高风险学员，保持观察</p>
      </div>

      <div class="risk-list" v-else>
        <div
          v-for="student in urgentStudents"
          :key="student.id"
          class="risk-item"
          :class="`risk-item--${student.risk_level}`"
          @click="viewStudent(student.id)"
        >
          <a-avatar :src="student.avatar" :size="40" class="student-avatar">
            {{ student.name?.[0] }}
          </a-avatar>
          <div class="risk-info">
            <div class="risk-name">{{ student.name }}</div>
            <div class="risk-reason">{{ student.risk_reason }}</div>
          </div>
          <div class="risk-score">
            <div class="trust-score-bar">
              <div
                class="trust-fill"
                :style="{ width: student.trust_score + '%' }"
                :class="`fill--${getTrustLevel(student.trust_score)}`"
              />
            </div>
            <span class="score-num">信任分 {{ student.trust_score }}</span>
          </div>
          <a-tag :color="riskColor(student.risk_level)" class="risk-tag">
            {{ student.risk_level_label }}
          </a-tag>
        </div>
      </div>
    </div>

    <!-- 待处理事项 -->
    <a-row :gutter="16" class="pending-row">
      <a-col :span="12">
        <div class="pending-card" @click="router.push('/rx/dashboard')">
          <div class="pending-icon pending-icon--rx">📋</div>
          <div class="pending-body">
            <div class="pending-num">{{ pendingReviews }}</div>
            <div class="pending-label">AI建议待审核</div>
          </div>
          <RightOutlined class="pending-arrow" />
        </div>
      </a-col>
      <a-col :span="12">
        <div class="pending-card" @click="router.push('/rx/history')">
          <div class="pending-icon pending-icon--approve">✅</div>
          <div class="pending-body">
            <div class="pending-num">{{ pendingPrescriptions }}</div>
            <div class="pending-label">处方待审批</div>
          </div>
          <RightOutlined class="pending-arrow" />
        </div>
      </a-col>
    </a-row>

    <!-- 本月KPI -->
    <div class="monthly-kpi-card">
      <div class="mk-header">
        <h4 class="mk-title">本月执行质量</h4>
        <span class="mk-period">{{ currentMonth }}</span>
      </div>
      <a-row :gutter="16">
        <a-col :span="8" v-for="m in monthlyMetrics" :key="m.label">
          <div class="mk-metric">
            <a-progress
              type="circle"
              :percent="m.percent"
              :size="64"
              :stroke-color="m.color"
            />
            <p class="mk-label">{{ m.label }}</p>
          </div>
        </a-col>
      </a-row>
    </div>

    <!-- 督导会议提醒 -->
    <div class="supervision-card" v-if="nextMeeting">
      <div class="sv-icon">📅</div>
      <div class="sv-body">
        <p class="sv-label">下次督导会议</p>
        <p class="sv-time">{{ nextMeeting }}</p>
      </div>
      <a-button size="small" @click="router.push('/expert/my/supervision')">
        查看详情
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ThunderboltOutlined, CheckCircleOutlined, RightOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const today = new Date().toLocaleDateString('zh-CN', { weekday: 'long', month: 'long', day: 'numeric' })
const currentMonth = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })

const urgentStudents = ref<any[]>([])
const pendingReviews = ref(0)
const pendingPrescriptions = ref(0)
const nextMeeting = ref<string | null>(null)

const urgentCount = computed(() =>
  urgentStudents.value.filter(s => s.risk_level === 'high').length
)

const kpiCards = ref([
  { label: '活跃学员', value: '--', icon: '👥', color: 'blue', trend: null },
  { label: '本月完成率', value: '--', icon: '📊', color: 'green', trend: null },
  { label: '高风险人数', value: '--', icon: '⚠️', color: 'red', trend: null },
  { label: '处方通过率', value: '--', icon: '✅', color: 'purple', trend: null },
])

const monthlyMetrics = ref([
  { label: '出勤率', percent: 0, color: '#1565C0' },
  { label: '任务完成', percent: 0, color: '#4CAF50' },
  { label: '处方执行', percent: 0, color: '#FF9800' },
])

const getTrustLevel = (score: number) => {
  if (score >= 70) return 'high'
  if (score >= 40) return 'mid'
  return 'low'
}
const riskColor = (level: string) => ({
  high: 'red', medium: 'orange', low: 'green'
}[level] || 'default')

const viewStudent = (id: string) => router.push(`/coach/student-health?id=${id}`)

onMounted(async () => {
  try {
    const res = await fetch('/api/v1/coach/home-dashboard').then(r => r.json())
    const d = res.data || {}
    urgentStudents.value = d.urgent_students || []
    pendingReviews.value = d.pending_ai_reviews || 0
    pendingPrescriptions.value = d.pending_prescriptions || 0
    nextMeeting.value = d.next_supervision_meeting || null
    if (d.kpi) {
      kpiCards.value[0].value = d.kpi.active_students
      kpiCards.value[1].value = d.kpi.completion_rate + '%'
      kpiCards.value[2].value = d.kpi.high_risk_count
      kpiCards.value[3].value = d.kpi.rx_approval_rate + '%'
    }
    if (d.monthly_metrics) {
      monthlyMetrics.value[0].percent = d.monthly_metrics.attendance_rate
      monthlyMetrics.value[1].percent = d.monthly_metrics.task_completion
      monthlyMetrics.value[2].percent = d.monthly_metrics.rx_execution
    }
  } catch {}
})
</script>

<style scoped>
.coach-dashboard { padding: 24px; max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 700; margin: 0; color: #1A237E; }
.page-date { font-size: 13px; color: #888; margin: 4px 0 0; }
.kpi-row { margin-bottom: 24px; }
.kpi-card {
  background: #fff; border-radius: 16px; padding: 20px 16px;
  display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06); cursor: pointer;
  transition: transform 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-card--blue { border-top: 3px solid #1565C0; }
.kpi-card--green { border-top: 3px solid #4CAF50; }
.kpi-card--red { border-top: 3px solid #F44336; }
.kpi-card--purple { border-top: 3px solid #7B1FA2; }
.kpi-icon { font-size: 28px; margin-bottom: 8px; }
.kpi-val { font-size: 28px; font-weight: 800; color: #222; }
.kpi-label { font-size: 12px; color: #888; margin-top: 4px; }
.kpi-trend { margin-top: 4px; font-size: 12px; }
.trend-up { color: #4CAF50; }
.trend-dn { color: #F44336; }
.risk-section { background: #fff; border-radius: 16px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.sec-title { font-size: 16px; font-weight: 700; color: #222; margin: 0; display: flex; align-items: center; gap: 8px; }
.alert-dot { width: 8px; height: 8px; background: #F44336; border-radius: 50%; animation: blink 1.5s ease infinite; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
.empty-tip { display: flex; flex-direction: column; align-items: center; padding: 24px; color: #888; gap: 8px; }
.risk-list { display: flex; flex-direction: column; gap: 12px; }
.risk-item {
  display: flex; align-items: center; gap: 14px;
  padding: 14px; border-radius: 12px; background: #FAFAFA;
  border: 1px solid #F0F0F0; cursor: pointer; transition: all 0.2s;
}
.risk-item:hover { background: #F5F5F5; border-color: #E0E0E0; }
.risk-item--high { border-left: 3px solid #F44336; }
.risk-item--medium { border-left: 3px solid #FF9800; }
.student-avatar { flex-shrink: 0; }
.risk-info { flex: 1; }
.risk-name { font-size: 14px; font-weight: 600; color: #222; }
.risk-reason { font-size: 12px; color: #888; margin-top: 2px; }
.risk-score { min-width: 100px; }
.trust-score-bar { height: 4px; background: #eee; border-radius: 2px; margin-bottom: 4px; }
.trust-fill { height: 100%; border-radius: 2px; transition: width 0.6s; }
.fill--high { background: #4CAF50; }
.fill--mid { background: #FF9800; }
.fill--low { background: #F44336; }
.score-num { font-size: 11px; color: #aaa; }
.risk-tag { flex-shrink: 0; }
.pending-row { margin-bottom: 16px; }
.pending-card {
  background: #fff; border-radius: 14px; padding: 16px;
  display: flex; align-items: center; gap: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05); cursor: pointer;
  transition: transform 0.2s;
}
.pending-card:hover { transform: translateY(-2px); }
.pending-icon { font-size: 28px; }
.pending-body { flex: 1; }
.pending-num { font-size: 24px; font-weight: 800; color: #1565C0; }
.pending-label { font-size: 12px; color: #888; }
.pending-arrow { color: #ccc; }
.monthly-kpi-card { background: #fff; border-radius: 16px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.mk-header { display: flex; justify-content: space-between; margin-bottom: 20px; }
.mk-title { font-size: 16px; font-weight: 700; margin: 0; }
.mk-period { font-size: 12px; color: #888; }
.mk-metric { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.mk-label { font-size: 12px; color: #888; text-align: center; }
.supervision-card {
  background: linear-gradient(135deg, #E8EAF6, #E3F2FD);
  border-radius: 14px; padding: 16px;
  display: flex; align-items: center; gap: 12px;
}
.sv-icon { font-size: 24px; }
.sv-body { flex: 1; }
.sv-label { font-size: 12px; color: #666; margin: 0 0 2px; }
.sv-time { font-size: 14px; font-weight: 600; color: #1A237E; margin: 0; }
</style>
