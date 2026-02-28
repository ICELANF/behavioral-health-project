<template>
  <view class="wd-page">

    <!-- 工作台头部 -->
    <view class="wd-header">
      <view class="wd-header__left">
        <text class="wd-header__greeting">👋 {{ greeting }}</text>
        <text class="wd-header__name">{{ userStore.displayName }}</text>
        <view class="wd-header__role-badge">
          <text>{{ userStore.roleLabel }}</text>
        </view>
      </view>
      <view class="wd-header__refresh" @tap="refresh">
        <text class="wd-header__refresh-icon">↻</text>
      </view>
    </view>

    <!-- 统计卡片 -->
    <view class="wd-stats px-4">
      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 140rpx; border-radius: var(--radius-lg);"></view>
      </template>
      <template v-else>
        <view class="wd-stats__grid">
          <view class="wd-stats__card wd-stats__card--total" @tap="goStudents">
            <text class="wd-stats__val">{{ stats.total_students }}</text>
            <text class="wd-stats__label">我的学员</text>
          </view>
          <view class="wd-stats__card wd-stats__card--risk" @tap="goStudents">
            <text class="wd-stats__val">{{ stats.high_risk_count }}</text>
            <text class="wd-stats__label">高风险</text>
            <view class="wd-stats__dot wd-dot--red" v-if="stats.high_risk_count > 0"></view>
          </view>
          <view class="wd-stats__card wd-stats__card--queue" @tap="goPushQueue">
            <text class="wd-stats__val">{{ stats.pending_queue_count }}</text>
            <text class="wd-stats__label">待审批</text>
            <view class="wd-stats__dot wd-dot--orange" v-if="stats.pending_queue_count > 0"></view>
          </view>
          <view class="wd-stats__card wd-stats__card--assess" @tap="goAssessment">
            <text class="wd-stats__val">{{ stats.pending_assessment_count }}</text>
            <text class="wd-stats__label">待审核</text>
            <view class="wd-stats__dot wd-dot--orange" v-if="stats.pending_assessment_count > 0"></view>
          </view>
        </view>
      </template>
    </view>

    <!-- 高风险学员警报 -->
    <view class="wd-alerts px-4" v-if="coachStore.highRiskStudents.length">
      <view class="wd-alerts__header">
        <text class="wd-section-title">⚠️ 高风险学员</text>
        <view @tap="goStudents"><text class="text-xs text-primary-color">查看全部 ›</text></view>
      </view>
      <scroll-view class="wd-alerts__scroll" scroll-x>
        <view
          v-for="s in coachStore.highRiskStudents"
          :key="s.id"
          class="wd-alert-card"
          :class="`wd-risk--${s.risk_level}`"
          @tap="goStudentDetail(s.id)"
        >
          <view class="wd-alert-card__avatar" :style="{ background: riskColor(s.risk_level) }">
            <text class="wd-alert-card__avatar-text">{{ (s.full_name || s.username || '用')[0] }}</text>
          </view>
          <text class="wd-alert-card__name">{{ s.full_name || s.username }}</text>
          <view class="wd-alert-card__risk-badge" :style="{ background: riskColor(s.risk_level) }">
            <text>{{ RISK_LABEL[s.risk_level] }}</text>
          </view>
          <text class="wd-alert-card__stage text-xs">{{ TTM_LABEL[s.ttm_stage] }}</text>
          <view class="wd-alert-card__glucose" v-if="s.latest_glucose">
            <text class="text-xs">血糖 {{ s.latest_glucose }}</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- 快捷功能 -->
    <view class="wd-quick px-4">
      <text class="wd-section-title">快捷操作</text>
      <view class="wd-quick__grid">
        <view
          v-for="item in quickActions"
          :key="item.key"
          class="wd-quick__item bhp-card bhp-card--flat"
          @tap="item.action"
        >
          <view class="wd-quick__icon" :style="{ background: item.color + '18' }">
            <text :style="{ color: item.color }">{{ item.icon }}</text>
          </view>
          <text class="wd-quick__label">{{ item.label }}</text>
          <view class="wd-quick__badge" v-if="item.badge > 0">
            <text>{{ item.badge > 99 ? '99+' : item.badge }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 近期推送审批 -->
    <view class="wd-pending px-4" v-if="coachStore.pendingQueue.length">
      <view class="wd-pending__header">
        <text class="wd-section-title">待审批推送</text>
        <view @tap="goPushQueue"><text class="text-xs text-primary-color">全部 ›</text></view>
      </view>
      <view
        v-for="item in coachStore.pendingQueue.slice(0, 3)"
        :key="item.id"
        class="wd-push-item bhp-card bhp-card--flat"
      >
        <view class="wd-push-item__body">
          <text class="wd-push-item__user text-xs text-secondary-color">
            → {{ item.target_user?.full_name || item.target_user?.username }}
          </text>
          <text class="wd-push-item__content">{{ item.content }}</text>
        </view>
        <view class="wd-push-item__actions">
          <view class="wd-push-btn wd-push-btn--reject" @tap="quickReject(item.id)">
            <text>拒</text>
          </view>
          <view class="wd-push-btn wd-push-btn--approve" @tap="quickApprove(item.id)">
            <text>批</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 绩效摘要 -->
    <view class="wd-perf px-4">
      <view class="wd-perf__card bhp-card bhp-card--flat">
        <text class="wd-section-title" style="margin-bottom: 16rpx;">本周数据</text>
        <view class="wd-perf__row">
          <view class="wd-perf__item">
            <text class="wd-perf__val">{{ stats.active_students_7d }}</text>
            <text class="wd-perf__label">活跃学员</text>
          </view>
          <view class="wd-perf__item">
            <text class="wd-perf__val">{{ stats.improvement_rate ? (stats.improvement_rate * 100).toFixed(0) + '%' : '—' }}</text>
            <text class="wd-perf__label">风险改善率</text>
          </view>
          <view class="wd-perf__item">
            <text class="wd-perf__val">{{ stats.medium_risk_count }}</text>
            <text class="wd-perf__label">中风险</text>
          </view>
        </view>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useCoachStore } from '@/stores/coach'
