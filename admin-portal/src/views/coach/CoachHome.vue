<template>
  <div class="coach-portal">
    <!-- 顶部导航栏 -->
    <div class="portal-header">
      <div class="header-left">
        <span class="greeting">{{ getGreeting() }}，{{ coachInfo.name }}</span>
        <a-tag :color="getLevelColor(coachInfo.level)">{{ coachInfo.level }} {{ coachInfo.levelName }}</a-tag>
      </div>
      <div class="header-right">
        <a-badge :count="notifications" :offset="[-2, 2]">
          <BellOutlined class="header-icon" />
        </a-badge>
        <a-dropdown>
          <a-avatar :src="coachInfo.avatar" :size="36">
            {{ coachInfo.name?.charAt(0) }}
          </a-avatar>
          <template #overlay>
            <a-menu>
              <a-menu-item key="profile">个人中心</a-menu-item>
              <a-menu-item key="settings">设置</a-menu-item>
              <a-menu-divider />
              <a-menu-item key="logout" @click="handleLogout">退出登录</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- 今日工作概览 -->
    <div class="overview-section">
      <div class="section-title">
        <CalendarOutlined /> 今日工作概览
      </div>
      <div class="overview-cards">
        <div class="overview-card">
          <div class="card-icon todo"><ClockCircleOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ todayStats.pendingFollowups }}</div>
            <div class="card-label">待跟进</div>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon done"><CheckCircleOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ todayStats.completedFollowups }}</div>
            <div class="card-label">已完成</div>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon alert"><AlertOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ todayStats.alertStudents }}</div>
            <div class="card-label">需关注</div>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon message"><MessageOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ todayStats.unreadMessages }}</div>
            <div class="card-label">未读消息</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 待跟进学员列表 -->
    <div class="students-section">
      <div class="section-header">
        <div class="section-title">
          <TeamOutlined /> 待跟进学员
        </div>
        <a class="view-all" @click="goToStudentList">查看全部 <RightOutlined /></a>
      </div>

      <div class="student-list">
        <div
          v-for="student in pendingStudents"
          :key="student.id"
          class="student-card"
          @click="openStudentDetail(student)"
        >
          <div class="student-avatar">
            <a-avatar :size="48" :src="student.avatar">
              {{ student.name?.charAt(0) }}
            </a-avatar>
            <span class="stage-badge" :class="student.stage">
              {{ getStageLabel(student.stage) }}
            </span>
          </div>
          <div class="student-info">
            <div class="student-name">{{ student.name }}</div>
            <div class="student-condition">{{ student.condition }}</div>
            <div class="student-meta">
              <span class="meta-item">
                <ClockCircleOutlined /> {{ student.lastContact }}
              </span>
              <a-tag v-if="student.priority === 'high'" color="red" size="small">紧急</a-tag>
              <a-tag v-else-if="student.priority === 'medium'" color="orange" size="small">重要</a-tag>
            </div>
          </div>
          <div class="student-action">
            <a-button type="primary" size="small" @click.stop="startFollowup(student)">
              开始跟进
            </a-button>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 助手推荐 -->
    <div class="ai-section">
      <div class="section-header">
        <div class="section-title">
          <RobotOutlined /> AI 干预建议
        </div>
      </div>

      <div class="ai-recommendations">
        <div
          v-for="rec in aiRecommendations"
          :key="rec.id"
          class="recommendation-card"
        >
          <div class="rec-header">
            <span class="rec-type" :class="rec.type">{{ rec.typeLabel }}</span>
            <span class="rec-student">{{ rec.studentName }}</span>
          </div>
          <div class="rec-content">{{ rec.suggestion }}</div>
          <div class="rec-actions">
            <a-button size="small" type="link" @click="applyRecommendation(rec)">
              采纳建议
            </a-button>
            <a-button size="small" type="link" @click="viewDetail(rec)">
              查看详情
            </a-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 干预包快捷入口 -->
    <div class="intervention-section">
      <div class="section-header">
        <div class="section-title">
          <AppstoreOutlined /> 干预工具箱
        </div>
      </div>

      <div class="intervention-grid">
        <div
          v-for="tool in interventionTools"
          :key="tool.id"
          class="tool-card"
          @click="openTool(tool)"
        >
          <div class="tool-icon">{{ tool.icon }}</div>
          <div class="tool-name">{{ tool.name }}</div>
        </div>
      </div>
    </div>

    <!-- 学习进度 -->
    <div class="learning-section">
      <div class="section-header">
        <div class="section-title">
          <BookOutlined /> 我的学习
        </div>
        <a class="view-all">查看课程 <RightOutlined /></a>
      </div>

      <div class="learning-progress">
        <div class="progress-item">
          <div class="progress-label">
            <span>{{ coachInfo.level }} 认证进度</span>
            <span class="progress-value">{{ learningProgress.certProgress }}%</span>
          </div>
          <a-progress
            :percent="learningProgress.certProgress"
            :show-info="false"
            stroke-color="#667eea"
          />
        </div>
        <div class="progress-stats">
          <div class="stat-item">
            <div class="stat-value">{{ learningProgress.coursesCompleted }}/{{ learningProgress.coursesTotal }}</div>
            <div class="stat-label">课程完成</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ learningProgress.examsPassed }}/{{ learningProgress.examsTotal }}</div>
            <div class="stat-label">考试通过</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ learningProgress.caseCount }}</div>
            <div class="stat-label">案例积累</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="bottom-nav">
      <div class="nav-item active">
        <HomeOutlined />
        <span>工作台</span>
      </div>
      <div class="nav-item" @click="goToStudentList">
        <TeamOutlined />
        <span>学员</span>
      </div>
      <div class="nav-item" @click="goToMessages">
        <MessageOutlined />
        <span>消息</span>
      </div>
      <div class="nav-item" @click="goToLearning">
        <BookOutlined />
        <span>学习</span>
      </div>
      <div class="nav-item" @click="goToProfile">
        <UserOutlined />
        <span>我的</span>
      </div>
    </div>

    <!-- 学员详情抽屉 -->
    <a-drawer
      v-model:open="studentDrawerVisible"
      :title="currentStudent?.name"
      placement="right"
      width="100%"
      :closable="true"
    >
      <template v-if="currentStudent">
        <div class="student-detail">
          <div class="detail-header">
            <a-avatar :size="64" :src="currentStudent.avatar">
              {{ currentStudent.name?.charAt(0) }}
            </a-avatar>
            <div class="detail-info">
              <h3>{{ currentStudent.name }}</h3>
              <p>{{ currentStudent.condition }}</p>
              <a-tag :color="getStageColor(currentStudent.stage)">
                {{ getStageLabel(currentStudent.stage) }}
              </a-tag>
            </div>
          </div>

          <a-tabs>
            <a-tab-pane key="health" tab="健康数据">
              <div class="health-metrics">
                <div class="metric-item">
                  <div class="metric-label">空腹血糖</div>
                  <div class="metric-value">{{ currentStudent.healthData?.fastingGlucose || '--' }} mmol/L</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">餐后血糖</div>
                  <div class="metric-value">{{ currentStudent.healthData?.postprandialGlucose || '--' }} mmol/L</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">体重</div>
                  <div class="metric-value">{{ currentStudent.healthData?.weight || '--' }} kg</div>
                </div>
                <div class="metric-item">
                  <div class="metric-label">本周运动</div>
                  <div class="metric-value">{{ currentStudent.healthData?.exerciseMinutes || 0 }} 分钟</div>
                </div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="records" tab="跟进记录">
              <div class="followup-records">
                <a-timeline>
                  <a-timeline-item v-for="record in currentStudent.records" :key="record.id" :color="record.type === 'call' ? 'blue' : 'green'">
                    <div class="record-item">
                      <div class="record-time">{{ record.time }}</div>
                      <div class="record-content">{{ record.content }}</div>
                    </div>
                  </a-timeline-item>
                </a-timeline>
              </div>
            </a-tab-pane>
            <a-tab-pane key="intervention" tab="干预方案">
              <div class="intervention-plan">
                <a-empty v-if="!currentStudent.interventionPlan" description="暂无干预方案" />
                <div v-else>
                  <h4>{{ currentStudent.interventionPlan.name }}</h4>
                  <p>{{ currentStudent.interventionPlan.description }}</p>
                </div>
              </div>
            </a-tab-pane>
          </a-tabs>

          <div class="detail-actions">
            <a-button type="primary" block @click="startFollowup(currentStudent)">
              开始跟进对话
            </a-button>
          </div>
        </div>
      </template>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  BellOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  AlertOutlined,
  MessageOutlined,
  TeamOutlined,
  RightOutlined,
  RobotOutlined,
  AppstoreOutlined,
  BookOutlined,
  HomeOutlined,
  UserOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

