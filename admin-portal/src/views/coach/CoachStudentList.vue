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

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const token = localStorage.getItem('admin_token')
const authHeaders = { Authorization: `Bearer ${token}` }

const loading = ref(false)
const students = ref<any[]>([])

const PAGE_SIZE = 30

const stageLabels: Record<string, string> = {
  S0: '觉醒期', S1: '松动期', S2: '探索期', S3: '准备期',
  S4: '行动期', S5: '坚持期', S6: '融入期',
}
const stageLabel = (s: string) => stageLabels[s] || s || '未评估'

function openDetail(student: any) {
  router.push(`/coach/student-assessment/${student.id}`)
}

// 示例学员生成（与 CoachHome 保持一致）
function generateSampleStudents() {
  const names = [
    '张明华', '王小红', '李建国', '赵芳芳', '刘大伟', '陈晓丽', '杨志强', '黄丽萍',
    '周文博', '吴雅琴', '孙海涛', '马晓东', '朱秀英', '胡建华', '林美玲', '郭志远',
    '何晓燕', '高建平', '罗雪梅', '梁伟明', '谢丽娟', '宋志刚', '唐小芳', '韩大勇',
    '冯雅静', '曹明辉', '彭晓霞', '潘建文', '蒋美华', '邓志豪',
  ]
  const stages = ['S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6']
  const conditions = [
    '2型糖尿病·饮食管理', '高血压·运动干预', '肥胖·综合管理', '失眠·睡眠行为调整',
    '焦虑·情绪管理', '慢性疼痛·行为康复', '代谢综合征·生活方式干预', '行为健康管理',
  ]
  const contactDays = ['今天', '1天前', '2天前', '3天前', '5天前', '7天前', '10天前']

  return names.map((name, i) => {
    const stage = stages[i % stages.length]
    const dayIdx = Math.min(i % 7, contactDays.length - 1)
    const daysNum = [0, 1, 2, 3, 5, 7, 10][dayIdx]
    let priority = 'low'
    if (daysNum >= 5 || stage === 'S0') priority = 'high'
    else if (daysNum >= 3 || stage === 'S1') priority = 'medium'

    return {
      id: 1000 + i,
      name,
      avatar: '',
      condition: conditions[i % conditions.length],
      stage,
      lastContact: contactDays[dayIdx],
      priority,
      healthData: {
        fastingGlucose: +(5.0 + Math.random() * 8).toFixed(1),
        postprandialGlucose: +(7.0 + Math.random() * 9).toFixed(1),
        weight: +(55 + Math.random() * 40).toFixed(1),
        exerciseMinutes: Math.floor(Math.random() * 90),
      },
      microAction7d: { completed: Math.floor(Math.random() * 7), total: 7 },
      riskFlags: daysNum >= 5 ? ['dropout_risk'] : [],
    }
  })
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/v1/coach/dashboard`, { headers: authHeaders })
    if (!res.ok) throw new Error('API failed')
    const data = await res.json()
    const rawStudents = (data.students || []).map((st: any) => ({
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
    students.value = rawStudents.length > 0 ? rawStudents.slice(0, PAGE_SIZE) : generateSampleStudents()
  } catch {
    students.value = generateSampleStudents()
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