import { useUserStore } from '@/stores/user'

const coachStore = useCoachStore()
const userStore  = useUserStore()

const loading = computed(() => coachStore.loading)
const stats   = computed(() => coachStore.dashboardStats || {
  total_students: 0, high_risk_count: 0, medium_risk_count: 0,
  pending_queue_count: 0, pending_assessment_count: 0,
  active_students_7d: 0, improvement_rate: 0
})

const RISK_LABEL: Record<string, string> = {
  critical: '危急', high: '高风', moderate: '中风', low: '低风', none: '正常'
}
const TTM_LABEL: Record<string, string> = {
  S0: '未知', S1: '前意向', S2: '意向', S3: '准备',
  S4: '行动', S5: '维持', S6: '终止'
}

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const quickActions = computed(() => [
  {
    key: 'students', icon: '👥', label: '我的学员', color: '#1890ff', badge: 0,
    action: goStudents
  },
  {
    key: 'push', icon: '📤', label: '推送审批', color: '#fa8c16',
    badge: stats.value.pending_queue_count,
    action: goPushQueue
  },
  {
    key: 'assessment', icon: '📋', label: '评估审核', color: '#722ed1',
    badge: stats.value.pending_assessment_count,
    action: goAssessment
  },
  {
    key: 'analytics', icon: '📊', label: '数据分析', color: '#52c41a', badge: 0,
    action: goAnalytics
  },
  {
    key: 'companions', icon: '🤝', label: '我的同道', color: '#eb2f96', badge: 0,
    action: () => uni.navigateTo({ url: '/pages/companions/index' })
  },
  {
    key: 'live', icon: '🎥', label: '直播管理', color: '#f5222d', badge: 0,
    action: () => uni.navigateTo({ url: '/pages/coach/live/index' })
  },
])

onMounted(() => coachStore.initDashboard())

onPullDownRefresh(async () => {
  await coachStore.initDashboard()
  uni.stopPullDownRefresh()
})

function refresh() { coachStore.initDashboard() }

function goStudents()            { uni.navigateTo({ url: '/pages/coach/students/index' }) }
function goStudentDetail(id: number) { uni.navigateTo({ url: `/pages/coach/students/detail?id=${id}` }) }
function goPushQueue()           { uni.navigateTo({ url: '/pages/coach/push-queue' }) }
function goAssessment()          { uni.navigateTo({ url: '/pages/coach/assessment/index' }) }
function goAnalytics()           { uni.navigateTo({ url: '/pages/coach/analytics/index' }) }

function riskColor(level: string): string {
  const map: Record<string, string> = {
    critical: '#f5222d', high: '#ff4d4f', moderate: '#fa8c16', low: '#52c41a', none: '#8c8c8c'
  }
  return map[level] || '#8c8c8c'
}

async function quickApprove(id: number) {
  try {
    await coachStore.approvePush(id)
    uni.showToast({ title: '已审批通过', icon: 'success' })
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

function quickReject(id: number) {
  uni.showModal({
    title: '拒绝推送',
    editable: true,
    placeholderText: '请输入拒绝原因（可选）',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await coachStore.rejectPush(id, res.content)
        uni.showToast({ title: '已拒绝', icon: 'none' })
      } catch {
        uni.showToast({ title: '操作失败', icon: 'none' })
      }
    }
  })
}
</script>

<style scoped>
.wd-page { background: var(--surface-secondary); min-height: 100vh; }

