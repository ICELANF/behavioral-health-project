<template>
  <div class="expert-portal">
    <!-- 顶部导航栏 -->
    <div class="portal-header">
      <div class="header-left">
        <span class="greeting">{{ getGreeting() }}，{{ expertInfo.name }}</span>
        <a-tag color="purple">督导专家</a-tag>
      </div>
      <div class="header-right">
        <a-badge :count="notifications" :offset="[-2, 2]">
          <BellOutlined class="header-icon" />
        </a-badge>
        <a-dropdown>
          <a-avatar :src="expertInfo.avatar" :size="36">
            {{ expertInfo.name?.charAt(0) }}
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

    <!-- 督导工作概览 -->
    <div class="overview-section">
      <div class="section-title">
        <DashboardOutlined /> 督导工作台
      </div>
      <div class="overview-cards">
        <div class="overview-card primary">
          <div class="card-icon"><TeamOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ overviewStats.coachesSupervised }}</div>
            <div class="card-label">带教教练</div>
          </div>
        </div>
        <div class="overview-card warning">
          <div class="card-icon"><AuditOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ overviewStats.pendingReviews }}</div>
            <div class="card-label">待审核</div>
          </div>
        </div>
        <div class="overview-card success">
          <div class="card-icon"><PlayCircleOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ overviewStats.upcomingLives }}</div>
            <div class="card-label">待直播</div>
          </div>
        </div>
        <div class="overview-card info">
          <div class="card-icon"><FileTextOutlined /></div>
          <div class="card-content">
            <div class="card-value">{{ overviewStats.casesToReview }}</div>
            <div class="card-label">案例待审</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 晋级审核 -->
    <div class="review-section">
      <div class="section-header">
        <div class="section-title">
          <AuditOutlined /> 晋级审核
        </div>
        <a class="view-all" @click="goToReviewList">全部申请 <RightOutlined /></a>
      </div>

      <div class="review-list">
        <div
          v-for="application in pendingApplications"
          :key="application.id"
          class="review-card"
        >
          <div class="review-header">
            <a-avatar :size="44" :src="application.avatar">
              {{ application.coachName?.charAt(0) }}
            </a-avatar>
            <div class="review-info">
              <div class="coach-name">{{ application.coachName }}</div>
              <div class="level-change">
                <a-tag :color="getLevelColor(application.currentLevel)">{{ application.currentLevel }}</a-tag>
                <span class="arrow">→</span>
                <a-tag :color="getLevelColor(application.targetLevel)">{{ application.targetLevel }}</a-tag>
              </div>
            </div>
            <div class="review-time">{{ application.appliedAt }}</div>
          </div>

          <div class="review-requirements">
            <div class="requirement-item" :class="{ met: application.requirements.courses }">
              <CheckCircleOutlined v-if="application.requirements.courses" />
              <CloseCircleOutlined v-else />
              <span>课程完成</span>
            </div>
            <div class="requirement-item" :class="{ met: application.requirements.exams }">
              <CheckCircleOutlined v-if="application.requirements.exams" />
              <CloseCircleOutlined v-else />
              <span>考试通过</span>
            </div>
            <div class="requirement-item" :class="{ met: application.requirements.cases }">
              <CheckCircleOutlined v-if="application.requirements.cases" />
              <CloseCircleOutlined v-else />
              <span>案例数量</span>
            </div>
            <div class="requirement-item" :class="{ met: application.requirements.mentoring }">
              <CheckCircleOutlined v-if="application.requirements.mentoring" />
              <CloseCircleOutlined v-else />
              <span>督导时长</span>
            </div>
          </div>

          <div class="review-actions">
            <a-button type="primary" @click="approveApplication(application)">通过</a-button>
            <a-button @click="rejectApplication(application)">拒绝</a-button>
            <a-button type="link" @click="viewApplicationDetail(application)">查看详情</a-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 带教教练 -->
    <div class="coaches-section">
      <div class="section-header">
        <div class="section-title">
          <TeamOutlined /> 带教教练
        </div>
        <a class="view-all" @click="goToCoachList">查看全部 <RightOutlined /></a>
      </div>

      <div class="coach-grid">
        <div
          v-for="coach in supervisedCoaches"
          :key="coach.id"
          class="coach-card"
          @click="openCoachDetail(coach)"
        >
          <a-avatar :size="52" :src="coach.avatar">
            {{ coach.name?.charAt(0) }}
          </a-avatar>
          <div class="coach-info">
            <div class="coach-name">{{ coach.name }}</div>
            <a-tag :color="getLevelColor(coach.level)" size="small">{{ coach.level }}</a-tag>
          </div>
          <div class="coach-stats">
            <div class="stat">
              <span class="stat-value">{{ coach.studentCount }}</span>
              <span class="stat-label">学员</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ coach.caseCount }}</span>
              <span class="stat-label">案例</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 直播培训 -->
    <div class="live-section">
      <div class="section-header">
        <div class="section-title">
          <PlayCircleOutlined /> 直播培训
        </div>
        <a class="view-all" @click="goToLiveList">全部直播 <RightOutlined /></a>
      </div>

      <div class="live-list">
        <div
          v-for="live in upcomingLives"
          :key="live.id"
          class="live-card"
        >
          <div class="live-cover" :style="{ backgroundImage: `url(${live.cover})` }">
            <div class="live-status" :class="live.status">
              {{ getStatusLabel(live.status) }}
            </div>
          </div>
          <div class="live-content">
            <div class="live-title">{{ live.title }}</div>
            <div class="live-meta">
              <span><CalendarOutlined /> {{ live.scheduledAt }}</span>
              <span><TeamOutlined /> {{ live.level }}</span>
            </div>
            <div class="live-actions">
              <a-button
                v-if="live.status === 'scheduled'"
                type="primary"
                size="small"
                @click="startLive(live)"
              >
                开始直播
              </a-button>
              <a-button
                v-else-if="live.status === 'live'"
                type="primary"
                danger
                size="small"
                @click="enterLive(live)"
              >
                进入直播间
              </a-button>
              <a-button size="small" @click="editLive(live)">编辑</a-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 案例评审 -->
    <div class="cases-section">
      <div class="section-header">
        <div class="section-title">
          <FileTextOutlined /> 案例评审
        </div>
        <a class="view-all">全部案例 <RightOutlined /></a>
      </div>

      <div class="case-list">
        <div
          v-for="caseItem in pendingCases"
          :key="caseItem.id"
          class="case-card"
        >
          <div class="case-header">
            <div class="case-info">
              <div class="case-title">{{ caseItem.title }}</div>
              <div class="case-meta">
                <span>提交人：{{ caseItem.coachName }}</span>
                <span>{{ caseItem.submittedAt }}</span>
              </div>
            </div>
            <a-tag :color="caseItem.type === 'success' ? 'green' : 'blue'">
              {{ caseItem.type === 'success' ? '成功案例' : '学习案例' }}
            </a-tag>
          </div>
          <div class="case-summary">{{ caseItem.summary }}</div>
          <div class="case-actions">
            <a-button type="primary" size="small" @click="reviewCase(caseItem)">评审</a-button>
            <a-button size="small" @click="viewCase(caseItem)">查看</a-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <div class="shortcuts-section">
      <div class="section-title">
        <AppstoreOutlined /> 快捷功能
      </div>
      <div class="shortcut-grid">
        <div class="shortcut-item" @click="goToReviewList">
          <div class="shortcut-icon review"><AuditOutlined /></div>
          <span>晋级审核</span>
        </div>
        <div class="shortcut-item" @click="goToLiveCreate">
          <div class="shortcut-icon live"><VideoCameraOutlined /></div>
          <span>创建直播</span>
        </div>
        <div class="shortcut-item" @click="goToCourseList">
          <div class="shortcut-icon course"><ReadOutlined /></div>
          <span>课程管理</span>
        </div>
        <div class="shortcut-item" @click="goToExamList">
          <div class="shortcut-icon exam"><SolutionOutlined /></div>
          <span>考试管理</span>
        </div>
        <div class="shortcut-item" @click="goToQuestionBank">
          <div class="shortcut-icon question"><FileTextOutlined /></div>
          <span>题库管理</span>
        </div>
        <div class="shortcut-item" @click="goToStats">
          <div class="shortcut-icon stats"><BarChartOutlined /></div>
          <span>数据统计</span>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="bottom-nav">
      <div class="nav-item active">
        <HomeOutlined />
        <span>工作台</span>
      </div>
      <div class="nav-item" @click="goToCoachList">
        <TeamOutlined />
        <span>教练</span>
      </div>
      <div class="nav-item" @click="goToLiveList">
        <PlayCircleOutlined />
        <span>直播</span>
      </div>
      <div class="nav-item" @click="goToMessages">
        <MessageOutlined />
        <span>消息</span>
      </div>
      <div class="nav-item" @click="goToProfile">
        <UserOutlined />
        <span>我的</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  BellOutlined,
  DashboardOutlined,
  TeamOutlined,
  AuditOutlined,
  PlayCircleOutlined,
  FileTextOutlined,
  RightOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CalendarOutlined,
  AppstoreOutlined,
  VideoCameraOutlined,
  ReadOutlined,
  SolutionOutlined,
  BarChartOutlined,
  HomeOutlined,
  MessageOutlined,
  UserOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

