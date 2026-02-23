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
          <div
            v-for="(todo, idx) in pendingTodos" :key="idx"
            class="todo-item"
            :style="{ borderBottom: idx < pendingTodos.length - 1 ? '1px solid #f0f0f0' : 'none' }"
            @click="openTodoDetail(todo)"
          >
            <a-badge :status="todo.status" :text="todo.text" />
            <span class="todo-arrow">›</span>
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

    <!-- 待处理事项详情抽屉 -->
    <a-drawer
      v-model:open="drawerVisible"
      :title="drawerTitle"
      width="520"
      placement="right"
    >
      <a-empty v-if="drawerItems.length === 0" description="暂无详细记录" />

      <div v-for="(item, idx) in drawerItems" :key="idx" class="drawer-item">
        <div class="drawer-item-header">
          <a-tag :color="item.tagColor" size="small">{{ item.tag }}</a-tag>
          <span class="drawer-item-date">{{ item.date }}</span>
        </div>
        <div class="drawer-item-title">{{ item.title }}</div>
        <div v-if="item.content" class="drawer-item-content">{{ item.content }}</div>
      </div>

      <template #footer>
        <a-button v-if="drawerLink" type="primary" block @click="$router.push(drawerLink); drawerVisible = false">
          前往处理页面
        </a-button>
      </template>
    </a-drawer>
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

// 角色映射 (六级体系 + 向后兼容旧角色名)
const roleLabels: Record<string, string> = {
  ADMIN: '系统管理员',
  MASTER: '大师',
  SUPERVISOR: '督导',
  PROMOTER: '促进师',
  COACH: '教练',
  SHARER: '分享者',
  GROWER: '成长者',
  OBSERVER: '观察员',
  // 向后兼容
  EXPERT: '专家',
  COACH_SENIOR: '教练',
  COACH_INTERMEDIATE: '分享者',
  COACH_JUNIOR: '成长者',
  PATIENT: '学员',
  USER: '学员',
}

const roleColors: Record<string, string> = {
  ADMIN: 'red',
  MASTER: 'volcano',
  SUPERVISOR: 'purple',
  PROMOTER: 'magenta',
  COACH: 'gold',
  SHARER: 'blue',
  GROWER: 'green',
  OBSERVER: 'cyan',
  // 向后兼容
  EXPERT: 'purple',
  COACH_SENIOR: 'gold',
  COACH_INTERMEDIATE: 'blue',
  COACH_JUNIOR: 'green',
  PATIENT: 'default',
  USER: 'default',
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

// ── 待处理事项 ──
interface TodoItem {
  status: string
  text: string
  link?: string
  /** 明细数据 key，指向 detailStore 中的具体列表 */
  detailKey?: string
}
interface DetailItem {
  tag: string
  tagColor: string
  title: string
  content: string
  date: string
}

const pendingTodos = ref<TodoItem[]>([])
/** 按分类存储原始明细，点击时读取 */
const detailStore = ref<Record<string, DetailItem[]>>({})

// 抽屉状态
const drawerVisible = ref(false)
const drawerTitle = ref('')
const drawerLink = ref('')
const drawerItems = ref<DetailItem[]>([])

const openTodoDetail = (todo: TodoItem) => {
  drawerTitle.value = todo.text
  drawerLink.value = todo.link || ''
  drawerItems.value = todo.detailKey ? (detailStore.value[todo.detailKey] || []) : []
  drawerVisible.value = true
}

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

const statusLabelMap: Record<string, [string, string]> = {
  pending: ['待审核', 'orange'],
  approved: ['已审核', 'cyan'],
  sent: ['已发送', 'green'],
  rejected: ['已拒绝', 'red'],
}

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

    // Pending todos (from overview API)
    const todos: TodoItem[] = (d.pending_todos || d.pendingTodos || []).map((t: any) => ({
      status: t.status || 'default', text: t.text || t.label || '', link: t.link || '',
    }))
    pendingTodos.value = todos
    const store: Record<string, DetailItem[]> = {}

    // Supplement: fetch pending promotion applications
    try {
      const supRes = await request.get('v1/promotion/applications', { params: { status: 'pending' } })
      const apps = supRes.data?.applications || []
      if (apps.length > 0) {
        store['promotion'] = apps.map((a: any) => ({
          tag: '晋级申请', tagColor: 'purple',
          title: `${a.full_name || a.username || ''}: ${a.current_level} → ${a.target_level}`,
          content: a.reviewer_comment || '',
          date: a.applied_at || '',
        }))
        pendingTodos.value.push({
          status: 'warning',
          text: `${apps.length} 条督导/晋级申请待审核`,
          link: '/expert/my/supervision',
          detailKey: 'promotion',
        })
      }
    } catch { /* optional */ }

    // Supplement: fetch pending push queue items (includes supervision schedules)
    try {
      const queueRes = await request.get('v1/coach/push-queue', { params: { status: 'pending', page_size: 50 } })
      const queueItems: any[] = queueRes.data?.items || []
      const queueTotal: number = queueRes.data?.total || 0

      const supervisionItems = queueItems.filter((i: any) => i.content?.startsWith('[督导安排]'))
      const otherItems = queueItems.filter((i: any) => !i.content?.startsWith('[督导安排]'))
      const otherCount = queueTotal - supervisionItems.length

      if (supervisionItems.length > 0) {
        store['supervision'] = supervisionItems.map((item: any) => {
          const lines = (item.content || '').split('\n')
          const [sl] = statusLabelMap[item.status] || ['待处理', 'blue']
          return {
            tag: sl, tagColor: (statusLabelMap[item.status] || [])[1] || 'blue',
            title: lines[0].replace('[督导安排] ', ''),
            content: lines.slice(1).join('\n'),
            date: item.created_at || '',
          }
        })
        pendingTodos.value.push({
          status: 'warning',
          text: `${supervisionItems.length} 条督导安排待处理`,
          link: '/expert/my/supervision',
          detailKey: 'supervision',
        })
      }

      if (otherCount > 0) {
        store['pushQueue'] = otherItems.map((item: any) => {
          const [sl] = statusLabelMap[item.status] || ['待处理', 'blue']
          return {
            tag: sl, tagColor: (statusLabelMap[item.status] || [])[1] || 'blue',
            title: item.title || '推送消息',
            content: item.content || '',
            date: item.created_at || '',
          }
        })
        pendingTodos.value.push({
          status: 'processing',
          text: `${otherCount} 条推送消息待审核`,
          link: '/coach/push-queue',
          detailKey: 'pushQueue',
        })
      }
    } catch { /* optional */ }

    detailStore.value = store

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

.todo-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  cursor: pointer;
  transition: background 0.2s;
}
.todo-item:hover {
  background: #fafafa;
}
.todo-arrow {
  color: #999;
  font-size: 16px;
  font-weight: 700;
  padding-left: 8px;
}

.drawer-item {
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
}
.drawer-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.drawer-item-date {
  font-size: 12px;
  color: #999;
}
.drawer-item-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}
.drawer-item-content {
  font-size: 13px;
  color: #666;
  white-space: pre-line;
}
</style>
