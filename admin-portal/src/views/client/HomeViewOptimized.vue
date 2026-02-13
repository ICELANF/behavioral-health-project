<template>
  <div class="client-home-optimized">
    <!-- 1. 顶部问候区 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <div class="greeting">
          <div class="greeting-time">{{ greetingText }}</div>
          <div class="greeting-name">{{ userName }} 👋</div>
        </div>
        <a-avatar :size="60" class="user-avatar">
          <template #icon><UserOutlined /></template>
        </a-avatar>
      </div>

      <!-- 健康评分 - 使用组件 -->
      <div class="health-score-wrapper">
        <HealthScoreCircle
          :score="healthScore"
          :size="100"
          :status-text="healthScoreText"
          :subtitle="`🔥 连续打卡 ${streakDays} 天`"
          :show-info="false"
        />
      </div>
    </div>

    <!-- 2. 主内容区 -->
    <div class="main-content">
      <!-- 今日重点任务 - 使用 TaskList 组件 -->
      <div v-if="priorityTasks.length > 0" class="section-card">
        <TaskList
          :tasks="priorityTasks"
          title="✨ 今天要做的事"
          :show-header="true"
          :show-progress="true"
          :show-encouragement="true"
          encouragement-text="太棒了！今日任务全部完成"
          @toggle="toggleTask"
        />
      </div>

      <!-- 3. 健康快照 - 使用 HealthMetricCard 组件 -->
      <div class="section-card health-snapshot">
        <h3 class="section-title">📊 健康快照</h3>

        <div class="snapshot-grid">
          <HealthMetricCard
            icon="🩸"
            label="血糖"
            :value="bloodGlucose.fasting"
            :status="bloodGlucose.status"
            :status-text="getStatusText(bloodGlucose.status)"
            theme="glucose"
            @click="goToDetail('glucose')"
          />

          <HealthMetricCard
            icon="⚖️"
            label="体重"
            :value="weight.current"
            :status="weight.status"
            :status-text="getStatusText(weight.status)"
            theme="weight"
            @click="goToDetail('weight')"
          />

          <HealthMetricCard
            icon="🏃"
            label="运动(分钟)"
            :value="exercise.weeklyMinutes"
            :progress="Math.min(100, (exercise.weeklyMinutes / exercise.targetMinutes) * 100)"
            :show-progress="true"
            :progress-text="`目标 ${exercise.targetMinutes} 分钟`"
            theme="exercise"
            @click="goToDetail('exercise')"
          />

          <HealthMetricCard
            icon="💊"
            label="今日用药"
            :value="todayMedCount"
            :badge="`${takenMedCount}/${todayMedCount}`"
            theme="medication"
            @click="goToDetail('medication')"
          />
        </div>
      </div>

      <!-- 4. 快速入口 - 4个核心功能 -->
      <div class="section-card quick-actions">
        <h3 class="section-title">⚡ 快速入口</h3>

        <div class="action-grid">
          <div class="action-btn" @click="router.push('/client/data-input')">
            <div class="action-icon">📝</div>
            <div class="action-label">记录数据</div>
            <div class="action-desc">血糖、体重等</div>
          </div>

          <div class="action-btn" @click="router.push('/client/chat-v2')">
            <div class="action-icon">💬</div>
            <div class="action-label">AI助手</div>
            <div class="action-desc">健康咨询</div>
          </div>

          <div class="action-btn" @click="router.push('/client/progress')">
            <div class="action-icon">📈</div>
            <div class="action-label">我的进展</div>
            <div class="action-desc">查看趋势</div>
          </div>

          <div class="action-btn" @click="showMoreDrawer = true">
            <div class="action-icon">🎯</div>
            <div class="action-label">更多功能</div>
            <div class="action-desc">学习、课程</div>
          </div>
        </div>
      </div>

      <!-- 5. 每日提示（如果有） -->
      <div class="section-card daily-tip" v-if="dailyTip">
        <div class="tip-header">
          <div class="tip-icon-large">{{ dailyTip.icon }}</div>
          <div class="tip-content">
            <div class="tip-title">{{ dailyTip.title }}</div>
            <div class="tip-text">{{ dailyTip.content }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航栏 -->
    <div class="bottom-nav">
      <div class="nav-item active">
        <HomeOutlined />
        <span>首页</span>
      </div>
      <div class="nav-item" @click="router.push('/client/device-dashboard')">
        <LineChartOutlined />
        <span>数据</span>
      </div>
      <div class="nav-item center-btn" @click="router.push('/client/chat-v2')">
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

    <!-- 更多功能抽屉 -->
    <a-drawer
      v-model:open="showMoreDrawer"
      title="更多功能"
      placement="bottom"
      :height="'70vh'"
    >
      <div class="more-menu">
        <div class="more-item" @click="goToPage('/client/my/assessments')">
          <div class="more-icon">📋</div>
          <div class="more-label">测评记录</div>
        </div>
        <div class="more-item" @click="goToPage('/client/my/trajectory')">
          <div class="more-icon">🎯</div>
          <div class="more-label">行为轨迹</div>
        </div>
        <div class="more-item" @click="goToPage('/client/learning-progress')">
          <div class="more-icon">📚</div>
          <div class="more-label">学习进度</div>
        </div>
        <div class="more-item" @click="goToPage('/client/my/devices')">
          <div class="more-icon">⌚</div>
          <div class="more-label">我的设备</div>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  UserOutlined,
  HomeOutlined,
  LineChartOutlined,
  MessageOutlined,
  ReadOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { healthApi } from '@/api/health'
import { HealthScoreCircle, TaskList, HealthMetricCard } from '@/components/health'
import type { Task } from '@/components/health'

const router = useRouter()

// 用户信息
const userName = ref('张先生')
const healthScore = ref(0)
const streakDays = ref(0)
const loading = ref(true)

// 患者ID（实际应该从登录状态获取）
const patientId = 'p001'

// 问候语
const greetingText = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了，早点休息'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了，早点休息'
})

