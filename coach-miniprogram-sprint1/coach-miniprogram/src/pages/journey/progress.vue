<template>
  <view class="progress-page">

    <!-- 当前等级卡 -->
    <view class="prog-level-card px-4">
      <view
        class="prog-level-card__inner bhp-card bhp-card--flat"
        :style="{ borderLeft: `6rpx solid ${currentMeta.color}` }"
      >
        <view class="prog-level-card__left">
          <view class="prog-level-card__icon-wrap" :style="{ background: currentMeta.bgColor }">
            <text class="prog-level-card__icon">{{ currentMeta.icon }}</text>
          </view>
        </view>
        <view class="prog-level-card__body">
          <text class="prog-level-card__level" :style="{ color: currentMeta.color }">{{ currentMeta.label }}</text>
          <text class="prog-level-card__name">{{ userStore.displayName }}</text>
          <view class="prog-level-card__pts-row">
            <text class="prog-level-card__pts">{{ userStore.growthPoints }} 成长</text>
            <text class="prog-level-card__sep">·</text>
            <text class="prog-level-card__pts">{{ userStore.contributionPts }} 贡献</text>
            <text class="prog-level-card__sep">·</text>
            <text class="prog-level-card__pts">{{ userStore.influencePts }} 影响</text>
          </view>
        </view>
        <view class="prog-level-card__refresh" @tap="refresh">
          <text>↻</text>
        </view>
      </view>
    </view>

    <!-- 已达顶级 -->
    <view class="prog-maxed px-4" v-if="!nextLevelKey">
      <view class="prog-maxed__card bhp-card bhp-card--flat">
        <text class="prog-maxed__icon">🏆</text>
        <text class="prog-maxed__text">您已达到最高等级 L5 大师！</text>
      </view>
    </view>

    <!-- 晋级进度 -->
    <template v-else>
      <view class="prog-next-label px-4">
        <text class="prog-next-label__text">距 {{ nextMeta?.label }} 还需</text>
      </view>

      <!-- 进度条组 -->
      <view class="prog-conditions px-4">

        <!-- 骨架屏 -->
        <template v-if="loadingProgress">
          <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 80rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
        </template>

        <template v-else>
          <!-- 1. 成长积分 -->
          <view class="prog-cond-card bhp-card bhp-card--flat" v-if="nextReq?.growth > 0">
            <view class="prog-cond-header">
              <text class="prog-cond-icon">🌱</text>
              <text class="prog-cond-label">成长积分</text>
              <view class="prog-cond-status-tag" :class="growthMet ? 'prog-tag--met' : 'prog-tag--unmet'">
                <text>{{ growthMet ? '✓ 已达成' : '未达成' }}</text>
              </view>
            </view>
            <view class="prog-bar-row">
              <view class="prog-bar">
                <view class="prog-bar-fill prog-bar-fill--growth" :style="{ width: growthPct + '%' }"></view>
              </view>
              <text class="prog-bar-text">{{ userStore.growthPoints }} / {{ nextReq.growth }}</text>
            </view>
          </view>

          <!-- 2. 贡献积分 -->
          <view class="prog-cond-card bhp-card bhp-card--flat" v-if="nextReq?.contribution > 0">
            <view class="prog-cond-header">
              <text class="prog-cond-icon">🌿</text>
              <text class="prog-cond-label">贡献积分</text>
              <view class="prog-cond-status-tag" :class="contributionMet ? 'prog-tag--met' : 'prog-tag--unmet'">
                <text>{{ contributionMet ? '✓ 已达成' : '未达成' }}</text>
              </view>
            </view>
            <view class="prog-bar-row">
              <view class="prog-bar">
                <view class="prog-bar-fill prog-bar-fill--contribution" :style="{ width: contributionPct + '%' }"></view>
              </view>
              <text class="prog-bar-text">{{ userStore.contributionPts }} / {{ nextReq.contribution }}</text>
            </view>
          </view>

          <!-- 3. 影响积分 -->
          <view class="prog-cond-card bhp-card bhp-card--flat" v-if="nextReq?.influence > 0">
            <view class="prog-cond-header">
              <text class="prog-cond-icon">⭐</text>
              <text class="prog-cond-label">影响积分</text>
              <view class="prog-cond-status-tag" :class="influenceMet ? 'prog-tag--met' : 'prog-tag--unmet'">
                <text>{{ influenceMet ? '✓ 已达成' : '未达成' }}</text>
              </view>
            </view>
            <view class="prog-bar-row">
              <view class="prog-bar">
                <view class="prog-bar-fill prog-bar-fill--influence" :style="{ width: influencePct + '%' }"></view>
              </view>
              <text class="prog-bar-text">{{ userStore.influencePts }} / {{ nextReq.influence }}</text>
            </view>
          </view>

          <!-- 4. 认证考试 -->
          <view class="prog-cond-card bhp-card bhp-card--flat" v-if="nextReq?.exam">
            <view class="prog-cond-header">
              <text class="prog-cond-icon">📝</text>
              <text class="prog-cond-label">{{ nextLevelKey }} 认证考试</text>
              <view class="prog-cond-status-tag" :class="serverProgress?.exam_passed ? 'prog-tag--met' : 'prog-tag--unmet'">
                <text>{{ serverProgress?.exam_passed ? '✓ 已通过' : '未通过' }}</text>
              </view>
            </view>
            <view class="prog-cond-action" v-if="!serverProgress?.exam_passed">
              <view class="bhp-btn bhp-btn--secondary" @tap="goExam">
                <text>去参加考试 ›</text>
              </view>
            </view>
          </view>

          <!-- 5. 同道者 -->
          <view class="prog-cond-card bhp-card bhp-card--flat" v-if="nextReq?.companions > 0">
            <view class="prog-cond-header">
              <text class="prog-cond-icon">👥</text>
              <text class="prog-cond-label">{{ nextReq.companions }} 位≥{{ nextReq.companion_min_level }}同道者</text>
              <view class="prog-cond-status-tag" :class="companionMet ? 'prog-tag--met' : 'prog-tag--unmet'">
                <text>{{ companionMet ? '✓ 已达成' : `${serverProgress?.companion_count || 0}/${nextReq.companions}` }}</text>
              </view>
            </view>
            <view class="prog-bar-row">
              <view class="prog-bar">
                <view
                  class="prog-bar-fill prog-bar-fill--companion"
                  :style="{ width: companionPct + '%' }"
                ></view>
              </view>
              <text class="prog-bar-text">{{ serverProgress?.companion_count || 0 }} / {{ nextReq.companions }}</text>
            </view>
            <view class="prog-cond-action" v-if="!companionMet">
              <view class="bhp-btn bhp-btn--secondary" @tap="goCompanions">
                <text>邀请同道者 ›</text>
              </view>
            </view>
          </view>
        </template>
      </view>

      <!-- 综合进度 -->
      <view class="prog-overall px-4">
        <view class="prog-overall__card bhp-card bhp-card--flat">
          <view class="prog-overall__row">
            <text class="prog-overall__label">综合完成度</text>
            <text class="prog-overall__pct" :style="{ color: overallPct >= 100 ? 'var(--bhp-success-500)' : 'var(--bhp-primary-500)' }">
              {{ overallPct }}%
            </text>
          </view>
          <view class="prog-overall__bar">
            <view class="prog-overall__fill" :style="{ width: overallPct + '%' }"></view>
          </view>
          <view
            class="prog-overall__apply-btn"
            v-if="overallPct >= 100"
            @tap="goPromotion"
          >
            <text>🚀 条件已满足，立即申请晋级</text>
          </view>
          <text class="prog-overall__hint" v-else>
            满足所有条件后即可提交晋级申请
          </text>
        </view>
      </view>
    </template>

    <!-- 操作入口 -->
    <view class="prog-shortcuts px-4">
      <view class="prog-shortcut" @tap="goOverview">
        <text class="prog-shortcut__icon">🗺</text>
        <text class="prog-shortcut__label">成长路径图</text>
        <text class="prog-shortcut__arrow">›</text>
      </view>
      <view class="prog-shortcut" @tap="goHistory">
        <text class="prog-shortcut__icon">📋</text>
        <text class="prog-shortcut__label">申请记录</text>
        <text class="prog-shortcut__arrow">›</text>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { pathsApi, companionApi, LEVEL_META, LEVEL_THRESHOLDS, type MyProgress } from '@/api/journey'

