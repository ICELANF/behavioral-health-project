<template>
  <div class="client-app">
    <!-- 顶部渐变背景区域 -->
    <div class="header-section">
      <div class="header-content">
        <div class="greeting-row">
          <div class="greeting-text">
            <div class="greeting-time">{{ greetingText }}</div>
            <div class="user-name">{{ userName }} 👋</div>
          </div>
          <a-avatar :size="56" class="user-avatar">
            <template #icon><UserOutlined /></template>
          </a-avatar>
        </div>

        <!-- 健康评分卡片 -->
        <div class="health-score-card">
          <div class="score-left">
            <div class="score-circle">
              <a-progress
                type="circle"
                :percent="healthScore"
                :size="80"
                :stroke-color="{ '0%': '#667eea', '100%': '#764ba2' }"
                :stroke-width="8"
              >
                <template #format="percent">
                  <span class="score-number">{{ percent }}</span>
                </template>
              </a-progress>
            </div>
            <div class="score-info">
              <div class="score-label">健康评分</div>
              <div class="score-status">{{ healthStatus }}</div>
            </div>
          </div>
          <div class="score-right">
            <div class="score-detail">
              <span class="detail-icon">🔥</span>
              <span class="detail-text">连续打卡 <strong>{{ streakDays }}</strong> 天</span>
            </div>
            <div class="score-detail">
              <span class="detail-icon">⭐</span>
              <span class="detail-text">获得 <strong>{{ totalPoints }}</strong> 积分</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 关注领域选择 -->
      <div class="section-card focus-card">
        <div class="card-header">
          <span class="card-title">🎯 我关注的领域</span>
          <a class="edit-link" @click="showFocusModal = true">编辑</a>
        </div>
        <div class="focus-tags">
          <div
            v-for="area in userFocusAreas"
            :key="area"
            class="focus-tag"
            :style="{ background: getFocusAreaStyle(area).bg, color: getFocusAreaStyle(area).color }"
          >
            <span class="tag-icon">{{ getFocusAreaStyle(area).icon }}</span>
            <span>{{ getFocusAreaStyle(area).label }}</span>
          </div>
        </div>
      </div>

      <!-- 每日提示 -->
      <div class="section-card daily-tip-card" v-if="recommendations.dailyTip">
        <div class="daily-tip-content">
          <div class="tip-icon-large">{{ recommendations.dailyTip.icon }}</div>
          <div class="tip-body">
            <div class="tip-title">{{ recommendations.dailyTip.title }}</div>
            <div class="tip-text">{{ recommendations.dailyTip.content }}</div>
          </div>
        </div>
      </div>

      <!-- 健康指标卡片组 -->
      <div class="metrics-grid">
        <div class="metric-card glucose" @click="goToDetail('glucose')">
          <div class="metric-icon">🩸</div>
          <div class="metric-info">
            <div class="metric-value">{{ bloodGlucose.fasting || '--' }}</div>
            <div class="metric-label">空腹血糖</div>
          </div>
          <div class="metric-trend" :class="bloodGlucose.trend">
            <component :is="getTrendIcon(bloodGlucose.trend)" />
          </div>
        </div>
        <div class="metric-card weight" @click="goToDetail('weight')">
          <div class="metric-icon">⚖️</div>
          <div class="metric-info">
            <div class="metric-value">{{ weight.current || '--' }}</div>
            <div class="metric-label">当前体重</div>
          </div>
          <div class="metric-trend" :class="weight.trend">
            <component :is="getTrendIcon(weight.trend)" />
          </div>
        </div>
        <div class="metric-card exercise" @click="goToDetail('exercise')">
          <div class="metric-icon">🏃</div>
          <div class="metric-info">
            <div class="metric-value">{{ exercise.weeklyMinutes }}</div>
            <div class="metric-label">本周运动</div>
          </div>
          <a-progress
            :percent="Math.min(100, (exercise.weeklyMinutes / exercise.targetMinutes) * 100)"
            :show-info="false"
            :stroke-color="'#10b981'"
            size="small"
            class="metric-progress"
          />
        </div>
        <div class="metric-card medication" @click="goToDetail('medication')">
          <div class="metric-icon">💊</div>
          <div class="metric-info">
            <div class="metric-value">{{ medication.adherenceRate }}%</div>
            <div class="metric-label">用药提醒</div>
          </div>
          <a-progress
            :percent="medication.adherenceRate"
            :show-info="false"
            :stroke-color="medication.adherenceRate >= 90 ? '#10b981' : '#f59e0b'"
            size="small"
            class="metric-progress"
          />
        </div>
      </div>

      <!-- 今日任务 -->
      <div class="section-card tasks-card">
        <div class="card-header">
          <span class="card-title">📋 今日任务</span>
          <span class="task-count">{{ completedTasksCount }}/{{ todayTasks.length }}</span>
        </div>
        <div class="tasks-list">
          <div
            v-for="task in todayTasks"
            :key="task.id"
            class="task-item"
            :class="{ completed: task.completed }"
            @click="toggleTask(task)"
          >
            <div class="task-checkbox">
              <div class="checkbox-inner" :class="{ checked: task.completed }">
                <CheckOutlined v-if="task.completed" />
              </div>
            </div>
            <div class="task-content">
              <div class="task-name">{{ task.name }}</div>
              <div class="task-desc">{{ task.description }}</div>
            </div>
            <div class="task-priority">
              <span v-if="task.priority === 'high'">🔴</span>
              <span v-else-if="task.priority === 'medium'">🟡</span>
              <span v-else>🟢</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 推荐视频 -->
      <div class="section-card" v-if="recommendations.videos.length">
        <div class="card-header">
          <span class="card-title">🎬 推荐视频</span>
          <a class="more-link" @click="router.push('/client/learning-progress')">更多 ›</a>
        </div>
        <div class="video-scroll">
          <div
            v-for="video in recommendations.videos"
            :key="video.id"
            class="video-card"
            @click="openVideo(video)"
          >
            <div class="video-thumbnail">
              <img :src="video.thumbnail" :alt="video.title" />
              <div class="video-duration">{{ formatDuration(video.duration) }}</div>
              <div class="video-play-btn">
                <PlayCircleOutlined />
              </div>
            </div>
            <div class="video-info">
              <div class="video-title">{{ video.title }}</div>
              <div class="video-meta">
                <span>{{ video.instructor }}</span>
                <span>{{ formatViews(video.views) }}次观看</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 推荐课程 -->
      <div class="section-card" v-if="recommendations.courses.length">
        <div class="card-header">
          <span class="card-title">📚 精选课程</span>
          <a class="more-link" @click="router.push('/client/learning-progress')">更多 ›</a>
        </div>
        <div class="course-list">
          <div
            v-for="course in recommendations.courses"
            :key="course.id"
            class="course-card"
            @click="openCourse(course)"
          >
            <div class="course-cover">
              <img :src="course.cover" :alt="course.title" />
              <div class="course-badge" v-if="course.isFree">免费</div>
            </div>
            <div class="course-info">
              <div class="course-title">{{ course.title }}</div>
              <div class="course-meta">
                <a-avatar :size="20" :src="course.instructorAvatar" />
                <span>{{ course.instructor }}</span>
              </div>
              <div class="course-stats">
                <span class="course-rating">
                  <StarFilled style="color: #fbbf24" />
                  {{ course.rating }}
                </span>
                <span class="course-enroll">{{ formatNumber(course.enrollCount) }}人学习</span>
              </div>
              <div class="course-price" v-if="!course.isFree">
                ¥{{ course.price }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 教练行为推荐 -->
      <div class="section-card coach-section" v-if="recommendations.coachActions.length">
        <div class="card-header">
          <span class="card-title">👨‍⚕️ 教练指导</span>
          <a class="more-link" @click="router.push('/client/my/profile')">预约教练 ›</a>
        </div>
        <div class="coach-actions">
          <div
            v-for="action in recommendations.coachActions"
            :key="action.id"
            class="coach-action-card"
            @click="openCoachAction(action)"
          >
            <div class="action-header">
              <div class="action-category" :class="action.category">
                {{ getCategoryIcon(action.category) }}
              </div>
              <div class="action-info">
                <div class="action-title">{{ action.title }}</div>
                <div class="action-desc">{{ action.description }}</div>
              </div>
            </div>
            <div class="action-footer">
              <span class="action-duration">
                <ClockCircleOutlined /> {{ action.expectedDuration }}分钟
              </span>
              <span class="action-difficulty" :class="action.difficulty">
                {{ getDifficultyLabel(action.difficulty) }}
              </span>
            </div>
          </div>
        </div>
      </div>


      <!-- AI 助手入口 -->
      <div class="section-card ai-card">
        <div class="ai-header">
          <div class="ai-avatar">🤖</div>
          <div class="ai-intro">
            <div class="ai-title">AI 健康助手</div>
            <div class="ai-subtitle">有问题随时问我</div>
          </div>
        </div>
        <div class="ai-buttons">
          <div class="ai-btn primary" @click="startChat('A1')">
            <span class="btn-icon">💬</span>
            <span class="btn-label">健康咨询</span>
          </div>
          <div class="ai-btn" @click="startChat('A3')">
            <span class="btn-icon">🥗</span>
            <span class="btn-label">饮食指导</span>
          </div>
          <div class="ai-btn" @click="startChat('A2')">
            <span class="btn-icon">🏋️</span>
            <span class="btn-label">运动计划</span>
          </div>
          <div class="ai-btn" @click="startChat('A4')">
            <span class="btn-icon">🧘</span>
            <span class="btn-label">心理支持</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="bottom-nav">
      <div class="nav-item active">
        <HomeOutlined />
        <span>首页</span>
      </div>
      <div class="nav-item" @click="router.push('/client/device-dashboard')">
        <LineChartOutlined />
        <span>数据</span>
      </div>
      <div class="nav-item center-btn" @click="router.push('/client/chat')">
        <div class="center-icon">
          <MessageOutlined />
        </div>
      </div>
      <div class="nav-item" @click="router.push('/client/learning-progress')">
        <ReadOutlined />
        <span>学习</span>
      </div>
      <div class="nav-item" @click="router.push('/client/my/profile')">
        <UserOutlined />
        <span>我的</span>
      </div>
    </div>

    <!-- 用药提醒抽屉 -->
    <a-drawer
      v-model:open="showMedDrawer"
      title="💊 用药提醒"
      placement="bottom"
      :height="'85vh'"
      class="med-drawer"
    >
      <div style="max-width:500px;margin:0 auto">
        <!-- 今日用药打卡 -->
        <div class="med-section">
          <h4 style="margin-bottom:12px;font-size:16px">📋 今日用药打卡</h4>
          <div v-for="med in medReminders" :key="med.id" class="med-item" :class="{taken: med.taken}" @click="toggleMedTaken(med)">
            <div class="med-check">
              <div class="med-checkbox" :class="{checked: med.taken}">
                <CheckOutlined v-if="med.taken" />
              </div>
            </div>
            <div class="med-info">
              <div class="med-name">{{ med.name }} <span class="med-dosage">{{ med.dosage }}</span></div>
              <div class="med-time">⏰ {{ med.time }} · {{ med.frequency }}</div>
            </div>
          </div>
        </div>

        <!-- 药物说明 -->
        <div class="med-section">
          <h4 style="margin-bottom:12px;font-size:16px">💡 药物功能说明</h4>
          <div v-for="med in medReminders" :key="'info-'+med.id" class="drug-info-card">
            <div class="drug-header">
              <span class="drug-name">{{ med.name }}</span>
              <span class="drug-dose">{{ med.dosage }} / {{ med.frequency }}</span>
            </div>
            <div class="drug-note">{{ med.notes }}</div>
          </div>
        </div>

        <!-- 注意事项 -->
        <div class="med-section">
          <h4 style="margin-bottom:12px;font-size:16px">⚠️ 用药注意事项</h4>
          <div v-for="(p, i) in medPrecautions" :key="i" class="precaution-item">
            <div class="precaution-icon">{{ p.icon }}</div>
            <div class="precaution-body">
              <div class="precaution-title">{{ p.title }}</div>
              <div class="precaution-desc">{{ p.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </a-drawer>

    <!-- 关注领域编辑弹窗 -->
    <a-modal
      v-model:open="showFocusModal"
      title="选择关注领域"
      @ok="saveFocusAreas"
      ok-text="保存"
      cancel-text="取消"
    >
      <div class="focus-select-grid">
        <div
          v-for="(config, key) in TRIGGER_DOMAINS"
          :key="key"
          class="focus-select-item"
          :class="{ selected: tempFocusAreas.includes(key as FocusArea) }"
          @click="toggleFocusArea(key as FocusArea)"
        >
          <span class="focus-icon">{{ getFocusAreaStyle(key as FocusArea).icon }}</span>
          <span class="focus-label">{{ config.label }}</span>
          <CheckOutlined v-if="tempFocusAreas.includes(key as FocusArea)" class="check-icon" />
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  UserOutlined,
  CheckOutlined,
  HomeOutlined,
  LineChartOutlined,
  MessageOutlined,
  ReadOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
  PlayCircleOutlined,
  StarFilled,
  ClockCircleOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { BEHAVIOR_STAGE_MAP, AGENT_TYPE_MAP, TRIGGER_DOMAINS } from '@/constants/index'
import { getPatientDashboard, updateTaskStatus, getHealthSummary, type Task } from '@/api/client'
import {
  getRecommendations,
  getUserFocusAreas,
  updateUserFocusAreas,
  trackRecommendationClick,
  type FocusArea,
  type RecommendationResult,
  type RecommendedVideo,
  type RecommendedCourse,
  type RecommendedProduct,
  type RecommendedCoachAction
} from '@/api/recommendation'

// 路由
const router = useRouter()

// 用户信息
const userName = ref('小明')
const healthScore = ref(78)
const streakDays = ref(7)
const totalPoints = ref(1280)

// 问候语
const greetingText = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了，注意休息'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了，注意休息'
})

const healthStatus = computed(() => {
  if (healthScore.value >= 90) return '非常棒！继续保持'
  if (healthScore.value >= 70) return '状态良好，再接再厉'
  if (healthScore.value >= 50) return '还需努力，加油哦'
  return '需要关注，一起加油'
})

// 行为阶段
const currentStageKey = ref<keyof typeof BEHAVIOR_STAGE_MAP>('preparation')

// 健康指标
const bloodGlucose = ref({ fasting: 6.8, postprandial: 9.2, trend: 'down' as const })
const weight = ref({ current: 75.5, target: 70, trend: 'down' as const })
const exercise = ref({ weeklyMinutes: 120, targetMinutes: 150, streak: 7 })
const medication = ref({ adherenceRate: 92, missedDoses: 2 })

const getTrendIcon = (trend: string) => {
  if (trend === 'up') return ArrowUpOutlined
  if (trend === 'down') return ArrowDownOutlined
  return MinusOutlined
}

// 今日任务
const todayTasks = ref<Task[]>([])
const completedTasksCount = computed(() => todayTasks.value.filter(t => t.completed).length)

const toggleTask = async (task: Task) => {
  task.completed = !task.completed
  await updateTaskStatus(task.id, task.completed)
  if (task.completed) {
    message.success({ content: '🎉 任务完成 +10积分', duration: 2 })
    totalPoints.value += 10
  }
}

// 关注领域
const userFocusAreas = ref<FocusArea[]>(['glucose', 'diet', 'exercise'])
const showFocusModal = ref(false)
const tempFocusAreas = ref<FocusArea[]>([])

const focusAreaStyles: Record<FocusArea, { icon: string; label: string; bg: string; color: string }> = {
  glucose: { icon: '🩸', label: '血糖管理', bg: '#fef2f2', color: '#dc2626' },
  diet: { icon: '🥗', label: '饮食控制', bg: '#f0fdf4', color: '#16a34a' },
  exercise: { icon: '🏃', label: '运动锻炼', bg: '#eff6ff', color: '#2563eb' },
  medication: { icon: '💊', label: '用药提醒', bg: '#faf5ff', color: '#9333ea' },
  sleep: { icon: '😴', label: '睡眠质量', bg: '#ecfeff', color: '#0891b2' },
  stress: { icon: '🧘', label: '压力管理', bg: '#fdf4ff', color: '#c026d3' },
  weight: { icon: '⚖️', label: '体重控制', bg: '#fffbeb', color: '#d97706' }
}

const getFocusAreaStyle = (area: FocusArea) => focusAreaStyles[area] || focusAreaStyles.glucose

const toggleFocusArea = (area: FocusArea) => {
  const index = tempFocusAreas.value.indexOf(area)
  if (index >= 0) {
    tempFocusAreas.value.splice(index, 1)
  } else {
    if (tempFocusAreas.value.length < 5) {
      tempFocusAreas.value.push(area)
    } else {
      message.warning('最多选择5个关注领域')
    }
  }
}

const saveFocusAreas = async () => {
  if (tempFocusAreas.value.length === 0) {
    message.warning('请至少选择一个关注领域')
    return
  }
  userFocusAreas.value = [...tempFocusAreas.value]
  await updateUserFocusAreas(tempFocusAreas.value)
  showFocusModal.value = false
  // 重新获取推荐
  await loadRecommendations()
  message.success('关注领域已更新')
}

// 推荐数据
const recommendations = ref<RecommendationResult>({
  userStage: 'preparation',
  focusAreas: [],
  videos: [],
  products: [],
  courses: [],
  coachActions: [],
  dailyTip: { icon: '💪', title: '', content: '' }
})

const loadRecommendations = async () => {
  const result = await getRecommendations(currentStageKey.value, userFocusAreas.value)
  recommendations.value = result
}

// 格式化函数
const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatViews = (views: number) => {
  if (views >= 10000) return `${(views / 10000).toFixed(1)}万`
  if (views >= 1000) return `${(views / 1000).toFixed(1)}k`
  return views.toString()
}

const formatNumber = (num: number) => {
  if (num >= 10000) return `${(num / 10000).toFixed(1)}万`
  return num.toString()
}

const getCategoryIcon = (category: string) => {
  const icons: Record<string, string> = {
    education: '📖',
    guidance: '🎯',
    coaching: '💪',
    support: '❤️'
  }
  return icons[category] || '📋'
}

const getDifficultyLabel = (difficulty: string) => {
  const labels: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '进阶'
  }
  return labels[difficulty] || difficulty
}