/* 头部 */
.wd-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 24rpx 32rpx 16rpx;
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
}
.wd-header__left  { display: flex; flex-direction: column; gap: 6rpx; }
.wd-header__greeting { font-size: 24rpx; color: var(--text-tertiary); }
.wd-header__name  { font-size: 36rpx; font-weight: 700; color: var(--text-primary); }
.wd-header__role-badge {
  display: inline-flex;
  background: var(--bhp-primary-50); color: var(--bhp-primary-700, #047857);
  border-radius: var(--radius-full);
  padding: 4rpx 16rpx;
  font-size: 22rpx; font-weight: 600;
}
.wd-header__refresh { padding: 12rpx; cursor: pointer; }
.wd-header__refresh-icon { font-size: 36rpx; color: var(--bhp-primary-500); }

/* 统计网格 */
.wd-stats { padding-top: 16rpx; }
.wd-stats__grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 8rpx;
}
.wd-stats__card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 16rpx 8rpx;
  display: flex; flex-direction: column; align-items: center; gap: 6rpx;
  border: 1px solid var(--border-light);
  cursor: pointer; position: relative;
}
.wd-stats__card:active { opacity: 0.8; }
.wd-stats__val   { font-size: 36rpx; font-weight: 700; color: var(--text-primary); }
.wd-stats__label { font-size: 20rpx; color: var(--text-tertiary); }
.wd-stats__dot {
  position: absolute; top: 8rpx; right: 8rpx;
  width: 12rpx; height: 12rpx; border-radius: 50%;
}
.wd-dot--red    { background: #ff4d4f; }
.wd-dot--orange { background: #fa8c16; }

/* 高风险警报 */
.wd-alerts { padding-top: 20rpx; }
.wd-alerts__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.wd-section-title { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }

.wd-alerts__scroll { white-space: nowrap; }

.wd-alert-card {
  display: inline-flex; flex-direction: column; align-items: center;
  width: 160rpx; padding: 16rpx;
  background: var(--surface);
  border-radius: var(--radius-lg);
  margin-right: 12rpx;
  border: 1px solid var(--border-light);
  cursor: pointer; gap: 8rpx;
  white-space: normal;
}
.wd-alert-card:active { opacity: 0.8; }
.wd-alert-card__avatar {
  width: 64rpx; height: 64rpx;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
}
.wd-alert-card__avatar-text { font-size: 26rpx; color: #fff; font-weight: 700; }
.wd-alert-card__name { font-size: 22rpx; font-weight: 500; color: var(--text-primary); text-align: center; }
.wd-alert-card__risk-badge {
  border-radius: var(--radius-full);
  padding: 2rpx 10rpx;
  font-size: 18rpx; color: #fff; font-weight: 700;
}
.wd-alert-card__stage { color: var(--text-tertiary); }
.wd-alert-card__glucose { background: var(--bhp-error-50, #fef2f2); border-radius: var(--radius-sm); padding: 2rpx 10rpx; }

/* 快捷操作 */
.wd-quick { padding-top: 20rpx; }
.wd-quick__grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10rpx; margin-top: 12rpx; }
.wd-quick__item {
  display: flex; flex-direction: column; align-items: center;
  padding: 20rpx 8rpx; gap: 10rpx;
  cursor: pointer; position: relative;
}
.wd-quick__item:active { opacity: 0.75; }
.wd-quick__icon {
  width: 72rpx; height: 72rpx;
  border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 32rpx;
}
.wd-quick__label { font-size: 22rpx; color: var(--text-primary); font-weight: 500; }
.wd-quick__badge {
  position: absolute; top: 6rpx; right: 20rpx;
  background: #ff4d4f; color: #fff;
  font-size: 16rpx; font-weight: 700;
  padding: 2rpx 8rpx;
  border-radius: var(--radius-full);
  min-width: 28rpx; text-align: center;
}

/* 待审批推送 */
.wd-pending { padding-top: 20rpx; }
.wd-pending__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.wd-push-item {
  display: flex; align-items: center; gap: 16rpx;
  padding: 16rpx 20rpx; margin-bottom: 10rpx;
}
.wd-push-item__body { flex: 1; overflow: hidden; }
.wd-push-item__user { display: block; margin-bottom: 4rpx; }
.wd-push-item__content {
  font-size: 24rpx; color: var(--text-primary);
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.wd-push-item__actions { display: flex; gap: 8rpx; flex-shrink: 0; }
.wd-push-btn {
  width: 56rpx; height: 56rpx;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; font-weight: 700;
  cursor: pointer;
}
.wd-push-btn:active { opacity: 0.7; }
.wd-push-btn--approve { background: var(--bhp-success-500, #22c55e); color: #fff; }
.wd-push-btn--reject  { background: var(--bhp-gray-200); color: var(--text-secondary); }

/* 绩效 */
.wd-perf { padding-top: 20rpx; }
.wd-perf__row { display: flex; }
.wd-perf__item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6rpx; }
.wd-perf__val   { font-size: 36rpx; font-weight: 700; color: var(--text-primary); }
.wd-perf__label { font-size: 22rpx; color: var(--text-tertiary); }
</style>