// 教练信息
const coachInfo = reactive({
  id: 'coach001',
  name: localStorage.getItem('admin_name') || '李教练',
  avatar: '',
  level: 'L2',
  levelName: '中级教练',
  specialty: ['糖尿病逆转', '体重管理']
})

const notifications = ref(3)

// 今日统计
const todayStats = reactive({
  pendingFollowups: 8,
  completedFollowups: 5,
  alertStudents: 2,
  unreadMessages: 12
})

// 待跟进学员
const pendingStudents = ref([
  {
    id: 's001',
    name: '张明华',
    avatar: '',
    condition: '2型糖尿病 · 高血压',
    stage: 'action',
    lastContact: '2天前',
    priority: 'high',
    healthData: {
      fastingGlucose: 7.2,
      postprandialGlucose: 10.5,
      weight: 78,
      exerciseMinutes: 90
    },
    records: [
      { id: 'r1', type: 'call', time: '2024-01-23 14:30', content: '电话跟进，患者反馈血糖控制有所改善' },
      { id: 'r2', type: 'message', time: '2024-01-21 09:15', content: '发送饮食指导资料' }
    ],
    interventionPlan: {
      name: '血糖管理强化方案',
      description: '针对餐后血糖控制的个性化干预'
    }
  },
  {
    id: 's002',
    name: '王小红',
    avatar: '',
    condition: '糖尿病前期 · 肥胖',
    stage: 'preparation',
    lastContact: '1天前',
    priority: 'medium',
    healthData: {
      fastingGlucose: 6.5,
      postprandialGlucose: 8.8,
      weight: 85,
      exerciseMinutes: 45
    },
    records: [
      { id: 'r3', type: 'message', time: '2024-01-24 10:00', content: '提醒完成今日运动任务' }
    ],
    interventionPlan: null
  },
  {
    id: 's003',
    name: '李建国',
    avatar: '',
    condition: '2型糖尿病',
    stage: 'contemplation',
    lastContact: '3天前',
    priority: 'low',
    healthData: {
      fastingGlucose: 8.1,
      postprandialGlucose: 12.3,
      weight: 72,
      exerciseMinutes: 30
    },
    records: [],
    interventionPlan: null
  }
])

