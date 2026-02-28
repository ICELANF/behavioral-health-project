<template>
  <view class="exam-result-page">

    <!-- 结果主卡 -->
    <view class="er-hero" :class="passed ? 'er-hero--pass' : 'er-hero--fail'">
      <view class="er-hero__icon">
        <text>{{ passed ? '🎉' : '😔' }}</text>
      </view>
      <text class="er-hero__title">{{ passed ? '认证通过！' : '未达及格线' }}</text>
      <text class="er-hero__sub">
        {{ passed ? `您已通过 ${targetLevel} 等级认证考试` : `还差 ${passScore - score} 分即可通过` }}
      </text>

      <!-- 得分圆 -->
      <view class="er-score-wrap">
        <view class="er-score-circle">
          <text class="er-score-circle__val">{{ score }}</text>
          <text class="er-score-circle__unit">分</text>
        </view>
        <text class="er-score-pass-line">及格线 {{ passScore }} 分</text>
      </view>

      <!-- 统计行 -->
      <view class="er-stats">
        <view class="er-stat-item">
          <text class="er-stat-item__val">{{ correctCount }}</text>
          <text class="er-stat-item__lbl">答对</text>
        </view>
        <view class="er-stat-divider"></view>
        <view class="er-stat-item">
          <text class="er-stat-item__val">{{ totalCount - correctCount }}</text>
          <text class="er-stat-item__lbl">答错</text>
        </view>
        <view class="er-stat-divider"></view>
        <view class="er-stat-item">
          <text class="er-stat-item__val">{{ totalCount }}</text>
          <text class="er-stat-item__lbl">总题</text>
        </view>
      </view>
    </view>

    <!-- 通过：奖励 + 晋级提示 -->
    <view class="er-section px-4" v-if="passed">

      <!-- 奖励卡 -->
      <view class="er-reward-card" v-if="pointsEarned > 0 || creditsEarned > 0">
        <text class="er-reward-card__title">🏆 考试奖励</text>
        <view class="er-reward-card__row">
          <view class="er-reward-item" v-if="pointsEarned > 0">
            <text class="er-reward-item__val">+{{ pointsEarned }}</text>
            <text class="er-reward-item__lbl">成长积分</text>
          </view>
          <view class="er-reward-divider" v-if="pointsEarned > 0 && creditsEarned > 0"></view>
          <view class="er-reward-item" v-if="creditsEarned > 0">
            <text class="er-reward-item__val">+{{ creditsEarned }}</text>
            <text class="er-reward-item__lbl">学分</text>
          </view>
        </view>
      </view>

      <!-- 晋级解锁提示 -->
      <view class="er-promotion-tip" v-if="promotionUnlocked">
        <text class="er-promotion-tip__icon">🚀</text>
        <view class="er-promotion-tip__body">
          <text class="er-promotion-tip__title">晋级资质已解锁！</text>
          <text class="er-promotion-tip__sub">满足晋级条件后，可前往「成长路径」提交晋级申请</text>
        </view>
        <view class="bhp-btn" style="padding: 8rpx 24rpx; background: var(--bhp-primary-500); color:#fff; font-size:24rpx;" @tap="goPromotion">
          <text>去申请</text>
        </view>
      </view>
    </view>

    <!-- 未通过：分析 + 建议 -->
    <view class="er-section px-4" v-else>
      <view class="er-fail-analysis bhp-card bhp-card--flat">
        <text class="er-fail-analysis__title">复习建议</text>
        <view class="er-fail-tip-item">
          <text class="er-fail-tip-item__icon">📚</text>
          <text class="er-fail-tip-item__text">仔细复习对应模块的学习内容，重点关注薄弱知识点</text>
        </view>
        <view class="er-fail-tip-item">
          <text class="er-fail-tip-item__icon">🧩</text>
          <text class="er-fail-tip-item__text">完成随堂测验，巩固知识记忆</text>
        </view>
        <view class="er-fail-tip-item">
          <text class="er-fail-tip-item__icon">⏰</text>
          <text class="er-fail-tip-item__text">24小时后可再次参加考试，不限次数</text>
        </view>
      </view>
    </view>

    <!-- 错题解析（若有）-->
    <view class="er-section px-4" v-if="loadingAnalysis">
      <view class="bhp-skeleton" style="height: 160rpx; border-radius: var(--radius-lg);"></view>
    </view>
    <view class="er-section px-4" v-else-if="wrongCount > 0">
      <view class="er-wrong-card bhp-card bhp-card--flat">
        <view class="er-wrong-card__header">
          <text class="er-wrong-card__title">错题解析</text>
          <text class="er-wrong-card__count">{{ wrongCount }} 道</text>
        </view>
        <text class="text-sm text-secondary-color" style="margin-top: 8rpx; display: block;">
          错题解析已记录，建议重点复习这些知识点
        </text>
      </view>
    </view>

    <!-- 操作按钮 -->
    <view class="er-actions px-4">
      <view class="bhp-btn bhp-btn--primary bhp-btn--full mb-3" @tap="goHome">
        <text>返回考试中心</text>
      </view>
      <view class="bhp-btn bhp-btn--secondary bhp-btn--full mb-3" @tap="goLearning">
        <text>继续学习</text>
      </view>
      <view class="bhp-btn bhp-btn--ghost bhp-btn--full" @tap="goHistory">
        <text>查看历史记录</text>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { certExamApi } from '@/api/exam'

