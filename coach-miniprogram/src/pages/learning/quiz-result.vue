<template>
  <view class="qr-page">
    <view class="qr-navbar safe-area-top">
      <view class="qr-navbar__back" @tap="goBack"><text class="qr-navbar__arrow">&#8249;</text></view>
      <text class="qr-navbar__title">测验结果</text>
      <view class="qr-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="qr-body">
      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 300rpx; border-radius: var(--radius-lg);"></view>
      </template>
      <template v-else-if="result">

        <!-- 得分环形图 -->
        <view class="qr-score-card">
          <view class="qr-ring">
            <view class="qr-ring__circle" :style="ringStyle"></view>
            <view class="qr-ring__inner">
              <text class="qr-ring__score">{{ result.score ?? 0 }}</text>
              <text class="qr-ring__total">/ {{ result.total_score ?? 100 }}</text>
            </view>
          </view>
          <view class="qr-score-info">
            <view class="qr-score-badge" :class="result.passed ? 'qr-score-badge--pass' : 'qr-score-badge--fail'">
              <text>{{ result.passed ? '通过' : '未通过' }}</text>
            </view>
            <text class="qr-score-detail">正确 {{ result.correct_count ?? 0 }}/{{ result.question_count ?? 0 }} 题</text>
          </view>
        </view>

        <!-- 答题明细 -->
        <view class="qr-section" v-if="result.answers?.length">
          <text class="qr-section__title">答题明细</text>
          <view v-for="(ans, idx) in result.answers" :key="idx" class="qr-answer" :class="ans.is_correct ? 'qr-answer--correct' : 'qr-answer--wrong'">
            <view class="qr-answer__header">
              <text class="qr-answer__num">{{ idx + 1 }}.</text>
              <text class="qr-answer__question">{{ ans.question || ans.title }}</text>
              <text class="qr-answer__icon">{{ ans.is_correct ? '&#10004;' : '&#10008;' }}</text>
            </view>
            <view class="qr-answer__body">
              <view class="qr-answer__row">
                <text class="qr-answer__label">你的答案：</text>
                <text class="qr-answer__val" :class="!ans.is_correct ? 'qr-answer__val--wrong' : ''">{{ ans.user_answer || '-' }}</text>
              </view>
              <view class="qr-answer__row" v-if="!ans.is_correct">
                <text class="qr-answer__label">正确答案：</text>
                <text class="qr-answer__val qr-answer__val--correct">{{ ans.correct_answer || '-' }}</text>
              </view>
              <view class="qr-answer__explain" v-if="ans.explanation">
                <text>{{ ans.explanation }}</text>
              </view>
            </view>
          </view>
        </view>

      </template>
    </scroll-view>

    <!-- 底部按钮 -->
    <view class="qr-footer safe-area-bottom" v-if="result">
      <view class="qr-footer__btn qr-footer__btn--retry" @tap="retryQuiz">
        <text>再做一次</text>
      </view>
      <view class="qr-footer__btn qr-footer__btn--back" @tap="goBack">
        <text>返回</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const result   = ref<any>(null)
const loading  = ref(false)
const quizId   = ref(0)

const ringStyle = computed(() => {
  const score = result.value?.score ?? 0
  const total = result.value?.total_score ?? 100
  const pct = Math.min(100, Math.round((score / total) * 100))
  const deg = (pct / 100) * 360
  const color = result.value?.passed ? 'var(--bhp-primary-500)' : '#ef4444'
  if (deg <= 180) {
    return { background: `conic-gradient(${color} ${deg}deg, var(--bhp-gray-100) ${deg}deg)` }
  }
  return { background: `conic-gradient(${color} ${deg}deg, var(--bhp-gray-100) ${deg}deg)` }
})

onMounted(() => {
  const pages = getCurrentPages()
  const pg = pages[pages.length - 1] as any
  quizId.value = Number(pg.$page?.options?.id || pg.options?.id || 0)
  if (quizId.value) loadResult()
})

