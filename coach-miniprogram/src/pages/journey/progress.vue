<template>
  <view class="jp-page">

    <!-- 顶部：当前等级 + 六级路径时间线 -->
    <view class="jp-header">
      <view class="jp-header__current">
        <BHPLevelBadge :role="userStore.role" size="md" />
        <text class="jp-header__name">{{ userStore.displayName }}</text>
      </view>
      <!-- 六级时间线 -->
      <view class="jp-timeline">
        <view
          v-for="lv in LEVELS"
          :key="lv.level"
          class="jp-timeline__node"
          :class="{
            'jp-timeline__node--done': userStore.roleLevel >= lv.level,
            'jp-timeline__node--current': userStore.roleLevel === lv.level,
          }"
        >
          <view class="jp-timeline__dot">
            <text v-if="userStore.roleLevel >= lv.level">✓</text>
            <text v-else>{{ lv.level }}</text>
          </view>
          <text class="jp-timeline__label">{{ lv.label }}</text>
        </view>
        <view class="jp-timeline__line">
          <view class="jp-timeline__line-fill" :style="{ width: timelineProgress + '%' }"></view>
        </view>
      </view>
    </view>

    <!-- 三维积分卡片 -->
    <view class="jp-section px-4">
      <text class="jp-section__title">我的积分</text>
      <view class="jp-points-grid">
        <view class="jp-point-card jp-point-card--growth" @tap="goPointsLog('growth')">
          <text class="jp-point-card__val">{{ formatPoints(userStore.growthPoints) }}</text>
          <text class="jp-point-card__label">成长积分</text>
          <view class="jp-point-card__bar">
            <view class="jp-point-card__fill jp-point-card__fill--growth" :style="{ width: growthPct + '%' }"></view>
          </view>
          <text class="jp-point-card__sub">{{ userStore.growthPoints }} / {{ growthTarget }}</text>
        </view>
        <view class="jp-point-card jp-point-card--contrib" @tap="goPointsLog('contribution')">
          <text class="jp-point-card__val">{{ formatPoints(userStore.contributionPts) }}</text>
          <text class="jp-point-card__label">贡献积分</text>
          <view class="jp-point-card__bar">
            <view class="jp-point-card__fill jp-point-card__fill--contrib" :style="{ width: contribPct + '%' }"></view>
          </view>
          <text class="jp-point-card__sub">{{ userStore.contributionPts }} / {{ contribTarget }}</text>
        </view>
        <view class="jp-point-card jp-point-card--influence" @tap="goPointsLog('influence')">
          <text class="jp-point-card__val">{{ formatPoints(userStore.influencePts) }}</text>
          <text class="jp-point-card__label">影响力积分</text>
          <view class="jp-point-card__bar">
            <view class="jp-point-card__fill jp-point-card__fill--influence" :style="{ width: influencePct + '%' }"></view>
          </view>
          <text class="jp-point-card__sub">{{ userStore.influencePts }} / {{ influenceTarget }}</text>
        </view>
      </view>
    </view>

    <!-- 晋级四维要求检查清单 -->
    <view class="jp-section px-4">
      <text class="jp-section__title">晋级要求</text>
      <view class="jp-checklist" v-if="requirements">
        <!-- 成长积分 -->
        <view class="jp-check-item">
          <view class="jp-check-icon" :class="growthMet ? 'jp-check-icon--done' : ''">
            <text>{{ growthMet ? '✅' : '⬜' }}</text>
          </view>
          <view class="jp-check-body">
            <text class="jp-check-label">成长积分达标</text>
            <view class="jp-check-bar">
              <view class="jp-check-fill jp-check-fill--growth" :style="{ width: growthPct + '%' }"></view>
            </view>
            <text class="jp-check-sub">{{ userStore.growthPoints }} / {{ growthTarget }}</text>
          </view>
        </view>
        <!-- 贡献积分 -->
        <view class="jp-check-item">
          <view class="jp-check-icon" :class="contribMet ? 'jp-check-icon--done' : ''">
            <text>{{ contribMet ? '✅' : '⬜' }}</text>
          </view>
          <view class="jp-check-body">
            <text class="jp-check-label">贡献积分达标</text>
            <view class="jp-check-bar">
              <view class="jp-check-fill jp-check-fill--contrib" :style="{ width: contribPct + '%' }"></view>
            </view>
            <text class="jp-check-sub">{{ userStore.contributionPts }} / {{ contribTarget }}</text>
          </view>
        </view>
        <!-- 影响力积分 -->
        <view class="jp-check-item">
          <view class="jp-check-icon" :class="influenceMet ? 'jp-check-icon--done' : ''">
            <text>{{ influenceMet ? '✅' : '⬜' }}</text>
          </view>
          <view class="jp-check-body">
            <text class="jp-check-label">影响力积分达标</text>
            <view class="jp-check-bar">
              <view class="jp-check-fill jp-check-fill--influence" :style="{ width: influencePct + '%' }"></view>
            </view>
            <text class="jp-check-sub">{{ userStore.influencePts }} / {{ influenceTarget }}</text>
          </view>
        </view>
        <!-- 认证考试 -->
        <view class="jp-check-item">
          <view class="jp-check-icon" :class="examPassed ? 'jp-check-icon--done' : ''">
            <text>{{ examPassed ? '✅' : '⬜' }}</text>
          </view>
          <view class="jp-check-body">
            <text class="jp-check-label">认证考试通过</text>
            <text class="jp-check-sub">{{ examPassed ? '已通过' : '未通过' }}</text>
          </view>
        </view>
        <!-- 同道者数量 -->
        <view class="jp-check-item">
          <view class="jp-check-icon" :class="companionsMet ? 'jp-check-icon--done' : ''">
            <text>{{ companionsMet ? '✅' : '⬜' }}</text>
          </view>
          <view class="jp-check-body">
            <text class="jp-check-label">同道者数量</text>
            <text class="jp-check-sub">{{ currentCompanions }} / {{ companionsTarget }}</text>
          </view>
        </view>
      </view>
      <!-- 加载中 -->
      <view v-else class="jp-loading">
        <view class="bhp-skeleton" style="height:60rpx;border-radius:var(--radius-md);margin-bottom:12rpx;" v-for="i in 5" :key="i"></view>
      </view>
    </view>

    <!-- 申请晋级按钮 -->
    <view class="jp-action px-4">
      <view
        class="jp-action__btn"
        :class="allMet ? 'jp-action__btn--active' : 'jp-action__btn--disabled'"
        @tap="handlePromotion"
      >
        <text>{{ allMet ? '申请晋级' : gapHint }}</text>
      </view>
    </view>

    <view style="height:60rpx;"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { formatPoints, LEVEL_THRESHOLDS } from '@/utils/level'