// 专家信息
const expertInfo = reactive({
  id: 'expert001',
  name: localStorage.getItem('admin_name') || '张专家',
  avatar: ''
})

const notifications = ref(5)

// 概览统计
const overviewStats = reactive({
  coachesSupervised: 12,
  pendingReviews: 3,
  upcomingLives: 2,
  casesToReview: 5
})

// 待审核申请
const pendingApplications = ref([
  {
    id: 'app001',
    coachName: '李教练',
    avatar: '',
    currentLevel: 'L1',
    targetLevel: 'L2',
    appliedAt: '2024-01-24',
    requirements: {
      courses: true,
      exams: true,
      cases: true,
      mentoring: false
    }
  },
  {
    id: 'app002',
    coachName: '王教练',
    avatar: '',
    currentLevel: 'L2',
    targetLevel: 'L3',
    appliedAt: '2024-01-23',
    requirements: {
      courses: true,
      exams: false,
      cases: true,
      mentoring: true
    }
  }
])

// 带教教练
const supervisedCoaches = ref([
  { id: 'c001', name: '李教练', avatar: '', level: 'L2', studentCount: 28, caseCount: 15 },
  { id: 'c002', name: '王教练', avatar: '', level: 'L1', studentCount: 18, caseCount: 8 },
  { id: 'c003', name: '张教练', avatar: '', level: 'L2', studentCount: 35, caseCount: 22 },
  { id: 'c004', name: '刘教练', avatar: '', level: 'L1', studentCount: 12, caseCount: 5 }
])

