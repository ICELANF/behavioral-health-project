<template>
  <view class="qr-page">

    <!-- 结果卡 -->
    <view class="qr-result-card px-4">
      <!-- 通过/不通过图标 -->
      <view class="qr-result-icon" :class="passed ? 'qr-result-icon--pass' : 'qr-result-icon--fail'">
        <text>{{ passed ? '🎉' : '😔' }}</text>
      </view>

      <text class="qr-result-title">{{ passed ? '测验通过！' : '未达到通过分数' }}</text>

      <!-- 分数大圆环 -->
      <view class="qr-score-ring">
        <view class="qr-score-ring__inner" :class="passed ? 'qr-score-ring__inner--pass' : 'qr-score-ring__inner--fail'">
          <text class="qr-score-ring__value">{{ score }}</text>
          <text class="qr-score-ring__unit">分</text>
        </view>
        <text class="qr-score-ring__pass-line">及格线 {{ passScore }} 分</text>
      </view>

      <!-- 统计 -->
      <view class="qr-stats-row">
        <view class="qr-stat">
          <text class="qr-stat__value">{{ correctCount }}</text>
          <text class="qr-stat__label">答对</text>
        </view>
        <view class="qr-stat-divider"></view>
        <view class="qr-stat">
          <text class="qr-stat__value">{{ totalCount - correctCount }}</text>
          <text class="qr-stat__label">答错</text>
        </view>
        <view class="qr-stat-divider"></view>
        <view class="qr-stat">
          <text class="qr-stat__value">{{ totalCount }}</text>
          <text class="qr-stat__label">总题数</text>
        </view>
      </view>
    </view>

    <!-- 奖励区（通过时展示）-->
    <view class="qr-rewards px-4" v-if="passed && (pointsEarned > 0 || creditsEarned > 0)">
      <view class="qr-rewards__card">
        <text class="qr-rewards__title">🏆 获得奖励</text>
        <view class="qr-rewards__row">
          <view class="qr-reward-item" v-if="pointsEarned > 0">
            <text class="qr-reward-item__value">+{{ pointsEarned }}</text>
            <text class="qr-reward-item__label">成长积分</text>
          </view>
          <view class="qr-reward-divider" v-if="pointsEarned > 0 && creditsEarned > 0"></view>
          <view class="qr-reward-item" v-if="creditsEarned > 0">
            <text class="qr-reward-item__value">+{{ creditsEarned }}</text>
            <text class="qr-reward-item__label">学分</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 未通过：鼓励文案 -->
    <view class="qr-retry-tip px-4" v-if="!passed">
      <view class="qr-retry-tip__card">
        <text class="qr-retry-tip__text">
          差一点就通过了！不要气馁，复习相关内容后再来挑战吧 💪
        </text>
      </view>
    </view>

    <!-- 操作按钮 -->
    <view class="qr-actions px-4">
      <view class="bhp-btn bhp-btn--primary bhp-btn--full mb-3" @tap="goBack">
        <text>返回学习</text>
      </view>
      <view class="bhp-btn bhp-btn--secondary bhp-btn--full" @tap="retakeQuiz" v-if="!passed">
        <text>再次挑战</text>
      </view>
      <view class="bhp-btn bhp-btn--ghost bhp-btn--full" @tap="goLearning" v-else>
        <text>继续学习</text>
      </view>
    </view>

    <view style="height: 60rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const score        = ref(0)
const passScore    = ref(60)
const passed       = ref(false)
const pointsEarned = ref(0)
const creditsEarned= ref(0)
const correctCount = ref(0)
const totalCount   = ref(0)
const contentId    = ref(0)

onMounted(() => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}

  score.value         = Number(query.score || 0)
  passScore.value     = Number(query.pass_score || 60)
  passed.value        = query.pass === '1' || query.pass === 'true'
  pointsEarned.value  = Number(query.points_earned || 0)
  creditsEarned.value = Number(query.credits_earned || 0)
  correctCount.value  = Number(query.correct_count || 0)
  totalCount.value    = Number(query.total_count || 0)
  contentId.value     = Number(query.content_id || 0)

  // 更新本地积分
  if (passed.value && pointsEarned.value > 0) {
    userStore.addPoints(pointsEarned.value, 0, 0)
  }
})

