<template>
  <view class="promo-page">

    <!-- 标题卡：当前→目标 -->
    <view class="promo-header px-4">
      <view class="promo-header__card">
        <view class="promo-header__from">
          <view class="promo-header__level-dot" :style="{ background: currentMeta.color }">
            <text>{{ currentMeta.icon }}</text>
          </view>
          <text class="promo-header__level-label" :style="{ color: currentMeta.color }">{{ currentMeta.label }}</text>
        </view>
        <view class="promo-header__arrow">
          <text>→</text>
        </view>
        <view class="promo-header__to">
          <view class="promo-header__level-dot" :style="{ background: nextMeta?.color || '#e5e7eb' }">
            <text>{{ nextMeta?.icon || '?' }}</text>
          </view>
          <text class="promo-header__level-label" :style="{ color: nextMeta?.color || '#9ca3af' }">{{ nextMeta?.label || '未知' }}</text>
        </view>
      </view>
    </view>

    <!-- 已达顶级 -->
    <view class="promo-maxed px-4" v-if="!nextLevelKey">
      <view class="bhp-card bhp-card--flat" style="padding: 48rpx; text-align: center;">
        <text style="font-size: 80rpx; display: block; margin-bottom: 16rpx;">🏆</text>
        <text style="font-size: 28rpx; font-weight: 700; color: var(--text-primary);">您已是最高等级 L5 大师</text>
      </view>
    </view>

    <template v-else>
      <!-- 资格检查 -->
      <view class="promo-check-section px-4">
        <text class="promo-section-title">晋级条件检查</text>

        <!-- 骨架屏 -->
        <template v-if="loadingCheck">
          <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 80rpx; margin-bottom: 10rpx; border-radius: var(--radius-lg);"></view>
        </template>

        <template v-else>
          <view
            v-for="cond in conditions"
            :key="cond.key"
            class="promo-cond-item"
            :class="cond.met ? 'promo-cond-item--met' : 'promo-cond-item--unmet'"
          >
            <view class="promo-cond-item__check">
              <text>{{ cond.met ? '✓' : '✗' }}</text>
            </view>
            <view class="promo-cond-item__body">
              <text class="promo-cond-item__label">{{ cond.label }}</text>
              <text class="promo-cond-item__detail">{{ cond.detail }}</text>
            </view>
            <view
              v-if="!cond.met && cond.actionUrl"
              class="promo-cond-item__action"
              @tap="cond.action && cond.action()"
            >
              <text>去完成 ›</text>
            </view>
          </view>

          <!-- 全满足 banner -->
          <view class="promo-all-met" v-if="allMet">
            <text class="promo-all-met__icon">🎉</text>
            <text class="promo-all-met__text">所有条件已满足，可提交申请！</text>
          </view>
        </template>
      </view>

      <!-- 申请表单 -->
      <view class="promo-form-section px-4">
        <text class="promo-section-title">申请信息</text>

        <view class="promo-form-card bhp-card bhp-card--flat">
          <text class="promo-form-label">申请理由 <text style="color: var(--text-tertiary); font-size: 22rpx;">（选填）</text></text>
          <textarea
            class="promo-form-textarea"
            v-model="reason"
            placeholder="简述您在本等级的成长经历、重要贡献或心得体会..."
            placeholder-class="promo-textarea-placeholder"
            :maxlength="500"
            auto-height
          />
          <text class="promo-form-count">{{ reason.length }}/500</text>
        </view>
      </view>

      <!-- 提交按钮 -->
      <view class="promo-submit px-4">
        <view
          class="promo-submit-btn"
          :class="{
            'promo-submit-btn--active':   allMet && !submitting,
            'promo-submit-btn--disabled': !allMet || submitting
          }"
          @tap="submitApplication"
        >
          <text v-if="submitting">提交中...</text>
          <text v-else-if="!allMet">条件未满足，暂不可申请</text>
          <text v-else>提交晋级申请 🚀</text>
        </view>

        <!-- 未满足提示 -->
        <view class="promo-submit__hint" v-if="!allMet && !loadingCheck">
          <text class="text-xs text-secondary-color">
            还有 {{ unmetCount }} 项条件未达到，请继续努力
          </text>
        </view>
      </view>

      <!-- 说明 -->
      <view class="promo-notice px-4">
        <view class="promo-notice__card bhp-card bhp-card--flat">
          <text class="promo-notice__title">📋 申请须知</text>
          <text class="promo-notice__item">• 申请提交后由督导专家在 3-7 个工作日内审核</text>
          <text class="promo-notice__item">• 审核通过后立即升级，积分和权限同步更新</text>
          <text class="promo-notice__item">• 审核不通过会附说明，30天后可重新申请</text>
          <text class="promo-notice__item">• 可前往「申请记录」查看审核状态</text>
        </view>
      </view>
    </template>

    <view style="height: 60rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { promotionApi, companionApi, LEVEL_META, LEVEL_THRESHOLDS } from '@/api/journey'

