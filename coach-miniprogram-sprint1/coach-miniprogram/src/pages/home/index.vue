<template>
  <view class="home-page">

    <!-- ════════════════════════════════════════
         学习者视图（L0-L2）
    ════════════════════════════════════════ -->
    <template v-if="!userStore.isCoach">

      <!-- 顶部 Header -->
      <view class="home-header">
        <view class="home-header__left">
          <image class="home-header__avatar" :src="avatar" mode="aspectFill" />
          <view>
            <text class="home-header__greeting">{{ greeting }}，</text>
            <text class="home-header__name">{{ userStore.displayName }}</text>
            <view class="mt-1">
              <BHPLevelBadge :role="userStore.role" size="xs" />
            </view>
          </view>
        </view>
        <view class="home-header__right" @tap="goNotify">
          <text class="home-header__bell">🔔</text>
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
      <view
        class="home-alert px-4"
        v-if="pendingAssessmentCount > 0"
        @tap="goPendingAssessment"
      >
        <view class="home-alert__card bhp-card">
          <text class="home-alert__icon">📋</text>
          <view class="flex-1">
            <text class="home-alert__title">你有 {{ pendingAssessmentCount }} 份待完成评估</text>
            <text class="home-alert__desc">教练已为你安排了行为评估任务</text>
          </view>
          <text class="home-alert__arrow">→</text>
        </view>
      </view>

      <!-- 继续学习 -->
      <view class="home-section" v-if="learningStore.inProgress.length > 0">
        <view class="home-section__header px-4">
          <text class="home-section__title">继续学习</text>
          <text class="home-section__more" @tap="goLearning">全部 →</text>
        </view>
        <scroll-view scroll-x class="home-continue-scroll px-4">
          <view class="home-continue-list">
            <view
              v-for="item in learningStore.inProgress"
              :key="item.content_id"
              class="home-continue-item bhp-card"
              @tap="goContinue(item)"
            >
              <view class="home-continue-item__bar">
                <view
                  class="home-continue-item__fill"
                  :style="{ width: item.progress_percent + '%' }"
                ></view>
              </view>
              <text class="home-continue-item__title line-clamp-2">{{ item.title }}</text>
              <text class="home-continue-item__pct">{{ item.progress_percent }}%</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 推荐课程 -->
      <view class="home-section">
        <view class="home-section__header px-4">
          <text class="home-section__title">为你推荐</text>
          <text class="home-section__more" @tap="goCatalog">更多 →</text>
        </view>
        <view v-if="loadingContent" class="px-4">
          <view v-for="i in 3" :key="i" class="bhp-skeleton home-skeleton-card"></view>
        </view>
        <view v-else class="home-course-grid px-4">
          <BHPCourseCard
            v-for="course in recommendedCourses"
            :key="course.id"
            :course="course"
            :user-level="userStore.roleLevel"
            @tap="goCourse"
          />
        </view>
      </view>

      <!-- 快捷入口 -->
      <view class="home-shortcuts px-4">
        <view class="home-shortcut" @tap="goJourney">
          <text class="home-shortcut__icon">🗺</text>
          <text class="home-shortcut__label">成长路径</text>
        </view>
        <view class="home-shortcut" @tap="goCompanions">
          <text class="home-shortcut__icon">👥</text>
          <text class="home-shortcut__label">同道者</text>
        </view>
        <view class="home-shortcut" @tap="goExam">
          <text class="home-shortcut__icon">📝</text>
          <text class="home-shortcut__label">认证考试</text>
        </view>
        <view class="home-shortcut" @tap="goAssessment">
          <text class="home-shortcut__icon">📊</text>
          <text class="home-shortcut__label">我的评估</text>
        </view>
      </view>

    </template>

    <!-- ════════════════════════════════════════
         教练工作台视图（L3+）
    ════════════════════════════════════════ -->
    <template v-else>

      <!-- 教练 Header -->
      <view class="home-header">
        <view class="home-header__left">
          <image class="home-header__avatar" :src="avatar" mode="aspectFill" />
          <view>
            <text class="home-header__greeting">{{ greeting }}，</text>
            <text class="home-header__name">{{ userStore.displayName }} 教练</text>
            <view class="mt-1">
              <BHPLevelBadge :role="userStore.role" size="xs" />
            </view>
          </view>
        </view>
        <view class="home-header__right" @tap="goNotify">
          <text class="home-header__bell">🔔</text>
          <view class="home-header__badge" v-if="coachStore.badgeCount > 0">
            <text>{{ coachStore.badgeCount }}</text>
          </view>
        </view>
      </view>

      <!-- 工作台统计卡 -->
      <view class="coach-stats px-4">
        <view class="bhp-card">
          <view class="coach-stats__grid">
            <view class="coach-stats__item" @tap="goStudents">
              <text class="coach-stats__value">{{ dashStats?.total_students || 0 }}</text>
              <text class="coach-stats__label">学员总数</text>
            </view>
            <view class="coach-stats__item coach-stats__item--danger" @tap="goHighRisk">
              <text class="coach-stats__value" style="color: #ef4444">{{ dashStats?.high_risk_count || 0 }}</text>
              <text class="coach-stats__label">高风险</text>
            </view>
            <view class="coach-stats__item coach-stats__item--warn" @tap="goPushQueue">
              <text class="coach-stats__value" style="color: #f59e0b">{{ coachStore.pendingQueueCount }}</text>
              <text class="coach-stats__label">待审批</text>
            </view>
            <view class="coach-stats__item coach-stats__item--info" @tap="goAssessmentReview">
              <text class="coach-stats__value" style="color: #3b82f6">{{ coachStore.pendingAssessmentCount }}</text>
              <text class="coach-stats__label">待审核</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 高风险学员列表 -->
      <view class="home-section" v-if="coachStore.highRiskStudents.length > 0">
        <view class="home-section__header px-4">
          <text class="home-section__title">⚠️ 需关注学员</text>
          <text class="home-section__more" @tap="goStudents">全部 →</text>
        </view>
        <view class="px-4">
          <view
            v-for="stu in coachStore.highRiskStudents"
            :key="stu.id"
            class="student-item bhp-card bhp-card--flat"
            @tap="goStudentDetail(stu.id)"
          >
            <view class="flex-between">
              <view class="flex-start gap-3">
                <view class="student-item__avatar">
                  <text>{{ stu.full_name?.[0] || stu.username?.[0] || '用' }}</text>
                </view>
                <view>
                  <text class="student-item__name">{{ stu.full_name || stu.username }}</text>
                  <view class="flex-start gap-2 mt-1">
                    <BHPRiskTag :level="stu.risk_level" />
                    <text class="text-xs text-secondary-color">{{ TTM_LABELS[stu.ttm_stage]?.label || stu.ttm_stage }}</text>
                  </view>
                </view>
              </view>
              <text class="student-item__arrow">→</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 教练快捷入口 -->
      <view class="home-shortcuts px-4">
        <view class="home-shortcut" @tap="goPushQueue">
          <text class="home-shortcut__icon">✅</text>
          <text class="home-shortcut__label">推送审批</text>
          <view class="home-shortcut__dot" v-if="coachStore.pendingQueueCount > 0"></view>
        </view>
        <view class="home-shortcut" @tap="goAssessmentReview">
          <text class="home-shortcut__icon">📋</text>
          <text class="home-shortcut__label">评估审核</text>
          <view class="home-shortcut__dot" v-if="coachStore.pendingAssessmentCount > 0"></view>
        </view>
        <view class="home-shortcut" @tap="goAnalytics">
          <text class="home-shortcut__icon">📈</text>
          <text class="home-shortcut__label">数据分析</text>
        </view>
        <view class="home-shortcut" @tap="goLearning">
          <text class="home-shortcut__icon">📖</text>
          <text class="home-shortcut__label">继续学习</text>
        </view>
      </view>

    </template>

    <!-- 底部安全区域占位 -->
    <view style="height: 100px"></view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useLearningStore } from '@/stores/learning'
