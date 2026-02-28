<template>
  <view class="home-page">

    <!-- ════════════════════════════════════════
         学员视图（L1-L3：grower/sharer/学员）
    ════════════════════════════════════════ -->
    <template v-if="!userStore.isCoach">

      <!-- 顶部 Header -->
      <view class="home-header">
        <view class="home-header__left">
          <image class="home-header__avatar" :src="avatar" mode="aspectFill" />
          <view>
            <view class="home-header__greeting-row">
              <text class="home-header__greeting">{{ greeting }}，</text>
              <text class="home-header__name">{{ userStore.displayName }}</text>
            </view>
            <view class="mt-1">
              <BHPLevelBadge :role="userStore.role" size="xs" />
            </view>
          </view>
        </view>
        <view class="home-header__right" @tap="goNotify">
          <text class="home-header__bell">🔔</text>
          <view class="home-header__bell-dot" v-if="unreadCount > 0">
            <text>{{ unreadCount > 9 ? '9+' : unreadCount }}</text>
          </view>
        </view>
      </view>

      <!-- 积分卡 -->
      <view class="home-section px-4">
        <BHPPointsCard
          :role="userStore.role"
          :growth-points="userStore.growthPoints"
          :contribution-points="userStore.contributionPts"
          :influence-points="userStore.influencePts"
          :streak="learningStore.currentStreak"
        />
      </view>

      <!-- 待完成评估提醒 -->
      <view class="home-alert px-4" v-if="pendingAssessmentCount > 0">
        <view class="home-alert__card" @tap="goAssessment">
          <text class="home-alert__icon">📋</text>
          <view class="home-alert__body">
            <text class="home-alert__title">您有 {{ pendingAssessmentCount }} 个待完成评估</text>
            <text class="home-alert__sub text-xs text-secondary-color">点击查看并完成</text>
          </view>
          <text class="home-alert__arrow">›</text>
        </view>
      </view>

      <!-- 今日任务 -->
      <view class="home-section px-4">
        <view class="home-section__header">
          <text class="home-section__title">今日任务</text>
          <text class="home-section__more text-primary-color" @tap="goTasks">全部 ›</text>
        </view>
        <template v-if="loadingTasks">
          <view class="bhp-skeleton" style="height: 80rpx; margin-bottom: 10rpx; border-radius: var(--radius-md);"></view>
          <view class="bhp-skeleton" style="height: 80rpx; border-radius: var(--radius-md);"></view>
        </template>
        <view v-else-if="todayTasks.length" class="home-tasks">
          <view
            v-for="task in todayTasks.slice(0, 3)"
            :key="task.id"
            class="home-task-item bhp-card bhp-card--flat"
            :class="{ 'home-task-item--done': task.completed }"
            @tap="toggleTask(task)"
          >
            <view class="home-task-item__check" :class="{ 'home-task-item__check--done': task.completed }">
              <text v-if="task.completed">✓</text>
            </view>
            <text class="home-task-item__text" :class="{ 'home-task-item__text--done': task.completed }">
              {{ task.title }}
            </text>
            <text class="home-task-item__pts text-xs text-primary-color" v-if="task.points">
              +{{ task.points }}
            </text>
          </view>
        </view>
        <view v-else class="home-empty-tip">
          <text class="text-secondary-color text-sm">今日任务已全部完成 🎉</text>
        </view>
      </view>

      <!-- 推荐学习 -->
      <view class="home-section px-4">
        <view class="home-section__header">
          <text class="home-section__title">推荐学习</text>
          <text class="home-section__more text-primary-color" @tap="goLearning">更多 ›</text>
        </view>
        <template v-if="loadingContent">
          <view class="bhp-skeleton" style="height: 200rpx; border-radius: var(--radius-lg);"></view>
        </template>
        <scroll-view v-else-if="recommended.length" scroll-x class="home-recommend-scroll">
          <view class="home-recommend-row">
            <BHPCourseCard
              v-for="item in recommended"
              :key="item.id"
              :title="item.title"
              :cover="item.cover_url"
              :type="item.type"
              :duration="item.estimated_minutes ? item.estimated_minutes + '分钟' : ''"
              :points="item.points"
              class="home-recommend-card"
              @tap="goContent(item.id)"
            />
          </view>
        </scroll-view>
        <view v-else class="home-empty-tip">
          <text class="text-secondary-color text-sm">暂无推荐内容</text>
        </view>
      </view>

    </template>

    <!-- ════════════════════════════════════════
         教练视图（L4+）
    ════════════════════════════════════════ -->
    <template v-else>

      <!-- 教练 Header -->
      <view class="home-header home-header--coach">
        <view class="home-header__left">
          <image class="home-header__avatar home-header__avatar--coach" :src="avatar" mode="aspectFill" />
          <view>
            <view class="home-header__greeting-row">
              <text class="home-header__greeting">{{ greeting }}，</text>
              <text class="home-header__name">{{ userStore.displayName }} 教练</text>
            </view>
            <BHPLevelBadge :role="userStore.role" size="xs" />
          </view>
        </view>
        <view class="home-header__right" @tap="goNotify">
          <text class="home-header__bell">🔔</text>
        </view>
      </view>

      <!-- 快速统计 -->
      <view class="home-coach-stats px-4" v-if="coachStore.dashboardStats">
        <view class="home-coach-stat-grid">
          <view class="home-coach-stat" @tap="goCoachStudents">
            <text class="home-coach-stat__val">{{ coachStore.dashboardStats.total_students }}</text>
            <text class="home-coach-stat__lbl">学员</text>
          </view>
          <view class="home-coach-stat" @tap="goCoachStudents">
            <text class="home-coach-stat__val" :class="{ 'text-error-color': coachStore.dashboardStats.high_risk_count > 0 }">
              {{ coachStore.dashboardStats.high_risk_count }}
            </text>
            <text class="home-coach-stat__lbl">高风险</text>
          </view>
          <view class="home-coach-stat" @tap="goPushQueue">
            <text class="home-coach-stat__val text-primary-color">{{ coachStore.dashboardStats.pending_push_count }}</text>
            <text class="home-coach-stat__lbl">待审批</text>
          </view>
          <view class="home-coach-stat" @tap="goCoachAssessment">
            <text class="home-coach-stat__val">{{ coachStore.dashboardStats.pending_review_count }}</text>
            <text class="home-coach-stat__lbl">待评审</text>
          </view>
        </view>
      </view>

      <!-- 待审批推送 -->
      <view class="home-section px-4" v-if="coachStore.pendingQueue.length">
        <view class="home-section__header">
          <text class="home-section__title">待审批推送</text>
          <text class="home-section__more text-primary-color" @tap="goPushQueue">全部 ›</text>
        </view>
        <view
          v-for="item in coachStore.pendingQueue.slice(0, 2)"
          :key="item.id"
          class="home-push-item bhp-card bhp-card--flat"
          @tap="goPushQueue"
        >
          <view class="home-push-item__left">
            <text class="home-push-item__name text-sm font-semibold">{{ item.student_name }}</text>
            <text class="home-push-item__title text-xs text-secondary-color">{{ item.content_title }}</text>
          </view>
          <view class="home-push-item__actions">
            <view class="home-push-btn home-push-btn--reject" @tap.stop="quickReject(item.id)">
              <text class="text-xs">拒绝</text>
            </view>
            <view class="home-push-btn home-push-btn--approve" @tap.stop="quickApprove(item.id)">
              <text class="text-xs">通过</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 教练工作台入口 -->
      <view class="home-section px-4">
        <view class="home-section__header">
          <text class="home-section__title">工作台</text>
        </view>
        <view class="home-coach-actions">
          <view class="home-coach-action" v-for="action in COACH_ACTIONS" :key="action.key" @tap="action.fn()">
            <view class="home-coach-action__icon" :style="{ background: action.color + '18' }">
              <text>{{ action.icon }}</text>
            </view>
            <text class="home-coach-action__label text-xs">{{ action.label }}</text>
          </view>
        </view>
      </view>

    </template>

    <view style="height: 40rpx;"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore }    from '@/stores/user'