// AI 推荐
const aiRecommendations = ref([
  {
    id: 'ai001',
    type: 'alert',
    typeLabel: '风险提醒',
    studentName: '张明华',
    suggestion: '该学员近3天血糖波动较大，建议进行电话跟进，了解饮食和用药情况'
  },
  {
    id: 'ai002',
    type: 'intervention',
    typeLabel: '干预建议',
    studentName: '王小红',
    suggestion: '学员处于准备期，建议推送"运动入门指南"课程，强化行为改变动机'
  },
  {
    id: 'ai003',
    type: 'followup',
    typeLabel: '跟进提醒',
    studentName: '李建国',
    suggestion: '该学员已3天未打卡，建议发送关怀消息，了解近况'
  }
])

// 干预工具
const interventionTools = ref([
  { id: 't1', icon: '📋', name: '评估量表' },
  { id: 't2', icon: '📚', name: '健康课程' },
  { id: 't3', icon: '🎯', name: '目标设定' },
  { id: 't4', icon: '💬', name: '话术模板' },
  { id: 't5', icon: '📊', name: '数据分析' },
  { id: 't6', icon: '🤖', name: 'AI 助手' }
])

// 学习进度
const learningProgress = reactive({
  certProgress: 65,
  coursesCompleted: 8,
  coursesTotal: 12,
  examsPassed: 2,
  examsTotal: 3,
  caseCount: 15
})

// 学员详情抽屉
const studentDrawerVisible = ref(false)
const currentStudent = ref<typeof pendingStudents.value[0] | null>(null)

// 方法
const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
}

const getLevelColor = (level: string) => {
  const colors: Record<string, string> = {
    'L0': 'default',
    'L1': 'blue',
    'L2': 'green',
    'L3': 'purple',
    'L4': 'gold'
  }
  return colors[level] || 'default'
}

const getStageLabel = (stage: string) => {
  const labels: Record<string, string> = {
    precontemplation: '前意向期',
    contemplation: '意向期',
    preparation: '准备期',
    action: '行动期',
    maintenance: '维持期'
  }
  return labels[stage] || stage
}

const getStageColor = (stage: string) => {
  const colors: Record<string, string> = {
    precontemplation: 'default',
    contemplation: 'blue',
    preparation: 'cyan',
    action: 'green',
    maintenance: 'purple'
  }
  return colors[stage] || 'default'
}

const openStudentDetail = (student: typeof pendingStudents.value[0]) => {
  currentStudent.value = student
  studentDrawerVisible.value = true
}

const startFollowup = (student: typeof pendingStudents.value[0]) => {
  message.info(`开始跟进 ${student.name}`)
  // TODO: 打开跟进对话界面
}