const userStore = useUserStore()

const serverProgress  = ref<MyProgress | null>(null)
const companionCount  = ref(0)
const loadingProgress = ref(false)

const ROLE_TO_LEVEL: Record<string, number> = {
  observer: 0, grower: 1, sharer: 2, coach: 3, promoter: 4, supervisor: 4, master: 5
}

const currentLevelNum = computed(() => ROLE_TO_LEVEL[userStore.role] ?? 0)
const nextLevelNum    = computed(() => currentLevelNum.value < 5 ? currentLevelNum.value + 1 : null)
const nextLevelKey    = computed(() => nextLevelNum.value !== null ? `L${nextLevelNum.value}` : null)

const currentMeta = computed(() => LEVEL_META[`L${currentLevelNum.value}`] || LEVEL_META['L0'])
const nextMeta    = computed(() => nextLevelKey.value ? LEVEL_META[nextLevelKey.value] : null)
const nextReq     = computed(() => nextLevelKey.value ? LEVEL_THRESHOLDS[nextLevelKey.value] : null)

// 各条件是否满足
const growthMet      = computed(() => !nextReq.value?.growth      || userStore.growthPoints    >= nextReq.value.growth)
const contributionMet= computed(() => !nextReq.value?.contribution || userStore.contributionPts >= nextReq.value.contribution)
const influenceMet   = computed(() => !nextReq.value?.influence    || userStore.influencePts    >= nextReq.value.influence)
const companionMet   = computed(() =>
  !nextReq.value?.companions || (serverProgress.value?.companion_count || companionCount.value) >= nextReq.value.companions
)