import { useCoachStore } from '@/stores/coach'
import { TTM_LABELS } from '@/utils/level'
import http from '@/api/request'

const userStore    = useUserStore()
const learningStore = useLearningStore()
const coachStore   = useCoachStore()

const loadingContent       = ref(true)
const recommendedCourses   = ref<any[]>([])
const pendingAssessmentCount = ref(0)

// ─── 计算属性 ─────────────────────────────────────────────────
const avatar = computed(() =>
  userStore.userInfo?.avatar_url || '/static/default-avatar.png'
)

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6)  return '夜深了'
  if (h < 11) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const dashStats = computed(() => coachStore.dashboardStats)

// ─── 初始化 ───────────────────────────────────────────────────
onMounted(async () => {
  await userStore.refreshUserInfo()

  if (userStore.isCoach) {
    await coachStore.initDashboard()
  } else {
    // 并发加载
    await Promise.all([
      learningStore.loadStats(),
      learningStore.loadInProgress(),
      loadRecommended(),
      loadPendingAssessment()
    ])
  }
})

// 下拉刷新
onPullDownRefresh(async () => {
  if (userStore.isCoach) {
    await coachStore.initDashboard()
  } else {
    await Promise.all([
      userStore.refreshUserInfo(),
      learningStore.loadStats(),
      learningStore.loadInProgress(),
      loadRecommended()
    ])
  }
  uni.stopPullDownRefresh()
})