// 直播列表
const upcomingLives = ref([
  {
    id: 'live001',
    title: 'L2认证培训：糖尿病患者心理支持技巧',
    cover: 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=400',
    status: 'scheduled',
    scheduledAt: '2024-01-26 14:00',
    level: 'L2教练'
  },
  {
    id: 'live002',
    title: 'TTM模型在行为改变中的应用',
    cover: 'https://images.unsplash.com/photo-1559757175-5700dde675bc?w=400',
    status: 'live',
    scheduledAt: '进行中',
    level: '全体教练'
  }
])

// 待审案例
const pendingCases = ref([
  {
    id: 'case001',
    title: '高血糖患者成功逆转案例',
    coachName: '李教练',
    submittedAt: '2024-01-24',
    type: 'success',
    summary: '患者通过3个月的饮食和运动干预，成功将糖化血红蛋白从8.5%降至6.2%...'
  },
  {
    id: 'case002',
    title: '肥胖患者减重困难分析',
    coachName: '王教练',
    submittedAt: '2024-01-23',
    type: 'learning',
    summary: '患者多次尝试减重未成功，分析原因可能与情绪性进食有关...'
  }
])

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

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    scheduled: '未开始',
    live: '直播中',
    ended: '已结束'
  }
  return labels[status] || status
}

const approveApplication = (application: typeof pendingApplications.value[0]) => {
  Modal.confirm({
    title: '确认通过',
    content: `确定通过 ${application.coachName} 的 ${application.targetLevel} 晋级申请吗？`,
    onOk() {
      message.success('已通过晋级申请')
      pendingApplications.value = pendingApplications.value.filter(a => a.id !== application.id)
    }
  })
}

const rejectApplication = (application: typeof pendingApplications.value[0]) => {
  Modal.confirm({
    title: '确认拒绝',
    content: `确定拒绝 ${application.coachName} 的晋级申请吗？`,
    onOk() {
      message.info('已拒绝晋级申请')
      pendingApplications.value = pendingApplications.value.filter(a => a.id !== application.id)
    }
  })
}

const viewApplicationDetail = (application: typeof pendingApplications.value[0]) => {
  message.info(`查看 ${application.coachName} 的申请详情`)
}

const openCoachDetail = (coach: typeof supervisedCoaches.value[0]) => {
  router.push(`/coach/detail/${coach.id}`)
}

const startLive = (live: typeof upcomingLives.value[0]) => {
  message.info(`开始直播：${live.title}`)
}