import { useLearningStore } from '@/stores/learning'
import { useCoachStore }   from '@/stores/coach'
import http from '@/api/request'
import BHPLevelBadge  from '@/components/BHPLevelBadge.vue'
import BHPPointsCard  from '@/components/BHPPointsCard.vue'
import BHPCourseCard  from '@/components/BHPCourseCard.vue'

const userStore     = useUserStore()
const learningStore = useLearningStore()
const coachStore    = useCoachStore()

const loadingTasks   = ref(false)
const loadingContent = ref(false)
const todayTasks     = ref<any[]>([])
const recommended    = ref<any[]>([])
const unreadCount    = ref(0)
const pendingAssessmentCount = ref(0)

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6)  return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const avatar = computed(() =>
  userStore.userInfo?.avatar_url || '/static/default-avatar.png'
)

const COACH_ACTIONS = [
  { key: 'students',   label: '我的学员', icon: '👥', color: '#10b981', fn: goCoachStudents },
  { key: 'push',       label: '推送审批', icon: '📨', color: '#3b82f6', fn: goPushQueue },
  { key: 'assessment', label: '评估管理', icon: '📋', color: '#8b5cf6', fn: goCoachAssessment },
  { key: 'analytics',  label: '数据分析', icon: '📊', color: '#f59e0b', fn: goAnalytics },
]