async function loadResult() {
  loading.value = true
  try {
    result.value = await http.get<any>(`/v1/quiz/result/${quizId.value}`)
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function retryQuiz() {
  const examId = result.value?.exam_id || result.value?.quiz_id
  if (examId) {
    uni.redirectTo({ url: `/pages/exam/intro?id=${examId}` })
  } else {
    goBack()
  }
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.qr-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.qr-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.qr-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.qr-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.qr-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.qr-navbar__placeholder { width: 64rpx; }
.qr-body { flex: 1; padding: 20rpx 32rpx 160rpx; }

.qr-score-card {
  display: flex; align-items: center; gap: 32rpx;
  background: var(--surface); border-radius: var(--radius-lg); padding: 32rpx; margin-bottom: 24rpx; border: 1px solid var(--border-light);
}
.qr-ring { position: relative; width: 180rpx; height: 180rpx; flex-shrink: 0; }
.qr-ring__circle { width: 100%; height: 100%; border-radius: 50%; }
.qr-ring__inner {
  position: absolute; top: 20rpx; left: 20rpx; right: 20rpx; bottom: 20rpx;
  border-radius: 50%; background: var(--surface);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.qr-ring__score { font-size: 40rpx; font-weight: 800; color: var(--text-primary); }
.qr-ring__total { font-size: 22rpx; color: var(--text-tertiary); }
.qr-score-info { display: flex; flex-direction: column; gap: 12rpx; }
.qr-score-badge { padding: 8rpx 24rpx; border-radius: var(--radius-full); font-size: 26rpx; font-weight: 700; text-align: center; }
.qr-score-badge--pass { background: #dcfce7; color: #16a34a; }
.qr-score-badge--fail { background: #fee2e2; color: #dc2626; }
.qr-score-detail { font-size: 24rpx; color: var(--text-secondary); }

.qr-section { margin-bottom: 24rpx; }
.qr-section__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 16rpx; }

.qr-answer {
  background: var(--surface); border-radius: var(--radius-lg); padding: 20rpx; margin-bottom: 12rpx;
  border: 1px solid var(--border-light);
}
.qr-answer--correct { border-left: 6rpx solid #22c55e; }
.qr-answer--wrong { border-left: 6rpx solid #ef4444; }
.qr-answer__header { display: flex; align-items: flex-start; gap: 8rpx; margin-bottom: 12rpx; }
.qr-answer__num { font-size: 26rpx; font-weight: 700; color: var(--text-secondary); flex-shrink: 0; }
.qr-answer__question { font-size: 26rpx; color: var(--text-primary); flex: 1; }
.qr-answer__icon { font-size: 28rpx; flex-shrink: 0; }
.qr-answer--correct .qr-answer__icon { color: #22c55e; }
.qr-answer--wrong .qr-answer__icon { color: #ef4444; }
.qr-answer__body { padding-left: 32rpx; }
.qr-answer__row { display: flex; gap: 8rpx; margin-bottom: 4rpx; }
.qr-answer__label { font-size: 24rpx; color: var(--text-tertiary); flex-shrink: 0; }
.qr-answer__val { font-size: 24rpx; color: var(--text-primary); }
.qr-answer__val--wrong { color: #ef4444; text-decoration: line-through; }
.qr-answer__val--correct { color: #22c55e; font-weight: 600; }
.qr-answer__explain { margin-top: 8rpx; padding: 12rpx; background: var(--surface-secondary); border-radius: var(--radius-md); font-size: 22rpx; color: var(--text-secondary); }

.qr-footer {
  position: fixed; bottom: 0; left: 0; right: 0; display: flex; gap: 16rpx;
  padding: 16rpx 32rpx 24rpx; background: var(--surface); border-top: 1px solid var(--border-light);
}
.qr-footer__btn {
  flex: 1; height: 88rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 700; cursor: pointer;
}
.qr-footer__btn--retry { background: var(--bhp-primary-500); color: #fff; }
.qr-footer__btn--back { background: var(--surface-secondary); color: var(--text-secondary); border: 1px solid var(--border-light); }
.qr-footer__btn:active { opacity: 0.85; }
</style>