const userStore = useUserStore()

const score            = ref(0)
const passScore        = ref(60)
const passed           = ref(false)
const pointsEarned     = ref(0)
const creditsEarned    = ref(0)
const correctCount     = ref(0)
const totalCount       = ref(0)
const promotionUnlocked= ref(false)
const examId           = ref(0)
const sessionId        = ref(0)
const targetLevel      = ref('')
const wrongCount       = ref(0)
const loadingAnalysis  = ref(false)

onMounted(async () => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}

  score.value             = Number(query.score || 0)
  passScore.value         = Number(query.pass_score || 60)
  passed.value            = query.pass === '1' || query.pass === 'true'
  pointsEarned.value      = Number(query.points_earned || 0)
  creditsEarned.value     = Number(query.credits_earned || 0)
  correctCount.value      = Number(query.correct_count || 0)
  totalCount.value        = Number(query.total_count || 0)
  promotionUnlocked.value = query.promotion_unlocked === '1'
  examId.value            = Number(query.exam_id || 0)
  sessionId.value         = Number(query.session_id || 0)
  wrongCount.value        = totalCount.value - correctCount.value

  // 从 session 详情获取 target_level 等附加信息
  if (sessionId.value) await loadSessionDetail()

  // 更新本地积分
  if (passed.value && pointsEarned.value > 0) {
    userStore.addPoints(pointsEarned.value, 0, 0)
  }
})

async function loadSessionDetail() {
  loadingAnalysis.value = true
  try {
    const detail = await certExamApi.sessionResult(sessionId.value)
    wrongCount.value = detail.wrong_ids?.length || wrongCount.value
  } catch { /* 静默 */ } finally {
    loadingAnalysis.value = false
  }
}

function goHome() {
  uni.navigateBack({ delta: 3 }) // session → intro → index
}

function goLearning() {
  uni.navigateTo({ url: '/pages/learning/index' })
}

function goHistory() {
  uni.navigateTo({ url: '/pages/exam/history' })
}

function goPromotion() {
  uni.navigateTo({ url: '/pages/journey/promotion' })
}
</script>

<style scoped>
.exam-result-page { background: var(--surface-secondary); min-height: 100vh; }