onMounted(async () => {
  userStore.restoreFromStorage()
  if (!userStore.isLoggedIn) {
    uni.reLaunch({ url: '/pages/auth/login' })
    return
  }
  if (userStore.isCoach) {
    coachStore.initDashboard()
  } else {
    loadLearnerData()
  }
  loadUnread()
})

onPullDownRefresh(async () => {
  if (userStore.isCoach) {
    await coachStore.initDashboard()
  } else {
    await loadLearnerData()
  }
  uni.stopPullDownRefresh()
})

async function loadLearnerData() {
  await Promise.allSettled([
    loadTasks(),
    loadRecommended(),
    loadPendingAssessments(),
    learningStore.fetchStats(),
  ])
}

async function loadTasks() {
  loadingTasks.value = true
  try {
    const res = await http.get<{ items: any[] }>('/v1/micro-actions/today', { page_size: 10 })
    todayTasks.value = res.items || []
  } catch {
    todayTasks.value = []
  } finally {
    loadingTasks.value = false
  }
}

async function loadRecommended() {
  loadingContent.value = true
  try {
    const res = await http.get<{ items: any[] }>('/v1/content/recommended', { page_size: 8 })
    recommended.value = res.items || []
  } catch {
    recommended.value = []
  } finally {
    loadingContent.value = false
  }
}

async function loadPendingAssessments() {
  try {
    const res = await http.get<{ items: any[] }>('/v1/assessment-assignments/my', {
      status: 'assigned', page_size: 5,
    })
    pendingAssessmentCount.value = (res.items || []).length
  } catch {
    pendingAssessmentCount.value = 0
  }
}

async function loadUnread() {
  try {
    const res = await http.get<{ unread_count: number }>('/v1/notifications/unread-count')
    unreadCount.value = res.unread_count ?? 0
  } catch {
    unreadCount.value = 0
  }
}

async function toggleTask(task: any) {
  if (task.completed) return
  try {
    await http.post(`/v1/micro-actions/${task.id}/complete`, {})
    task.completed = true
    if (task.points) userStore.addPoints(task.points)
  } catch {/* ignore */}
}

async function quickApprove(id: number) {
  const ok = await coachStore.approvePush(id)
  if (ok) uni.showToast({ title: '已通过', icon: 'success' })
}
async function quickReject(id: number) {
  const ok = await coachStore.rejectPush(id)
  if (ok) uni.showToast({ title: '已拒绝', icon: 'none' })
}

// ─── 导航 ──────────────────────────────────────
function goNotify()          { uni.switchTab({ url: '/pages/notifications/index' }) }
function goLearning()        { uni.navigateTo({ url: '/pages/learning/index' }) }
function goContent(id: number) { uni.navigateTo({ url: `/pages/learning/content-detail?id=${id}` }) }
function goAssessment()      { uni.navigateTo({ url: '/pages/assessment/pending' }) }
function goTasks()           { uni.navigateTo({ url: '/pages/learning/my-learning' }) }
function goCoachStudents()   { uni.navigateTo({ url: '/pages/coach/students/index' }) }
function goPushQueue()       { uni.navigateTo({ url: '/pages/coach/push-queue' }) }
function goCoachAssessment() { uni.navigateTo({ url: '/pages/coach/assessment/index' }) }
function goAnalytics()       { uni.navigateTo({ url: '/pages/coach/analytics/index' }) }
</script>

<style scoped>
.home-page { background: var(--surface-secondary); min-height: 100vh; }