// 进度百分比
const growthPct       = computed(() => !nextReq.value?.growth ? 100 :
  Math.min(Math.round(userStore.growthPoints / nextReq.value.growth * 100), 100))
const contributionPct = computed(() => !nextReq.value?.contribution ? 100 :
  Math.min(Math.round(userStore.contributionPts / nextReq.value.contribution * 100), 100))
const influencePct    = computed(() => !nextReq.value?.influence ? 100 :
  Math.min(Math.round(userStore.influencePts / nextReq.value.influence * 100), 100))
const companionPct    = computed(() => !nextReq.value?.companions ? 100 :
  Math.min(Math.round((serverProgress.value?.companion_count || 0) / nextReq.value.companions * 100), 100))

// 综合进度
const overallPct = computed(() => {
  if (!nextLevelKey.value) return 100
  const req = nextReq.value
  if (!req) return 0
  const checks: boolean[] = [growthMet.value, contributionMet.value]
  if (req.influence > 0) checks.push(influenceMet.value)
  if (req.exam)          checks.push(serverProgress.value?.exam_passed || false)
  if (req.companions > 0)checks.push(companionMet.value)
  const met = checks.filter(Boolean).length
  return Math.round((met / checks.length) * 100)
})

onMounted(async () => {
  await Promise.all([loadProgress(), loadCompanions()])
})

onPullDownRefresh(async () => {
  await Promise.all([loadProgress(), loadCompanions(), userStore.refreshUserInfo()])
  uni.stopPullDownRefresh()
})

async function loadProgress() {
  loadingProgress.value = true
  try {
    serverProgress.value = await pathsApi.myProgress()
  } catch { /* 静默，使用本地数据 */ } finally {
    loadingProgress.value = false
  }
}

async function loadCompanions() {
  try {
    const s = await companionApi.mySummary()
    companionCount.value = s.qualified || s.total || 0
    if (serverProgress.value) serverProgress.value.companion_count = companionCount.value
  } catch { /* 静默 */ }
}

async function refresh() {
  uni.showLoading({ title: '刷新中' })
  await Promise.all([loadProgress(), loadCompanions(), userStore.refreshUserInfo()])
  uni.hideLoading()
}

function goPromotion()  { uni.navigateTo({ url: '/pages/journey/promotion' }) }
function goOverview()   { uni.navigateTo({ url: '/pages/journey/overview' }) }
function goHistory()    { uni.navigateTo({ url: '/pages/journey/history' }) }
function goExam()       { uni.navigateTo({ url: '/pages/exam/index' }) }
function goCompanions() { uni.navigateTo({ url: '/pages/companions/index' }) }
</script>

<style scoped>
.progress-page { background: var(--surface-secondary); min-height: 100vh; }