/* 顶部英雄区 */
.er-hero {
  padding: 60rpx 32rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.er-hero--pass { background: linear-gradient(160deg, #d1fae5, #a7f3d0); }
.er-hero--fail { background: linear-gradient(160deg, var(--bhp-gray-100), var(--bhp-gray-200)); }

.er-hero__icon { font-size: 80rpx; margin-bottom: 12rpx; }
.er-hero__title {
  font-size: 40rpx;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8rpx;
}
.er-hero__sub { font-size: 24rpx; color: var(--text-secondary); margin-bottom: 32rpx; text-align: center; }

/* 分数圆 */
.er-score-wrap { display: flex; flex-direction: column; align-items: center; margin-bottom: 32rpx; }
.er-score-circle {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background: rgba(255,255,255,0.7);
  border: 6rpx solid rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 8rpx;
}
.er-score-circle__val { font-size: 56rpx; font-weight: 700; color: var(--text-primary); line-height: 1; }
.er-score-circle__unit{ font-size: 22rpx; color: var(--text-secondary); }
.er-score-pass-line { font-size: 20rpx; color: var(--text-tertiary); }

/* 统计 */
.er-stats { display: flex; align-items: center; gap: 40rpx; }
.er-stat-item { text-align: center; }
.er-stat-item__val { display: block; font-size: 40rpx; font-weight: 700; color: var(--text-primary); }
.er-stat-item__lbl { display: block; font-size: 20rpx; color: var(--text-secondary); margin-top: 4rpx; }
.er-stat-divider { width: 1px; height: 48rpx; background: rgba(0,0,0,0.15); }

/* 区块 */
.er-section { padding-top: 16rpx; }

/* 奖励卡 */
.er-reward-card {
  background: linear-gradient(135deg, var(--bhp-warn-50, #fffbeb), var(--bhp-warn-100, #fef3c7));
  border: 1px solid var(--bhp-warn-200, #fde68a);
  border-radius: var(--radius-xl, 16px);
  padding: 24rpx 28rpx;
  margin-bottom: 12rpx;
}
.er-reward-card__title { display: block; font-size: 26rpx; font-weight: 700; color: var(--bhp-warn-700, #b45309); margin-bottom: 16rpx; }
.er-reward-card__row   { display: flex; align-items: center; justify-content: center; gap: 48rpx; }
.er-reward-item { text-align: center; }
.er-reward-item__val { display: block; font-size: 48rpx; font-weight: 700; color: var(--bhp-warn-600, #d97706); }
.er-reward-item__lbl { display: block; font-size: 22rpx; color: var(--bhp-warn-500, #f59e0b); margin-top: 4rpx; }
.er-reward-divider { width: 1px; height: 60rpx; background: var(--bhp-warn-200, #fde68a); }

/* 晋级提示 */
.er-promotion-tip {
  display: flex;
  align-items: center;
  gap: 16rpx;
  background: var(--bhp-primary-50);
  border: 1px solid var(--bhp-primary-200, #a7f3d0);
  border-radius: var(--radius-lg);
  padding: 20rpx 24rpx;
}
.er-promotion-tip__icon { font-size: 40rpx; }
.er-promotion-tip__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--bhp-primary-700, #047857); }
.er-promotion-tip__sub   { display: block; font-size: 20rpx; color: var(--bhp-primary-600, #059669); margin-top: 4rpx; }

/* 复习建议 */
.er-fail-analysis__title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 16rpx; }
.er-fail-tip-item { display: flex; gap: 12rpx; margin-bottom: 12rpx; align-items: flex-start; }
.er-fail-tip-item__icon { font-size: 28rpx; }
.er-fail-tip-item__text { font-size: 26rpx; color: var(--text-secondary); line-height: 1.5; flex: 1; }

/* 错题卡 */
.er-wrong-card__header { display: flex; align-items: center; justify-content: space-between; }
.er-wrong-card__title { font-size: 26rpx; font-weight: 700; color: var(--text-primary); }
.er-wrong-card__count { font-size: 24rpx; color: var(--bhp-error-500, #ef4444); font-weight: 600; }

/* 操作区 */
.er-actions { padding-top: 16rpx; }
</style>