import BHPLevelBadge from '@/components/BHPLevelBadge.vue'
import http from '@/api/request'

const userStore = useUserStore()

const LEVELS = [
  { level: 1, label: '观察者' },
  { level: 2, label: '成长者' },
  { level: 3, label: '分享者' },
  { level: 4, label: '教练' },
  { level: 5, label: '促进师' },
  { level: 6, label: '大师' },
]

// ── 服务端晋级数据 ────────────────────────────────────
const requirements = ref<any>(null)

onMounted(async () => {
  userStore.restoreFromStorage()
  await loadProgress()
})

async function loadProgress() {
  try {
    const res = await http.get<any>('/v1/certification/paths/my-progress')
    requirements.value = res
  } catch {
    // 用本地数据兜底
    requirements.value = {}
  }
}

// ── 积分目标 ──────────────────────────────────────────
const growthTarget    = computed(() => requirements.value?.growth_required    ?? LEVEL_THRESHOLDS[userStore.roleLevel] ?? 500)
const contribTarget   = computed(() => requirements.value?.contribution_required ?? 200)
const influenceTarget = computed(() => requirements.value?.influence_required   ?? 100)
const companionsTarget = computed(() => requirements.value?.companions_required ?? 3)

// ── 进度百分比 ────────────────────────────────────────
const growthPct    = computed(() => Math.min(Math.round((userStore.growthPoints / growthTarget.value) * 100), 100))
const contribPct   = computed(() => Math.min(Math.round((userStore.contributionPts / contribTarget.value) * 100), 100))
const influencePct = computed(() => Math.min(Math.round((userStore.influencePts / influenceTarget.value) * 100), 100))

// ── 条件判断 ──────────────────────────────────────────
const growthMet     = computed(() => userStore.growthPoints >= growthTarget.value)
const contribMet    = computed(() => userStore.contributionPts >= contribTarget.value)
const influenceMet  = computed(() => userStore.influencePts >= influenceTarget.value)
const examPassed    = computed(() => !!requirements.value?.exam_passed)
const currentCompanions = computed(() => requirements.value?.current_companions ?? 0)
const companionsMet = computed(() => currentCompanions.value >= companionsTarget.value)
const allMet        = computed(() => growthMet.value && contribMet.value && influenceMet.value && examPassed.value && companionsMet.value)

// ── 最紧迫缺口提示 ────────────────────────────────────
const gapHint = computed(() => {
  if (!growthMet.value) {
    const gap = growthTarget.value - userStore.growthPoints
    return `还差 ${gap} 成长积分`
  }
  if (!contribMet.value) {
    const gap = contribTarget.value - userStore.contributionPts
    return `还差 ${gap} 贡献积分`
  }
  if (!influenceMet.value) {
    const gap = influenceTarget.value - userStore.influencePts
    return `还差 ${gap} 影响力积分`
  }
  if (!examPassed.value) return '需要通过认证考试'
  if (!companionsMet.value) {
    const gap = companionsTarget.value - currentCompanions.value
    return `还差 ${gap} 位同道者`
  }
  return '申请晋级'
})