function goBack() {
  uni.navigateBack()
}

function retakeQuiz() {
  // 返回两层（quiz → content-detail/video）
  uni.navigateBack({ delta: 2 })
}

function goLearning() {
  uni.switchTab
    ? uni.switchTab({ url: '/pages/learning/index' })
    : uni.navigateTo({ url: '/pages/learning/index' })
}
</script>

<style scoped>
.qr-page { background: var(--surface-secondary); min-height: 100vh; }

/* 结果卡 */
.qr-result-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 60rpx;
  padding-bottom: 40rpx;
  background: var(--surface);
  margin-bottom: 16rpx;
}

.qr-result-icon {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 60rpx;
  margin-bottom: 16rpx;
}
.qr-result-icon--pass { background: var(--bhp-success-50, #f0fdf4); }
.qr-result-icon--fail { background: var(--bhp-gray-100); }

.qr-result-title {
  font-size: 36rpx;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 32rpx;
}

/* 分数圆环 */
.qr-score-ring {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32rpx;
}
.qr-score-ring__inner {
  width: 180rpx;
  height: 180rpx;
  border-radius: 50%;
  border: 8rpx solid var(--bhp-gray-200);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 12rpx;
}
.qr-score-ring__inner--pass { border-color: var(--bhp-success-400, #4ade80); }
.qr-score-ring__inner--fail { border-color: var(--bhp-error-300, #fca5a5); }
.qr-score-ring__value { font-size: 60rpx; font-weight: 700; color: var(--text-primary); line-height: 1; }
.qr-score-ring__unit  { font-size: 24rpx; color: var(--text-secondary); }
.qr-score-ring__pass-line { font-size: 22rpx; color: var(--text-tertiary); }

/* 统计行 */
.qr-stats-row {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 0 40rpx;
}
.qr-stat { flex: 1; text-align: center; }
.qr-stat__value { display: block; font-size: 40rpx; font-weight: 700; color: var(--text-primary); }
.qr-stat__label { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }
.qr-stat-divider { width: 1px; height: 50rpx; background: var(--border-light); }

/* 奖励 */
.qr-rewards { margin-bottom: 16rpx; }
.qr-rewards__card {
  background: linear-gradient(135deg, var(--bhp-warn-50, #fffbeb), var(--bhp-warn-100, #fef3c7));
  border: 1px solid var(--bhp-warn-200, #fde68a);
  border-radius: var(--radius-xl, 16px);
  padding: 28rpx 32rpx;
}
.qr-rewards__title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: var(--bhp-warn-700, #b45309);
  margin-bottom: 20rpx;
}
.qr-rewards__row { display: flex; align-items: center; justify-content: center; gap: 40rpx; }
.qr-reward-item { text-align: center; }
.qr-reward-item__value {
  display: block;
  font-size: 48rpx;
  font-weight: 700;
  color: var(--bhp-warn-600, #d97706);
}
.qr-reward-item__label { display: block; font-size: 22rpx; color: var(--bhp-warn-500, #f59e0b); margin-top: 4rpx; }
.qr-reward-divider { width: 1px; height: 60rpx; background: var(--bhp-warn-200, #fde68a); }

/* 未通过提示 */
.qr-retry-tip { margin-bottom: 16rpx; }
.qr-retry-tip__card {
  background: var(--bhp-gray-50, #f9fafb);
  border-radius: var(--radius-lg);
  padding: 20rpx 24rpx;
}
.qr-retry-tip__text { font-size: 26rpx; color: var(--text-secondary); line-height: 1.6; }

/* 操作按钮 */
.qr-actions { padding-top: 8rpx; }
</style>