const userStore = useUserStore()

const reason       = ref('')
const loadingCheck = ref(false)
const submitting   = ref(false)
const companionCount  = ref(0)
const examPassed   = ref(false)
const hasPending   = ref(false)

const ROLE_TO_LEVEL: Record<string, number> = {
  observer: 0, grower: 1, sharer: 2, coach: 3, promoter: 4, supervisor: 4, master: 5
}

const currentLevelNum = computed(() => ROLE_TO_LEVEL[userStore.role] ?? 0)
const nextLevelNum    = computed(() => currentLevelNum.value < 5 ? currentLevelNum.value + 1 : null)
const nextLevelKey    = computed(() => nextLevelNum.value !== null ? `L${nextLevelNum.value}` : null)
const currentMeta     = computed(() => LEVEL_META[`L${currentLevelNum.value}`] || LEVEL_META['L0'])
const nextMeta        = computed(() => nextLevelKey.value ? LEVEL_META[nextLevelKey.value] : null)
const nextReq         = computed(() => nextLevelKey.value ? LEVEL_THRESHOLDS[nextLevelKey.value] : null)

interface Condition {
  key: string
  label: string
  detail: string
  met: boolean
  actionUrl?: string
  action?: () => void
}

const conditions = computed<Condition[]>(() => {
  const req = nextReq.value
  if (!req) return []
  const items: Condition[] = []

  // 成长积分
  if (req.growth > 0) {
    const met = userStore.growthPoints >= req.growth
    items.push({
      key: 'growth', label: '成长积分',
      detail: `${userStore.growthPoints} / ${req.growth}（${met ? '已满足' : `还差 ${req.growth - userStore.growthPoints}`}）`,
      met, actionUrl: '/pages/learning/index',
      action: () => uni.navigateTo({ url: '/pages/learning/index' })
    })
  }

  // 贡献积分
  if (req.contribution > 0) {
    const met = userStore.contributionPts >= req.contribution
    items.push({
      key: 'contribution', label: '贡献积分',
      detail: `${userStore.contributionPts} / ${req.contribution}（${met ? '已满足' : `还差 ${req.contribution - userStore.contributionPts}`}）`,
      met, actionUrl: '/pages/learning/index',
      action: () => uni.navigateTo({ url: '/pages/learning/index' })
    })
  }

  // 影响积分
  if (req.influence > 0) {
    const met = userStore.influencePts >= req.influence
    items.push({
      key: 'influence', label: '影响积分',
      detail: `${userStore.influencePts} / ${req.influence}（${met ? '已满足' : `还差 ${req.influence - userStore.influencePts}`}）`,
      met, actionUrl: '/pages/learning/index',
      action: () => uni.navigateTo({ url: '/pages/learning/index' })
    })
  }

  // 认证考试
  if (req.exam) {
    items.push({
      key: 'exam', label: `通过 ${nextLevelKey.value} 认证考试`,
      detail: examPassed.value ? '已通过 ✓' : '尚未通过认证考试',
      met: examPassed.value, actionUrl: '/pages/exam/index',
      action: () => uni.navigateTo({ url: '/pages/exam/index' })
    })
  }

  // 同道者
  if (req.companions > 0) {
    const met = companionCount.value >= req.companions
    items.push({
      key: 'companions', label: `${req.companions} 位≥${req.companion_min_level}同道者`,
      detail: `已有 ${companionCount.value} / ${req.companions} 位符合条件的同道者`,
      met, actionUrl: '/pages/companions/index',
      action: () => uni.navigateTo({ url: '/pages/companions/index' })
    })
  }

  return items
})

const allMet    = computed(() => conditions.value.length > 0 && conditions.value.every(c => c.met))
const unmetCount= computed(() => conditions.value.filter(c => !c.met).length)

onMounted(async () => {
  await loadCheckData()
})

async function loadCheckData() {
  loadingCheck.value = true
  try {
    const [eligibility, companions] = await Promise.all([
      promotionApi.checkEligibility().catch(() => null),
      companionApi.mySummary().catch(() => null)
    ])
    if (eligibility) {
      examPassed.value = eligibility.conditions.find(c => c.key === 'exam')?.met ?? false
    }
    if (companions) {
      companionCount.value = companions.qualified || companions.total || 0
    }
    // 检查是否有待审核的申请
    const history = await promotionApi.myHistory(1).catch(() => null)
    if (history?.items?.length) {
      hasPending.value = history.items[0].status === 'pending'
    }
  } catch { /* 静默，使用本地数据 */ } finally {
    loadingCheck.value = false
  }
}