// ── 时间线进度 ────────────────────────────────────────
const timelineProgress = computed(() => {
  const lv = userStore.roleLevel
  if (lv >= 6) return 100
  return Math.round(((lv - 1) / 5) * 100)
})

// ── 导航 ─────────────────────────────────────────────
function handlePromotion() {
  if (allMet.value) {
    uni.navigateTo({ url: '/pages/journey/promotion' })
  }
}

function goPointsLog(type: string) {
  uni.navigateTo({ url: `/pages/learning/credits?type=${type}` })
}
</script>

<style scoped>
.jp-page { background: var(--surface-secondary); min-height: 100vh; }

/* 顶部 */
.jp-header { background: var(--surface); padding: 32rpx 32rpx 24rpx; }
.jp-header__current { display: flex; align-items: center; gap: 16rpx; margin-bottom: 28rpx; }
.jp-header__name { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }

/* 六级时间线 */
.jp-timeline { display: flex; justify-content: space-between; position: relative; padding: 0 8rpx; }
.jp-timeline__node { display: flex; flex-direction: column; align-items: center; gap: 8rpx; z-index: 2; }
.jp-timeline__dot {
  width: 48rpx; height: 48rpx; border-radius: 50%;
  background: var(--bhp-gray-100); border: 2px solid var(--bhp-gray-300);
  display: flex; align-items: center; justify-content: center;
  font-size: 20rpx; font-weight: 700; color: var(--text-secondary);
}
.jp-timeline__node--done .jp-timeline__dot {
  background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); color: #fff;
}
.jp-timeline__node--current .jp-timeline__dot {
  border-color: var(--bhp-primary-500); box-shadow: 0 0 0 4rpx rgba(16,185,129,0.2);
}
.jp-timeline__label { font-size: 18rpx; color: var(--text-tertiary); }
.jp-timeline__node--done .jp-timeline__label,
.jp-timeline__node--current .jp-timeline__label { color: var(--bhp-primary-500); font-weight: 600; }
.jp-timeline__line {
  position: absolute; top: 24rpx; left: 32rpx; right: 32rpx; height: 4rpx;
  background: var(--bhp-gray-200); z-index: 1; border-radius: 2rpx;
}
.jp-timeline__line-fill { height: 100%; background: var(--bhp-primary-500); border-radius: 2rpx; transition: width 0.3s; }

/* 分区 */
.jp-section { padding-top: 28rpx; }
.jp-section__title { font-size: 30rpx; font-weight: 700; color: var(--text-primary); display: block; margin-bottom: 20rpx; }

/* 三维积分 */
.jp-points-grid { display: flex; gap: 16rpx; }
.jp-point-card {
  flex: 1; background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx 16rpx; display: flex; flex-direction: column; align-items: center; gap: 8rpx;
  border: 1px solid var(--border-light); cursor: pointer;
}
.jp-point-card:active { opacity: 0.8; }
.jp-point-card__val { font-size: 40rpx; font-weight: 700; }
.jp-point-card--growth .jp-point-card__val { color: var(--bhp-primary-500); }
.jp-point-card--contrib .jp-point-card__val { color: #3b82f6; }
.jp-point-card--influence .jp-point-card__val { color: #f59e0b; }
.jp-point-card__label { font-size: 22rpx; color: var(--text-secondary); }
.jp-point-card__bar { width: 100%; height: 8rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.jp-point-card__fill { height: 100%; border-radius: var(--radius-full); transition: width 0.3s; }
.jp-point-card__fill--growth { background: var(--bhp-primary-500); }
.jp-point-card__fill--contrib { background: #3b82f6; }
.jp-point-card__fill--influence { background: #f59e0b; }
.jp-point-card__sub { font-size: 18rpx; color: var(--text-tertiary); }

/* 检查清单 */
.jp-checklist { display: flex; flex-direction: column; gap: 16rpx; }
.jp-check-item {
  display: flex; gap: 16rpx; align-items: flex-start;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx 24rpx; border: 1px solid var(--border-light);
}
.jp-check-icon { font-size: 36rpx; flex-shrink: 0; margin-top: 2rpx; }
.jp-check-body { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
.jp-check-label { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.jp-check-bar { height: 8rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.jp-check-fill { height: 100%; border-radius: var(--radius-full); transition: width 0.3s; }
.jp-check-fill--growth { background: var(--bhp-primary-500); }
.jp-check-fill--contrib { background: #3b82f6; }
.jp-check-fill--influence { background: #f59e0b; }
.jp-check-sub { font-size: 22rpx; color: var(--text-tertiary); }

/* 加载 */
.jp-loading { padding: 16rpx 0; }

/* 申请按钮 */
.jp-action { padding-top: 32rpx; }
.jp-action__btn {
  width: 100%; height: 88rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; font-weight: 700;
}
.jp-action__btn--active { background: var(--bhp-primary-500); color: #fff; cursor: pointer; }
.jp-action__btn--active:active { opacity: 0.85; }
.jp-action__btn--disabled { background: var(--bhp-gray-100); color: var(--text-tertiary); }
</style>