/* Header */
.home-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16rpx 32rpx 12rpx;
  background: var(--surface);
}
.home-header--coach { background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); }
.home-header--coach .home-header__greeting,
.home-header--coach .home-header__name { color: #fff; }
.home-header__left     { display: flex; align-items: center; gap: 16rpx; }
.home-header__avatar   { width: 72rpx; height: 72rpx; border-radius: 50%; background: var(--bhp-gray-100); }
.home-header__avatar--coach { border: 2px solid rgba(255,255,255,0.5); }
.home-header__greeting-row { display: flex; align-items: baseline; }
.home-header__greeting { font-size: 26rpx; color: var(--text-secondary); }
.home-header__name     { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.home-header__right    { position: relative; cursor: pointer; }
.home-header__bell     { font-size: 44rpx; }
.home-header__bell-dot {
  position: absolute; top: -4rpx; right: -4rpx;
  background: #ff4d4f; color: #fff;
  font-size: 16rpx; min-width: 28rpx; height: 28rpx;
  border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center; padding: 0 4rpx;
}

/* Section */
.home-section      { padding-top: 24rpx; }
.home-section__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; }
.home-section__title  { font-size: 30rpx; font-weight: 700; color: var(--text-primary); }
.home-section__more   { font-size: 24rpx; cursor: pointer; }
.home-empty-tip       { padding: 24rpx 0; text-align: center; }

/* 评估提醒 */
.home-alert { padding-top: 16rpx; }
.home-alert__card {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--bhp-warn-50); border: 1px solid var(--bhp-warn-100);
  border-radius: var(--radius-lg); padding: 20rpx 24rpx; cursor: pointer;
}
.home-alert__icon   { font-size: 40rpx; }
.home-alert__body   { flex: 1; }
.home-alert__title  { font-size: 26rpx; font-weight: 600; color: var(--bhp-warn-700); display: block; }
.home-alert__arrow  { font-size: 36rpx; color: var(--bhp-warn-700); }

/* 今日任务 */
.home-tasks { display: flex; flex-direction: column; gap: 10rpx; }
.home-task-item {
  display: flex; align-items: center; gap: 16rpx;
  padding: 20rpx 20rpx; cursor: pointer; transition: opacity 0.15s;
}
.home-task-item:active { opacity: 0.8; }
.home-task-item--done  { opacity: 0.6; }
.home-task-item__check {
  width: 36rpx; height: 36rpx; border-radius: 50%;
  border: 2px solid var(--bhp-gray-300);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  font-size: 20rpx;
}
.home-task-item__check--done { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); color: #fff; }
.home-task-item__text         { flex: 1; font-size: 26rpx; color: var(--text-primary); }
.home-task-item__text--done   { text-decoration: line-through; color: var(--text-tertiary); }
.home-task-item__pts          { flex-shrink: 0; font-weight: 600; }

/* 推荐学习 */
.home-recommend-scroll { white-space: nowrap; }
.home-recommend-row    { display: flex; gap: 16rpx; }
.home-recommend-card   { width: 280rpx; flex-shrink: 0; display: inline-block; white-space: normal; }

/* 教练统计 */
.home-coach-stats { padding-top: 16rpx; }
.home-coach-stat-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  background: var(--surface); border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
}
.home-coach-stat {
  display: flex; flex-direction: column; align-items: center;
  padding: 24rpx 8rpx; cursor: pointer; gap: 6rpx;
  border-right: 1px solid var(--border-light);
}
.home-coach-stat:last-child { border-right: none; }
.home-coach-stat__val { font-size: 40rpx; font-weight: 700; color: var(--text-primary); }
.home-coach-stat__lbl { font-size: 20rpx; color: var(--text-secondary); }

/* 待审批推送 */
.home-push-item {
  display: flex; align-items: center; gap: 16rpx;
  padding: 20rpx; margin-bottom: 10rpx; cursor: pointer;
}
.home-push-item__left  { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.home-push-item__actions { display: flex; gap: 12rpx; flex-shrink: 0; }
.home-push-btn {
  padding: 8rpx 20rpx; border-radius: var(--radius-full); cursor: pointer;
  font-weight: 600;
}
.home-push-btn--approve { background: var(--bhp-primary-500); color: #fff; }
.home-push-btn--reject  { background: var(--bhp-gray-100); color: var(--text-secondary); }

/* 教练操作网格 */
.home-coach-actions {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16rpx;
}
.home-coach-action {
  display: flex; flex-direction: column; align-items: center; gap: 10rpx; cursor: pointer;
}
.home-coach-action:active { opacity: 0.7; }
.home-coach-action__icon {
  width: 96rpx; height: 96rpx; border-radius: var(--radius-xl);
  display: flex; align-items: center; justify-content: center;
  font-size: 40rpx;
}
.home-coach-action__label { color: var(--text-secondary); text-align: center; }
</style>