async function loadRecommended() {
  loadingContent.value = true
  try {
    const data = await http.get<{ items: any[] }>('/v1/content', {
      limit: 6,
      status: 'published'
    })
    recommendedCourses.value = data.items || []
  } catch { /* 静默 */ } finally {
    loadingContent.value = false
  }
}

async function loadPendingAssessment() {
  try {
    const data = await http.get<{ total: number }>('/v1/assessment/assignments/pending')
    pendingAssessmentCount.value = data.total || 0
  } catch { /* 静默 */ }
}

// ─── 导航 ─────────────────────────────────────────────────────
const nav = (url: string) => uni.navigateTo({ url })
const tab = (url: string) => uni.switchTab({ url })

const goNotify          = () => nav('/pages/notifications/index')
const goLearning        = () => nav('/pages/learning/index')
const goCatalog         = () => nav('/pages/learning/catalog')
const goJourney         = () => nav('/pages/journey/overview')
const goCompanions      = () => nav('/pages/companions/index')
const goExam            = () => nav('/pages/exam/index')
const goAssessment      = () => nav('/pages/assessment/pending')
const goPendingAssessment = () => nav('/pages/assessment/pending')
const goStudents        = () => nav('/pages/coach/students/index')
const goHighRisk        = () => nav('/pages/coach/students/index?filter=high_risk')
const goPushQueue       = () => nav('/pages/coach/push-queue')
const goAssessmentReview = () => nav('/pages/coach/assessment/index')
const goAnalytics       = () => nav('/pages/coach/analytics/index')
const goStudentDetail   = (id: number) => nav(`/pages/coach/students/detail?id=${id}`)

function goCourse(course: any) {
  const typePageMap: Record<string, string> = {
    video:  '/pages/learning/video-player',
    audio:  '/pages/learning/audio-player',
    course: '/pages/learning/course-detail',
    article:'/pages/learning/content-detail',
    card:   '/pages/learning/content-detail'
  }
  const page = typePageMap[course.content_type] || '/pages/learning/content-detail'
  nav(`${page}?id=${course.id}`)
}

function goContinue(item: any) {
  const typePageMap: Record<string, string> = {
    video: '/pages/learning/video-player',
    audio: '/pages/learning/audio-player',
    course:'/pages/learning/course-detail'
  }
  const page = typePageMap[item.content_type] || '/pages/learning/content-detail'
  nav(`${page}?id=${item.content_id}`)
}
</script>

<style scoped>
.home-page { background: var(--surface-secondary); min-height: 100vh; }