// 点击事件
const openVideo = (video: RecommendedVideo) => {
  trackRecommendationClick('video', video.id)
  message.success(`正在播放: ${video.title}`)
}

const openCourse = (course: RecommendedCourse) => {
  trackRecommendationClick('course', course.id)
  message.success(`正在打开课程: ${course.title}`)
}

const openProduct = (product: RecommendedProduct) => {
  trackRecommendationClick('product', product.id)
  message.success(`正在查看: ${product.name}`)
}

const openCoachAction = (action: RecommendedCoachAction) => {
  trackRecommendationClick('coachAction', action.id)
  message.success(`已预约: ${action.title}`)
}

// 用药提醒
const showMedDrawer = ref(false)
const medReminders = ref([
  { id: 1, name: '二甲双胍', dosage: '500mg', time: '08:00', frequency: '每日2次（早/晚餐后）', taken: false, notes: '餐后服用，避免空腹；如出现胃肠不适可随餐服用' },
  { id: 2, name: '格列美脲', dosage: '2mg', time: '07:30', frequency: '每日1次（早餐前）', taken: true, notes: '早餐前15分钟服用；注意低血糖风险，随身携带糖果' },
  { id: 3, name: '阿卡波糖', dosage: '50mg', time: '12:00', frequency: '每日3次（随餐）', taken: false, notes: '与第一口饭同时嚼服；可能引起腹胀、排气增多' },
])
const medPrecautions = [
  { icon: '⏰', title: '按时服药', desc: '设定闹钟提醒，固定时间服药，不要随意更改服药时间' },
  { icon: '🚫', title: '不可自行停药', desc: '即使血糖正常也不要自行停药或减量，需遵医嘱调整' },
  { icon: '🍺', title: '避免饮酒', desc: '服药期间避免饮酒，酒精可能加重低血糖风险' },
  { icon: '📋', title: '记录不良反应', desc: '如出现恶心、腹泻、头晕等不适，及时记录并告知医生' },
  { icon: '💊', title: '勿与部分食物同服', desc: '避免与柚子汁同服；二甲双胍避免与含碘造影剂同用' },
  { icon: '🔄', title: '定期复查', desc: '每1-3个月复查糖化血红蛋白和肝肾功能' },
]
const toggleMedTaken = (med: typeof medReminders.value[0]) => {
  med.taken = !med.taken
  if (med.taken) message.success(`${med.name} 已打卡服药 ✓`)
}

