<template>
  <div class="coach-student-list-page">
    <div class="page-header">
      <a-button type="text" @click="$router.push('/coach-portal')">
        <LeftOutlined /> 返回工作台
      </a-button>
      <h2>待跟进学员 ({{ students.length }})</h2>
    </div>

    <div v-if="loading" style="text-align:center;padding:60px 0">
      <a-spin size="large" tip="加载学员数据..." />
    </div>

    <a-alert v-else-if="error" type="error" :message="error" show-icon style="margin-bottom: 16px" />

    <a-empty v-else-if="students.length === 0" description="暂无待跟进学员" />

    <div v-else class="list-container">
      <div
        v-for="student in students"
        :key="student.id"
        class="student-card"
        @click="openDetail(student)"
      >
        <div class="student-avatar">
          <a-avatar :size="48" :src="student.avatar">
            {{ student.name?.charAt(0) }}
          </a-avatar>
          <span class="stage-badge" :class="student.stage">
            {{ stageLabel(student.stage) }}
          </span>
        </div>
        <div class="student-info">
          <div class="student-name">{{ student.name }}</div>
          <div class="student-condition">{{ student.condition }}</div>
          <div class="student-meta">
            <span class="meta-item">
              <ClockCircleOutlined /> {{ student.lastContact }}
            </span>
            <span class="meta-item" v-if="student.microAction7d">
              微行动 {{ student.microAction7d.completed }}/{{ student.microAction7d.total }}
            </span>
            <a-tag v-if="student.priority === 'high'" color="red" size="small">紧急</a-tag>
            <a-tag v-else-if="student.priority === 'medium'" color="orange" size="small">重要</a-tag>
          </div>
          <div class="student-health" v-if="student.healthData">
            <a-tag v-if="student.healthData.fastingGlucose" size="small">
              空腹 {{ student.healthData.fastingGlucose }} mmol/L
            </a-tag>
            <a-tag v-if="student.healthData.exerciseMinutes" size="small" color="green">
              运动 {{ student.healthData.exerciseMinutes }} 分钟
            </a-tag>
          </div>
        </div>
        <div class="student-actions">
          <a-button type="primary" size="small" @click.stop="$router.push(`/coach/student-assessment/${student.id}`)">
            查看测评
          </a-button>
          <a-button size="small" @click.stop="$router.push(`/coach/student-profile/${student.id}`)">
            行为画像
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { LeftOutlined, ClockCircleOutlined } from '@ant-design/icons-vue'
import request from '@/api/request'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const students = ref<any[]>([])

const stageLabels: Record<string, string> = {
  S0: '觉醒期', S1: '松动期', S2: '探索期', S3: '准备期',
  S4: '行动期', S5: '坚持期', S6: '融入期',
}
const stageLabel = (s: string) => stageLabels[s] || s || '未评估'

function openDetail(student: any) {
  router.push(`/coach/student-assessment/${student.id}`)
}

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await request.get('/v1/coach/dashboard')
    const data = res.data
    students.value = (data.students || []).map((st: any) => ({
      id: st.id,
      name: st.name,
      avatar: st.avatar || '',
      condition: st.condition || '行为健康管理',
      stage: st.stage || 'unknown',
      lastContact: st.last_contact || '未知',
      priority: st.priority || 'low',
      healthData: {
        fastingGlucose: st.health_data?.fasting_glucose ?? null,
        postprandialGlucose: st.health_data?.postprandial_glucose ?? null,
        weight: st.health_data?.weight ?? null,
        exerciseMinutes: st.health_data?.exercise_minutes ?? 0,
      },
      microAction7d: st.micro_action_7d || { completed: 0, total: 0 },
      riskFlags: st.risk_flags || [],
    }))
  } catch (e: any) {
    error.value = '加载学员数据失败，请稍后重试'
    console.error('CoachStudentList fetch error:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.coach-student-list-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 18px;
}
.list-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.student-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.student-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.student-avatar {
  position: relative;
  flex-shrink: 0;
}
.stage-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  color: #fff;
  white-space: nowrap;
  background: #999;
}
.stage-badge.S0, .stage-badge.S1 { background: #ff4d4f; }
.stage-badge.S2, .stage-badge.S3 { background: #faad14; }
.stage-badge.S4, .stage-badge.S5 { background: #52c41a; }
.stage-badge.S6 { background: #1890ff; }
.student-info {
  flex: 1;
  min-width: 0;
}
.student-name {
  font-size: 15px;
  font-weight: 600;
}
.student-condition {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
.student-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}
.student-health {
  display: flex;
  gap: 4px;
  margin-top: 6px;
}
.student-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}
</style>