/* Header */
.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 60rpx 32rpx 24rpx;
  background: var(--surface);
}
.home-header__left    { display: flex; align-items: center; gap: 16rpx; }
.home-header__avatar  { width: 80rpx; height: 80rpx; border-radius: 50%; background: var(--bhp-gray-200); }
.home-header__greeting{ font-size: 26rpx; color: var(--text-secondary); }
.home-header__name    { font-size: 32rpx; font-weight: 700; color: var(--text-primary); display: block; }
.home-header__right   { position: relative; }
.home-header__bell    { font-size: 44rpx; }
.home-header__badge   {
  position: absolute; top: -6px; right: -6px;
  min-width: 18px; height: 18px;
  background: #ef4444; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 18rpx; color: #fff; font-weight: 700;
}

/* Section */
.home-section { margin-top: 24rpx; }
.home-section__header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16rpx;
}
.home-section__title { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }
.home-section__more  { font-size: 26rpx; color: var(--bhp-primary-500); }

/* Alert */
.home-alert { margin-top: 24rpx; }
.home-alert__card {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--bhp-accent-50);
  border: 1px solid var(--bhp-accent-200);
}
.home-alert__icon  { font-size: 40rpx; }
.home-alert__title { font-size: 28rpx; font-weight: 600; color: var(--bhp-accent-700); }
.home-alert__desc  { font-size: 22rpx; color: var(--bhp-accent-600); margin-top: 4rpx; display: block; }
.home-alert__arrow { font-size: 28rpx; color: var(--bhp-accent-500); }

/* 继续学习 */
.home-continue-scroll { white-space: nowrap; }
.home-continue-list   { display: flex; gap: 16rpx; padding-bottom: 4rpx; }
.home-continue-item {
  display: inline-flex; flex-direction: column;
  width: 240rpx; flex-shrink: 0;
  padding: 16rpx;
  position: relative;
  overflow: hidden;
}
.home-continue-item__bar {
  height: 4px; background: var(--bhp-gray-200);
  border-radius: 9999px; margin-bottom: 12rpx;
  overflow: hidden;
}
.home-continue-item__fill {
  height: 100%; background: var(--bhp-primary-500);
  border-radius: 9999px; transition: width 0.4s;
}
.home-continue-item__title { font-size: 24rpx; font-weight: 600; color: var(--text-primary); flex: 1; }
.home-continue-item__pct   { font-size: 22rpx; color: var(--bhp-primary-500); font-weight: 600; margin-top: 8rpx; }

/* 课程网格 */
.home-course-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

/* 骨架屏 */
.home-skeleton-card { height: 200rpx; margin-bottom: 16rpx; border-radius: var(--radius-lg); }

/* 快捷入口 */
.home-shortcuts {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
  margin-top: 24rpx;
}
.home-shortcut {
  display: flex; flex-direction: column; align-items: center; gap: 8rpx;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx 8rpx;
  position: relative;
  cursor: pointer;
}
.home-shortcut:active { opacity: 0.7; }
.home-shortcut__icon  { font-size: 44rpx; }
.home-shortcut__label { font-size: 22rpx; color: var(--text-secondary); text-align: center; }
.home-shortcut__dot   {
  position: absolute; top: 8px; right: 8px;
  width: 8px; height: 8px; background: #ef4444; border-radius: 50%;
}

/* 教练统计卡 */
.coach-stats { margin-top: 16rpx; }
.coach-stats__grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 0; text-align: center;
}
.coach-stats__item {
  padding: 16rpx 8rpx;
  border-right: 1px solid var(--divider);
  cursor: pointer;
}
.coach-stats__item:last-child { border-right: none; }
.coach-stats__item:active { background: var(--bhp-gray-50); }
.coach-stats__value {
  display: block; font-size: 44rpx; font-weight: 700;
  color: var(--text-primary); line-height: 1.2;
}
.coach-stats__label { display: block; font-size: 20rpx; color: var(--text-secondary); margin-top: 4rpx; }

/* 学员列表项 */
.student-item { margin-bottom: 12rpx; }
.student-item__avatar {
  width: 72rpx; height: 72rpx; border-radius: 50%;
  background: var(--bhp-primary-100);
  display: flex; align-items: center; justify-content: center;
  font-size: 32rpx; font-weight: 700; color: var(--bhp-primary-600);
}
.student-item__name  { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.student-item__arrow { font-size: 28rpx; color: var(--text-tertiary); }
</style>