const goToDetail = (type: string) => {
  if (type === 'medication') {
    showMedDrawer.value = true
    return
  }
  message.success(`正在加载${type}详情...`)
}

const startChat = (agentType: keyof typeof AGENT_TYPE_MAP) => {
  router.push({ path: '/client/chat', query: { agent: agentType } })
}

const handleLogout = () => {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_username')
  localStorage.removeItem('admin_role')
  localStorage.removeItem('admin_level')
  localStorage.removeItem('admin_name')
  router.push('/login')
}

// 刷新健康数据
const refreshHealth = async () => {
  const health = await getHealthSummary()
  if (health) {
    bloodGlucose.value = health.bloodGlucose
    weight.value = health.weight
    exercise.value = health.exercise
    medication.value = health.medication
  }
}

// 定时刷新
let refreshTimer: ReturnType<typeof setInterval> | null = null

// 初始化
onMounted(async () => {
  // 加载用户关注领域
  const areas = await getUserFocusAreas()
  userFocusAreas.value = areas
  tempFocusAreas.value = [...areas]

  // 加载仪表盘数据
  const dashboard = await getPatientDashboard()
  if (dashboard) {
    currentStageKey.value = dashboard.currentBehaviorStage
    todayTasks.value = dashboard.todayTasks
  }

  // 加载健康数据
  await refreshHealth()

  // 加载推荐
  await loadRecommendations()

  // 每10秒自动刷新健康指标
  refreshTimer = setInterval(refreshHealth, 10000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.client-app {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 90px;
}

/* 顶部区域 */
.header-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px 16px 50px;
  border-radius: 0 0 24px 24px;
}

.header-content {
  max-width: 500px;
  margin: 0 auto;
}

.greeting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.greeting-time { color: rgba(255,255,255,0.8); font-size: 14px; }
.user-name { color: #fff; font-size: 24px; font-weight: 600; margin-top: 4px; }
.user-avatar { background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.5); }

.health-score-card {
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-left { display: flex; align-items: center; gap: 16px; }
.score-number { font-size: 24px; font-weight: 700; color: #fff; }
.score-label { color: rgba(255,255,255,0.8); font-size: 12px; }
.score-status { color: #fff; font-size: 14px; font-weight: 500; margin-top: 2px; }
.score-right { display: flex; flex-direction: column; gap: 8px; }
.score-detail { display: flex; align-items: center; gap: 6px; color: rgba(255,255,255,0.9); font-size: 13px; }
.detail-icon { font-size: 16px; }

/* 主内容区域 */
.main-content {
  max-width: 500px;
  margin: -30px auto 0;
  padding: 0 16px;
  position: relative;
  z-index: 10;
}

.section-card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title { font-size: 16px; font-weight: 600; color: #1f2937; }
.edit-link, .more-link { color: #667eea; font-size: 13px; cursor: pointer; }

/* 关注领域 */
.focus-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.focus-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}
.tag-icon { font-size: 14px; }

/* 每日提示 */
.daily-tip-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}
.daily-tip-content { display: flex; gap: 12px; align-items: flex-start; }
.tip-icon-large { font-size: 36px; }
.tip-title { font-size: 15px; font-weight: 600; margin-bottom: 4px; }
.tip-text { font-size: 13px; opacity: 0.9; line-height: 1.5; }

/* 指标卡片 */
.metrics-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
.metric-card {
  background: #fff;
  border-radius: 16px;
  padding: 14px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
}
.metric-card:hover { transform: translateY(-2px); }
.metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.metric-card.glucose::before { background: linear-gradient(90deg, #ef4444, #f87171); }
.metric-card.weight::before { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.metric-card.exercise::before { background: linear-gradient(90deg, #10b981, #34d399); }
.metric-card.medication::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.metric-icon { font-size: 24px; margin-bottom: 8px; }
.metric-value { font-size: 24px; font-weight: 700; color: #1f2937; }
.metric-label { font-size: 12px; color: #6b7280; margin-top: 2px; }
.metric-trend {
  position: absolute; top: 12px; right: 12px;
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 12px;
}
.metric-trend.down { background: #dcfce7; color: #16a34a; }
.metric-trend.up { background: #fee2e2; color: #dc2626; }
.metric-trend.stable { background: #f3f4f6; color: #6b7280; }
.metric-progress { margin-top: 8px; }

/* 任务列表 */
.task-count { background: #f3f4f6; padding: 4px 10px; border-radius: 12px; font-size: 12px; color: #6b7280; }
.tasks-list { display: flex; flex-direction: column; gap: 10px; }
.task-item {
  display: flex; align-items: center; gap: 12px; padding: 12px;
  background: #f9fafb; border-radius: 12px; cursor: pointer; transition: all 0.2s;
}
.task-item:hover { background: #f3f4f6; }
.task-item.completed { opacity: 0.6; }
.checkbox-inner {
  width: 22px; height: 22px; border: 2px solid #d1d5db; border-radius: 6px;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.checkbox-inner.checked { background: #10b981; border-color: #10b981; color: #fff; }
.task-content { flex: 1; min-width: 0; }
.task-name { font-size: 14px; font-weight: 500; color: #1f2937; }
.task-item.completed .task-name { text-decoration: line-through; color: #9ca3af; }
.task-desc { font-size: 12px; color: #6b7280; margin-top: 2px; }

/* 视频列表 */
.video-scroll { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.video-scroll::-webkit-scrollbar { height: 4px; }
.video-scroll::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
.video-card { flex-shrink: 0; width: 200px; cursor: pointer; }
.video-thumbnail {
  position: relative; border-radius: 12px; overflow: hidden;
  aspect-ratio: 16/9; background: #f3f4f6;
}
.video-thumbnail img { width: 100%; height: 100%; object-fit: cover; }
.video-duration {
  position: absolute; bottom: 8px; right: 8px;
  background: rgba(0,0,0,0.7); color: #fff;
  padding: 2px 6px; border-radius: 4px; font-size: 11px;
}
.video-play-btn {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  color: #fff; font-size: 32px; opacity: 0.9;
}
.video-info { padding: 8px 0; }
.video-title { font-size: 13px; font-weight: 500; color: #1f2937; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.video-meta { font-size: 11px; color: #9ca3af; margin-top: 4px; display: flex; gap: 8px; }

/* 课程列表 */
.course-list { display: flex; flex-direction: column; gap: 12px; }
.course-card { display: flex; gap: 12px; cursor: pointer; padding: 8px; border-radius: 12px; transition: background 0.2s; }
.course-card:hover { background: #f9fafb; }
.course-cover { flex-shrink: 0; width: 100px; height: 70px; border-radius: 8px; overflow: hidden; position: relative; }
.course-cover img { width: 100%; height: 100%; object-fit: cover; }
.course-badge { position: absolute; top: 4px; left: 4px; background: #ef4444; color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 4px; }
.course-info { flex: 1; min-width: 0; }
.course-title { font-size: 14px; font-weight: 500; color: #1f2937; margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
.course-meta { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6b7280; margin-bottom: 4px; }
.course-stats { display: flex; gap: 12px; font-size: 12px; color: #6b7280; }
.course-rating { display: flex; align-items: center; gap: 2px; }
.course-price { font-size: 14px; font-weight: 600; color: #ef4444; margin-top: 4px; }

/* 教练行为 */
.coach-actions { display: flex; flex-direction: column; gap: 10px; }
.coach-action-card {
  padding: 12px; background: #f9fafb; border-radius: 12px;
  cursor: pointer; transition: all 0.2s;
}
.coach-action-card:hover { background: #f3f4f6; transform: translateX(4px); }
.action-header { display: flex; gap: 12px; margin-bottom: 8px; }
.action-category { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.action-category.education { background: #dbeafe; }
.action-category.guidance { background: #fef3c7; }
.action-category.coaching { background: #dcfce7; }
.action-category.support { background: #fce7f3; }
.action-title { font-size: 14px; font-weight: 500; color: #1f2937; }
.action-desc { font-size: 12px; color: #6b7280; margin-top: 2px; }
.action-footer { display: flex; justify-content: space-between; align-items: center; }
.action-duration { font-size: 12px; color: #6b7280; display: flex; align-items: center; gap: 4px; }
.action-difficulty { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.action-difficulty.easy { background: #dcfce7; color: #16a34a; }
.action-difficulty.medium { background: #fef3c7; color: #d97706; }
.action-difficulty.hard { background: #fee2e2; color: #dc2626; }

/* 产品网格 */
.product-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.product-card { cursor: pointer; transition: transform 0.2s; }
.product-card:hover { transform: translateY(-2px); }
.product-image { position: relative; border-radius: 12px; overflow: hidden; aspect-ratio: 1; background: #f3f4f6; }
.product-image img { width: 100%; height: 100%; object-fit: cover; }
.product-tags { position: absolute; top: 8px; left: 8px; display: flex; gap: 4px; }
.product-tag { background: #ef4444; color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 4px; }
.product-info { padding: 8px 0; }
.product-name { font-size: 13px; font-weight: 500; color: #1f2937; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.product-price-row { display: flex; align-items: baseline; gap: 6px; margin-top: 4px; }
.product-price { font-size: 16px; font-weight: 600; color: #ef4444; }
.product-original { font-size: 12px; color: #9ca3af; text-decoration: line-through; }
.product-rating { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #6b7280; margin-top: 4px; }
.product-sales { margin-left: auto; }

/* AI 助手 */
.ai-card { background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: #fff; }
.ai-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.ai-avatar { font-size: 36px; }
.ai-title { font-size: 16px; font-weight: 600; }
.ai-subtitle { font-size: 12px; color: rgba(255,255,255,0.7); margin-top: 2px; }
.ai-buttons { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.ai-btn {
  background: rgba(255,255,255,0.1); border-radius: 12px; padding: 12px 8px;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  cursor: pointer; transition: all 0.2s;
}
.ai-btn:hover { background: rgba(255,255,255,0.15); transform: translateY(-2px); }
.ai-btn.primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.btn-icon { font-size: 24px; }
.btn-label { font-size: 11px; }

/* 底部导航 */
.bottom-nav {
  position: fixed; bottom: 0; left: 0; right: 0; background: #fff;
  display: flex; justify-content: space-around; align-items: center;
  padding: 8px 0 20px; box-shadow: 0 -2px 12px rgba(0,0,0,0.08); z-index: 100;
}
.nav-item { display: flex; flex-direction: column; align-items: center; gap: 4px; color: #9ca3af; font-size: 10px; cursor: pointer; }
.nav-item.active { color: #667eea; }
.nav-item :deep(.anticon) { font-size: 22px; }
.nav-item.center-btn { margin-top: -20px; }
.center-icon {
  width: 50px; height: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  color: #fff; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
.center-icon :deep(.anticon) { font-size: 24px; }

/* 关注领域选择弹窗 */
.focus-select-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.focus-select-item {
  display: flex; align-items: center; gap: 8px; padding: 12px;
  border: 2px solid #e5e7eb; border-radius: 12px; cursor: pointer; transition: all 0.2s;
}
.focus-select-item:hover { border-color: #667eea; }
.focus-select-item.selected { border-color: #667eea; background: #f0f5ff; }
.focus-icon { font-size: 24px; }
.focus-label { flex: 1; font-size: 14px; }
.check-icon { color: #667eea; }

:deep(.ant-progress-circle .ant-progress-text) { color: #fff !important; }

/* 用药提醒抽屉 */
.med-section { margin-bottom: 24px; }
.med-item {
  display: flex; align-items: center; gap: 12px; padding: 14px;
  background: #f9fafb; border-radius: 12px; margin-bottom: 10px; cursor: pointer; transition: all 0.2s;
}
.med-item:hover { background: #f3f4f6; }
.med-item.taken { opacity: 0.6; }
.med-checkbox {
  width: 24px; height: 24px; border: 2px solid #d1d5db; border-radius: 6px;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.med-checkbox.checked { background: #10b981; border-color: #10b981; color: #fff; }
.med-info { flex: 1; }
.med-name { font-weight: 600; font-size: 15px; color: #1f2937; }
.med-dosage { font-weight: 400; font-size: 13px; color: #6b7280; margin-left: 6px; }
.med-time { font-size: 12px; color: #6b7280; margin-top: 4px; }
.drug-info-card {
  background: #f0f5ff; border-radius: 12px; padding: 14px; margin-bottom: 10px;
  border-left: 4px solid #667eea;
}
.drug-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.drug-name { font-weight: 600; font-size: 15px; color: #1f2937; }
.drug-dose { font-size: 12px; color: #667eea; background: #e0e7ff; padding: 2px 8px; border-radius: 10px; }
.drug-note { font-size: 13px; color: #4b5563; line-height: 1.6; }
.precaution-item {
  display: flex; gap: 12px; padding: 12px; background: #fffbeb; border-radius: 12px; margin-bottom: 10px;
}
.precaution-icon { font-size: 24px; flex-shrink: 0; }
.precaution-title { font-weight: 600; font-size: 14px; color: #1f2937; margin-bottom: 4px; }
.precaution-desc { font-size: 13px; color: #6b7280; line-height: 1.5; }
</style>