async function submitApplication() {
  if (!allMet.value || submitting.value) return
  if (hasPending.value) {
    uni.showToast({ title: '您有一个待审核的申请', icon: 'none' })
    return
  }
  uni.showModal({
    title: '确认提交',
    content: `确认提交从 ${currentMeta.value.label} 晋升至 ${nextMeta.value?.label} 的申请吗？`,
    confirmText: '确认提交',
    success: async (res) => {
      if (!res.confirm) return
      submitting.value = true
      try {
        await promotionApi.apply({ reason: reason.value || undefined })
        uni.showToast({ title: '申请已提交！', icon: 'success', duration: 2000 })
        setTimeout(() => {
          uni.redirectTo({ url: '/pages/journey/history' })
        }, 2000)
      } catch (e: any) {
        const msg = e?.message || '提交失败，请重试'
        uni.showToast({ title: msg, icon: 'none' })
      } finally {
        submitting.value = false
      }
    }
  })
}
</script>

<style scoped>
.promo-page { background: var(--surface-secondary); min-height: 100vh; }

/* 标题卡 */
.promo-header { padding-top: 16rpx; }
.promo-header__card {
  background: var(--surface);
  border-radius: var(--radius-xl, 16px);
  padding: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32rpx;
  box-shadow: var(--shadow-card);
}
.promo-header__from,
.promo-header__to {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}
.promo-header__level-dot {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
}
.promo-header__level-label { font-size: 22rpx; font-weight: 700; }
.promo-header__arrow { font-size: 48rpx; color: var(--text-tertiary); }

/* 条件区 */
.promo-check-section { padding-top: 24rpx; }
.promo-section-title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12rpx;
}

.promo-cond-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 20rpx;
  border-radius: var(--radius-lg);
  margin-bottom: 10rpx;
  border: 1px solid transparent;
}
.promo-cond-item--met   { background: var(--bhp-success-50, #f0fdf4); border-color: var(--bhp-success-200, #bbf7d0); }
.promo-cond-item--unmet { background: var(--surface); border-color: var(--border-light); }

.promo-cond-item__check {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 700;
  flex-shrink: 0;
}
.promo-cond-item--met   .promo-cond-item__check { background: var(--bhp-success-500, #22c55e); color: #fff; }
.promo-cond-item--unmet .promo-cond-item__check { background: var(--bhp-gray-200); color: var(--text-tertiary); }

.promo-cond-item__body { flex: 1; overflow: hidden; }
.promo-cond-item__label  { display: block; font-size: 26rpx; font-weight: 500; color: var(--text-primary); }
.promo-cond-item__detail { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }

.promo-cond-item__action {
  font-size: 22rpx;
  color: var(--bhp-primary-500);
  cursor: pointer;
  white-space: nowrap;
}

.promo-all-met {
  display: flex;
  align-items: center;
  gap: 12rpx;
  background: var(--bhp-success-50, #f0fdf4);
  border-radius: var(--radius-lg);
  padding: 16rpx 20rpx;
  margin-top: 8rpx;
  border: 1px solid var(--bhp-success-200, #bbf7d0);
}
.promo-all-met__icon { font-size: 32rpx; }
.promo-all-met__text { font-size: 26rpx; color: var(--bhp-success-700, #15803d); font-weight: 600; }

/* 表单 */
.promo-form-section { padding-top: 24rpx; }
.promo-form-card { padding: 20rpx 24rpx; }
.promo-form-label {
  display: block;
  font-size: 26rpx;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 12rpx;
}
.promo-form-textarea {
  width: 100%;
  min-height: 160rpx;
  font-size: 26rpx;
  color: var(--text-primary);
  background: var(--bhp-gray-50, #f9fafb);
  border-radius: var(--radius-md);
  padding: 16rpx;
  line-height: 1.6;
  box-sizing: border-box;
}
.promo-textarea-placeholder { color: var(--text-tertiary); font-size: 26rpx; }
.promo-form-count { display: block; text-align: right; font-size: 20rpx; color: var(--text-tertiary); margin-top: 8rpx; }

/* 提交按钮 */
.promo-submit { padding-top: 24rpx; }
.promo-submit-btn {
  text-align: center;
  padding: 24rpx;
  border-radius: var(--radius-lg);
  font-size: 28rpx;
  font-weight: 700;
  cursor: pointer;
}
.promo-submit-btn--active   { background: var(--bhp-primary-500); color: #fff; }
.promo-submit-btn--disabled { background: var(--bhp-gray-200); color: var(--text-tertiary); pointer-events: none; }
.promo-submit__hint { text-align: center; margin-top: 10rpx; }

/* 说明 */
.promo-notice { padding-top: 20rpx; }
.promo-notice__card { padding: 20rpx 24rpx; }
.promo-notice__title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 12rpx; }
.promo-notice__item  { display: block; font-size: 24rpx; color: var(--text-secondary); line-height: 1.8; }
</style>