const healthScoreText = computed(() => {
  if (healthScore.value >= 90) return '状态非常好！'
  if (healthScore.value >= 75) return '保持得不错'
  if (healthScore.value >= 60) return '继续加油'
  return '需要更多关注'
})

// 今日重点任务（最多3个）
const priorityTasks = ref<Task[]>([])

const toggleTask = async (task: Task) => {
  task.completed = !task.completed
  if (task.completed) {
    try {
      await healthApi.completeTask(patientId, String(task.id))
      message.success({
        content: '🎉 太棒了！任务完成 +10积分',
        duration: 2
      })
    } catch (e) {
      console.error('完成任务失败:', e)
    }
  }
}

// 健康指标
const bloodGlucose = ref({ fasting: '--', status: 'good' as const })
const weight = ref({ current: '--', status: 'good' as const })
const exercise = ref({ weeklyMinutes: 0, targetMinutes: 150 })
const todayMedCount = ref(3)
const takenMedCount = ref(2)

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    good: '正常',
    normal: '正常',
    warning: '注意',
    danger: '偏高'
  }
  return map[status] || '正常'
}

// 每日提示
const dailyTip = ref<{ icon: string; title: string; content: string } | null>(null)

// 更多功能
const showMoreDrawer = ref(false)

const goToDetail = (type: string) => {
  const routes: Record<string, string> = {
    glucose: '/client/data-input',
    weight: '/client/data-input',
    exercise: '/client/data-input',
    medication: '/client/my/profile'
  }
  if (routes[type]) {
    router.push(routes[type])
  } else {
    router.push('/client')
  }
}

const goToPage = (path: string) => {
  router.push(path)
  showMoreDrawer.value = false
}

