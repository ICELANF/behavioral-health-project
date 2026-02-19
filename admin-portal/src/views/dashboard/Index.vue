<template>
  <div class="dashboard">
    <!-- 用户欢迎卡片 -->
    <a-card style="margin-bottom: 16px">
      <a-row align="middle">
        <a-col :span="18">
          <h2 style="margin: 0">欢迎回来，{{ userInfo.userId }}</h2>
          <p style="color: #666; margin: 8px 0 0">
            角色: {{ userInfo.roleLabel }} | 等级: L{{ userInfo.level }}
          </p>
        </a-col>
        <a-col :span="6" style="text-align: right">
          <a-tag :color="userInfo.roleColor">{{ userInfo.role }}</a-tag>
        </a-col>
      </a-row>
    </a-card>

    <a-row :gutter="16">
      <a-col :span="6">
        <a-card>
          <a-statistic title="注册学员" :value="stats.totalUsers" suffix="人">
            <template #prefix><UserOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="认证教练" :value="stats.totalCoaches" suffix="人">
            <template #prefix><TeamOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="课程数量" :value="stats.totalCourses" suffix="门">
            <template #prefix><VideoCameraOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="今日学习" :value="stats.todayLearning" suffix="人次">
            <template #prefix><ReadOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="16">
        <a-card title="认证等级分布">
          <div style="display: flex; align-items: flex-end; height: 280px; gap: 40px; padding: 20px; justify-content: center;">
            <div v-for="bar in levelDistribution" :key="bar.level" style="text-align: center;">
              <div :style="{ height: bar.height + 'px', width: '60px', background: bar.gradient, borderRadius: '4px' }"></div>
              <div style="margin-top: 8px; color: #666;">{{ bar.level }}<br/>{{ bar.count }}人</div>
            </div>
            <a-empty v-if="levelDistribution.length === 0" description="暂无数据" />
          </div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="待处理事项">
          <div v-for="(todo, idx) in pendingTodos" :key="idx" :style="{ padding: '8px 0', borderBottom: idx < pendingTodos.length - 1 ? '1px solid #f0f0f0' : 'none' }">
            <a-badge :status="todo.status" :text="todo.text" />
          </div>
          <a-empty v-if="pendingTodos.length === 0" description="暂无待处理事项" />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="12">
        <a-card title="最近考试">
          <a-table :dataSource="recentExams" :columns="examColumns" rowKey="name" size="small" :pagination="false" />
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="晋级申请">
          <a-table :dataSource="recentPromotions" :columns="promotionColumns" rowKey="id" size="small" :pagination="false" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  UserOutlined,
  TeamOutlined,
  VideoCameraOutlined,
  ReadOutlined
} from '@ant-design/icons-vue'
import request from '@/api/request'

// 角色映射
const roleLabels: Record<string, string> = {
  ADMIN: '系统管理员',
  EXPERT: '专家',
  COACH_SENIOR: '教练',
  COACH_INTERMEDIATE: '分享者',
  COACH_JUNIOR: '成长者',
  USER: '学员'
}

const roleColors: Record<string, string> = {
  ADMIN: 'red',
  EXPERT: 'purple',
  COACH_SENIOR: 'gold',
  COACH_INTERMEDIATE: 'blue',
  COACH_JUNIOR: 'green',
  USER: 'default'
}

// 从 localStorage 读取用户信息
const storedUsername = localStorage.getItem('admin_username') || '管理员'
const storedRole = localStorage.getItem('admin_role') || 'USER'
const storedLevel = parseInt(localStorage.getItem('admin_level') || '0')

const userInfo = ref({
  userId: storedUsername,
  role: storedRole,
  roleLabel: roleLabels[storedRole] || '学员',
  roleColor: roleColors[storedRole] || 'default',
  level: storedLevel
})

const stats = reactive({ totalUsers: 0, totalCoaches: 0, totalCourses: 0, todayLearning: 0 })

const levelGradients = [
  'linear-gradient(to top, #1890ff, #69c0ff)',
  'linear-gradient(to top, #52c41a, #95de64)',
  'linear-gradient(to top, #faad14, #ffc53d)',
  'linear-gradient(to top, #f5222d, #ff7875)',
  'linear-gradient(to top, #722ed1, #b37feb)',
]
const levelDistribution = ref<{ level: string; count: number; height: number; gradient: string }[]>([])

const pendingTodos = ref<{ status: string; text: string }[]>([])
const recentExams = ref<any[]>([])
const recentPromotions = ref<any[]>([])

const examColumns = [
  { title: '考试名称', dataIndex: 'name' },
  { title: '参考人数', dataIndex: 'participants' },
  { title: '平均分', dataIndex: 'avgScore' },
  { title: '通过率', dataIndex: 'passRate' },
]
const promotionColumns = [
  { title: '教练', dataIndex: 'coachName' },
  { title: '当前等级', dataIndex: 'currentLevel' },
  { title: '申请等级', dataIndex: 'targetLevel' },
  { title: '申请日期', dataIndex: 'appliedAt' },
]

const loadDashboard = async () => {
  try {
    const res = await request.get('v1/analytics/admin/overview')
    const d = res.data?.data || res.data || {}
    stats.totalUsers = d.total_users ?? d.totalUsers ?? 0
    stats.totalCoaches = d.total_coaches ?? d.totalCoaches ?? 0
    stats.totalCourses = d.total_courses ?? d.totalCourses ?? 0
    stats.todayLearning = d.today_learning ?? d.todayLearning ?? 0
    // Level distribution
    const dist = d.level_distribution || d.levelDistribution || {}
    const maxCount = Math.max(...Object.values(dist).map(Number), 1)
    levelDistribution.value = Object.entries(dist).map(([level, count], i) => ({
      level, count: Number(count),
      height: Math.max(Math.round((Number(count) / maxCount) * 200), 10),
      gradient: levelGradients[i % levelGradients.length],
    }))
    // Pending todos
    const todos = d.pending_todos || d.pendingTodos || []
    pendingTodos.value = todos.map((t: any) => ({
      status: t.status || 'default', text: t.text || t.label || '',
    }))
    // Recent exams
    recentExams.value = (d.recent_exams || d.recentExams || []).map((e: any) => ({
      name: e.name || e.title || '', participants: e.participants ?? 0,
      avgScore: e.avg_score ?? e.avgScore ?? 0,
      passRate: e.pass_rate ? `${e.pass_rate}%` : (e.passRate || '0%'),
    }))
    // Promotion applications
    recentPromotions.value = (d.recent_promotions || d.recentPromotions || []).map((p: any) => ({
      id: p.id, coachName: p.coach_name || p.coachName || '',
      currentLevel: p.current_level || p.currentLevel || '',
      targetLevel: p.target_level || p.targetLevel || '',
      appliedAt: p.applied_at || p.appliedAt || '',
    }))
  } catch (e) {
    console.error('加载仪表盘数据失败:', e)
  }
}

onMounted(loadDashboard)
</script>

<style scoped>
.dashboard :deep(.ant-card) {
  border-radius: 8px;
}
</style>