/* 等级卡 */
.prog-level-card { padding-top: 16rpx; }
.prog-level-card__inner {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 24rpx;
}
.prog-level-card__icon-wrap {
  width: 80rpx;
  height: 80rpx;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.prog-level-card__icon   { font-size: 44rpx; }
.prog-level-card__body   { flex: 1; }
.prog-level-card__level  { display: block; font-size: 28rpx; font-weight: 700; }
.prog-level-card__name   { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }
.prog-level-card__pts-row{ display: flex; align-items: center; gap: 8rpx; margin-top: 6rpx; flex-wrap: wrap; }
.prog-level-card__pts    { font-size: 20rpx; color: var(--text-tertiary); }
.prog-level-card__sep    { color: var(--border-light); font-size: 16rpx; }
.prog-level-card__refresh{ font-size: 32rpx; color: var(--text-tertiary); cursor: pointer; padding: 8rpx; }

/* 已满级 */
.prog-maxed { padding-top: 16rpx; }
.prog-maxed__card {
  display: flex; flex-direction: column; align-items: center; padding: 48rpx; gap: 16rpx;
}
.prog-maxed__icon { font-size: 80rpx; }
.prog-maxed__text { font-size: 28rpx; color: var(--text-primary); font-weight: 600; }

/* 标签 */
.prog-next-label { padding-top: 24rpx; margin-bottom: 12rpx; }
.prog-next-label__text { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }

/* 条件卡 */
.prog-conditions { display: flex; flex-direction: column; gap: 12rpx; }
.prog-cond-card { padding: 20rpx 24rpx; }
.prog-cond-header {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 12rpx;
}
.prog-cond-icon  { font-size: 28rpx; }
.prog-cond-label { flex: 1; font-size: 26rpx; font-weight: 500; color: var(--text-primary); }

.prog-cond-status-tag {
  font-size: 20rpx;
  font-weight: 600;
  padding: 3rpx 12rpx;
  border-radius: var(--radius-full);
}
.prog-tag--met   { background: var(--bhp-success-50, #f0fdf4); color: var(--bhp-success-600, #16a34a); }
.prog-tag--unmet { background: var(--bhp-gray-100); color: var(--text-tertiary); }

.prog-bar-row { display: flex; align-items: center; gap: 16rpx; }
.prog-bar {
  flex: 1;
  height: 10rpx;
  background: var(--bhp-gray-200);
  border-radius: 9999px;
  overflow: hidden;
}
.prog-bar-fill { height: 100%; border-radius: 9999px; transition: width 0.6s; }
.prog-bar-fill--growth       { background: var(--bhp-success-500, #22c55e); }
.prog-bar-fill--contribution { background: var(--bhp-primary-500); }
.prog-bar-fill--influence    { background: var(--bhp-warn-500, #f59e0b); }
.prog-bar-fill--companion    { background: #a855f7; }
.prog-bar-text { font-size: 22rpx; color: var(--text-secondary); white-space: nowrap; }

.prog-cond-action { margin-top: 12rpx; }

/* 综合进度 */
.prog-overall { padding-top: 16rpx; }
.prog-overall__row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10rpx; }
.prog-overall__label { font-size: 26rpx; font-weight: 500; color: var(--text-primary); }
.prog-overall__pct   { font-size: 28rpx; font-weight: 700; }
.prog-overall__bar {
  height: 12rpx;
  background: var(--bhp-gray-200);
  border-radius: 9999px;
  overflow: hidden;
  margin-bottom: 16rpx;
}
.prog-overall__fill {
  height: 100%;
  background: linear-gradient(90deg, var(--bhp-primary-400, #34d399), var(--bhp-primary-500));
  border-radius: 9999px;
  transition: width 0.8s;
}
.prog-overall__apply-btn {
  text-align: center;
  padding: 16rpx;
  background: var(--bhp-primary-500);
  border-radius: var(--radius-lg);
  font-size: 26rpx;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.prog-overall__hint { font-size: 22rpx; color: var(--text-tertiary); text-align: center; }

/* 快捷入口 */
.prog-shortcuts { padding-top: 16rpx; display: flex; flex-direction: column; gap: 10rpx; }
.prog-shortcut {
  display: flex;
  align-items: center;
  gap: 16rpx;
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 18rpx 24rpx;
  cursor: pointer;
  box-shadow: var(--shadow-card);
}
.prog-shortcut:active { opacity: 0.8; }
.prog-shortcut__icon  { font-size: 32rpx; }
.prog-shortcut__label { flex: 1; font-size: 26rpx; color: var(--text-primary); }
.prog-shortcut__arrow { font-size: 32rpx; color: var(--text-tertiary); }
</style>