const applyRecommendation = (rec: typeof aiRecommendations.value[0]) => {
  message.success('已采纳建议')
}

const viewDetail = (rec: typeof aiRecommendations.value[0]) => {
  message.info('查看详情')
}

const openTool = (tool: typeof interventionTools.value[0]) => {
  message.info(`打开 ${tool.name}`)
}

const goToStudentList = () => {
  router.push('/student')
}

const goToMessages = () => {
  message.info('消息中心')
}

const goToLearning = () => {
  router.push('/course/list')
}

const goToProfile = () => {
  message.info('个人中心')
}

const handleLogout = () => {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_username')
  localStorage.removeItem('admin_role')
  localStorage.removeItem('admin_level')
  localStorage.removeItem('admin_name')
  router.push('/login')
}

onMounted(() => {
  // 加载数据
})
</script>

<style scoped>
.coach-portal {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 70px;
}

/* 顶部导航 */
.portal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.greeting {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  color: #fff;
  font-size: 20px;
  cursor: pointer;
}

/* 概览区域 */
.overview-section {
  padding: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.overview-card {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.card-icon.todo {
  background: #fff7e6;
  color: #fa8c16;
}

.card-icon.done {
  background: #f6ffed;
  color: #52c41a;
}

.card-icon.alert {
  background: #fff1f0;
  color: #f5222d;
}

.card-icon.message {
  background: #e6f7ff;
  color: #1890ff;
}

.card-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.card-label {
  font-size: 12px;
  color: #6b7280;
}

/* 学员列表 */
.students-section {
  padding: 0 16px 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.view-all {
  font-size: 13px;
  color: #667eea;
  display: flex;
  align-items: center;
  gap: 4px;
}

.student-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.student-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: transform 0.2s;
}

.student-card:active {
  transform: scale(0.98);
}

.student-avatar {
  position: relative;
}

.stage-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
  white-space: nowrap;
  background: #e8e8e8;
  color: #666;
}

.stage-badge.action {
  background: #f6ffed;
  color: #52c41a;
}

.stage-badge.preparation {
  background: #e6fffb;
  color: #13c2c2;
}

.stage-badge.contemplation {
  background: #e6f7ff;
  color: #1890ff;
}

.student-info {
  flex: 1;
  min-width: 0;
}

.student-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.student-condition {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.student-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #9ca3af;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* AI 推荐 */
.ai-section {
  padding: 0 16px 16px;
}

.ai-recommendations {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.rec-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.rec-type {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.rec-type.alert {
  background: #fff1f0;
  color: #f5222d;
}

.rec-type.intervention {
  background: #e6f7ff;
  color: #1890ff;
}

.rec-type.followup {
  background: #fff7e6;
  color: #fa8c16;
}

.rec-student {
  font-size: 13px;
  color: #6b7280;
}

.rec-content {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
}

.rec-actions {
  margin-top: 8px;
  display: flex;
  gap: 12px;
}

/* 干预工具 */
.intervention-section {
  padding: 0 16px 16px;
}

.intervention-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.tool-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: transform 0.2s;
}

.tool-card:active {
  transform: scale(0.95);
}

.tool-icon {
  font-size: 28px;
  margin-bottom: 6px;
}

.tool-name {
  font-size: 13px;
  color: #374151;
}

/* 学习进度 */
.learning-section {
  padding: 0 16px 16px;
}

.learning-progress {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.progress-item {
  margin-bottom: 12px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
  color: #374151;
}

.progress-value {
  color: #667eea;
  font-weight: 600;
}

.progress-stats {
  display: flex;
  justify-content: space-around;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.stat-label {
  font-size: 11px;
  color: #9ca3af;
}

/* 底部导航 */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  display: flex;
  justify-content: space-around;
  padding: 8px 0;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
  z-index: 100;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 10px;
  color: #9ca3af;
  cursor: pointer;
  padding: 4px 12px;
}

.nav-item.active {
  color: #667eea;
}

.nav-item :deep(.anticon) {
  font-size: 20px;
}

/* 学员详情 */
.student-detail {
  padding: 16px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.detail-info h3 {
  margin: 0 0 4px;
  font-size: 18px;
}

.detail-info p {
  margin: 0 0 8px;
  color: #6b7280;
  font-size: 14px;
}

.health-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.metric-item {
  background: #f9fafb;
  border-radius: 8px;
  padding: 12px;
}

.metric-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.followup-records {
  padding: 16px 0;
}

.record-item {
  padding: 4px 0;
}

.record-time {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 4px;
}

.record-content {
  font-size: 14px;
  color: #374151;
}

.detail-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: #fff;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
}
</style>