const enterLive = (live: typeof upcomingLives.value[0]) => {
  message.info(`进入直播间：${live.title}`)
}

const editLive = (live: typeof upcomingLives.value[0]) => {
  router.push(`/live/edit/${live.id}`)
}

const reviewCase = (caseItem: typeof pendingCases.value[0]) => {
  message.info(`评审案例：${caseItem.title}`)
}

const viewCase = (caseItem: typeof pendingCases.value[0]) => {
  message.info(`查看案例：${caseItem.title}`)
}

// 导航
const goToReviewList = () => router.push('/coach/review')
const goToCoachList = () => router.push('/coach/list')
const goToLiveList = () => router.push('/live/list')
const goToLiveCreate = () => router.push('/live/create')
const goToCourseList = () => router.push('/course/list')
const goToExamList = () => router.push('/exam/list')
const goToQuestionBank = () => router.push('/question/bank')
const goToStats = () => router.push('/dashboard')
const goToMessages = () => message.info('消息中心')
const goToProfile = () => message.info('个人中心')

const handleLogout = () => {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_username')
  localStorage.removeItem('admin_role')
  localStorage.removeItem('admin_level')
  localStorage.removeItem('admin_name')
  router.push('/login')
}
</script>

<style scoped>
.expert-portal {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 70px;
}

/* 顶部导航 */
.portal-header {
  background: linear-gradient(135deg, #9333ea 0%, #7c3aed 100%);
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
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.overview-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.overview-card .card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.overview-card.primary .card-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.overview-card.warning .card-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
}

.overview-card.success .card-icon {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: #fff;
}

.overview-card.info .card-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #fff;
}

.card-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
}

.card-label {
  font-size: 13px;
  color: #6b7280;
}

/* 审核区域 */
.review-section {
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
  color: #9333ea;
  display: flex;
  align-items: center;
  gap: 4px;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.review-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.review-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.review-info {
  flex: 1;
}

.coach-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.level-change {
  display: flex;
  align-items: center;
  gap: 6px;
}

.arrow {
  color: #9ca3af;
}

.review-time {
  font-size: 12px;
  color: #9ca3af;
}

.review-requirements {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
}

.requirement-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #9ca3af;
}

.requirement-item.met {
  color: #52c41a;
}

.requirement-item :deep(.anticon) {
  font-size: 14px;
}

.review-actions {
  display: flex;
  gap: 8px;
}

/* 教练网格 */
.coaches-section {
  padding: 0 16px 16px;
}

.coach-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.coach-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: transform 0.2s;
}

.coach-card:active {
  transform: scale(0.98);
}

.coach-info {
  margin: 10px 0;
}

.coach-info .coach-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.coach-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
}

.stat-label {
  font-size: 11px;
  color: #9ca3af;
}

/* 直播区域 */
.live-section {
  padding: 0 16px 16px;
}

.live-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.live-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.live-cover {
  height: 120px;
  background-size: cover;
  background-position: center;
  position: relative;
}

.live-status {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.live-status.scheduled {
  background: rgba(0,0,0,0.6);
  color: #fff;
}

.live-status.live {
  background: #f5222d;
  color: #fff;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.live-content {
  padding: 12px;
}

.live-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.live-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 12px;
}

.live-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.live-actions {
  display: flex;
  gap: 8px;
}

/* 案例区域 */
.cases-section {
  padding: 0 16px 16px;
}

.case-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.case-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.case-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.case-meta {
  font-size: 12px;
  color: #9ca3af;
  display: flex;
  gap: 12px;
}

.case-summary {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.case-actions {
  display: flex;
  gap: 8px;
}

/* 快捷入口 */
.shortcuts-section {
  padding: 0 16px 16px;
}

.shortcut-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.shortcut-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: transform 0.2s;
}

.shortcut-item:active {
  transform: scale(0.95);
}

.shortcut-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  margin: 0 auto 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.shortcut-icon.review { background: #f3e8ff; color: #9333ea; }
.shortcut-icon.live { background: #fef3c7; color: #d97706; }
.shortcut-icon.course { background: #dcfce7; color: #16a34a; }
.shortcut-icon.exam { background: #e0f2fe; color: #0369a1; }
.shortcut-icon.question { background: #fce7f3; color: #db2777; }
.shortcut-icon.stats { background: #e0e7ff; color: #4f46e5; }

.shortcut-item span {
  font-size: 12px;
  color: #374151;
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
  color: #9333ea;
}

.nav-item :deep(.anticon) {
  font-size: 20px;
}
</style>