// 加载数据
const loadData = async () => {
  try {
    loading.value = true

    // 并行加载多个数据
    const [scoreData, snapshotData, tasksData, summaryData] = await Promise.all([
      healthApi.getHealthScore(patientId, 'week'),
      healthApi.getHealthSnapshot(patientId),
      healthApi.getDailyTasks(patientId),
      healthApi.getAISummary(patientId, 'week')
    ])

    // 更新健康评分
    if (scoreData) {
      healthScore.value = scoreData.overall
      streakDays.value = 7 // 可以从后端返回
    }

    // 更新健康快照
    if (snapshotData) {
      bloodGlucose.value = {
        fasting: snapshotData.glucose.value.toString(),
        status: snapshotData.glucose.status
      }
      weight.value = {
        current: snapshotData.weight.value.toString(),
        status: 'good'
      }
      exercise.value = {
        weeklyMinutes: snapshotData.exercise.todayMinutes * 7, // 估算周总量
        targetMinutes: snapshotData.exercise.weeklyGoal
      }
    }

    // 更新任务列表（只显示前3个高优先级任务）
    if (tasksData?.tasks) {
      const emojiMap: Record<string, string> = {
        glucose: '🩸',
        weight: '⚖️',
        exercise: '🏃',
        mood: '😊',
        assessment: '📋'
      }

      priorityTasks.value = tasksData.tasks
        .filter((t: any) => t.priority === 'high' || t.priority === 'medium')
        .slice(0, 3)
        .map((t: any) => ({
          id: t.id,
          name: t.title,
          hint: t.dueTime ? `建议在 ${t.dueTime} 前完成` : undefined,
          emoji: emojiMap[t.type] || '📝',
          completed: t.completed
        }))
    }

    // 更新每日提示
    if (summaryData?.summary) {
      dailyTip.value = {
        icon: '💡',
        title: 'AI 健康建议',
        content: summaryData.summary
      }
    }

  } catch (error) {
    console.error('加载数据失败:', error)
    message.error('加载数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.client-home-optimized {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 80px;
}

/* 1. 顶部问候区 */
.welcome-section {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  padding: 24px 20px 32px;
  border-radius: 0 0 32px 32px;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.greeting-time {
  color: rgba(255,255,255,0.9);
  font-size: 15px;
  margin-bottom: 4px;
}

.greeting-name {
  color: #fff;
  font-size: 28px;
  font-weight: 700;
}

.user-avatar {
  background: rgba(255,255,255,0.2);
  border: 3px solid rgba(255,255,255,0.5);
}

.health-score-wrapper {
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 20px;
  display: flex;
  justify-content: center;
}

/* 2. 主内容区 */
.main-content {
  max-width: 640px;
  margin: -20px auto 0;
  padding: 0 16px;
  position: relative;
  z-index: 10;
}

.section-card {
  background: #fff;
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 16px 0;
}

/* 健康快照 */
.snapshot-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

/* 快速入口 */
.action-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.action-btn {
  background: #f9fafb;
  padding: 20px 16px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
  border: 2px solid transparent;
}

.action-btn:hover {
  background: #f3f4f6;
  border-color: #10b981;
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(16,185,129,0.15);
}

.action-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.action-label {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.action-desc {
  font-size: 12px;
  color: #6b7280;
}

/* 每日提示 */
.daily-tip {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 2px solid #bfdbfe;
}

.tip-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.tip-icon-large {
  font-size: 40px;
  flex-shrink: 0;
}

.tip-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 6px;
}

.tip-text {
  font-size: 14px;
  color: #1e3a8a;
  line-height: 1.6;
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
  align-items: center;
  padding: 8px 0 20px;
  box-shadow: 0 -2px 12px rgba(0,0,0,0.08);
  z-index: 100;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #9ca3af;
  font-size: 11px;
  cursor: pointer;
  transition: color 0.2s;
}

.nav-item:hover {
  color: #10b981;
}

.nav-item.active {
  color: #10b981;
  font-weight: 600;
}

.nav-item :deep(.anticon) {
  font-size: 24px;
}

.nav-item.center-btn {
  margin-top: -24px;
}

.center-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 16px rgba(16,185,129,0.4);
}

.center-icon :deep(.anticon) {
  font-size: 28px;
}

/* 更多功能抽屉 */
.more-menu {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 20px;
}

.more-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: #f9fafb;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.more-item:hover {
  background: #f3f4f6;
  transform: translateY(-4px);
}

.more-icon {
  font-size: 40px;
}

.more-label {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}
</style>
