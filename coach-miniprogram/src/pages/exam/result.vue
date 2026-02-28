<template>
  <view class="er-page">

    <!-- 导航栏 -->
    <view class="er-navbar safe-area-top">
      <view class="er-navbar__back" @tap="goBack">
        <text class="er-navbar__arrow">‹</text>
      </view>
      <text class="er-navbar__title">考试结果</text>
      <view class="er-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="er-body">

      <!-- 分数圆环 -->
      <view class="er-score-section">
        <view class="er-score-ring" :class="isPassed ? 'er-score-ring--pass' : 'er-score-ring--fail'">
          <text class="er-score-ring__num">{{ result?.score ?? 0 }}</text>
          <text class="er-score-ring__unit">分</text>
        </view>
        <view class="er-score-msg" v-if="isPassed">
          <text class="er-score-msg__text er-score-msg__text--pass">恭喜通过！+20积分</text>
        </view>
        <view class="er-score-msg" v-else>
          <text class="er-score-msg__text er-score-msg__text--fail">继续加油，还差{{ passGap }}分</text>
        </view>
      </view>

      <!-- 答题统计 -->
      <view class="er-card">
        <text class="er-card__title">答题统计</text>
        <view class="er-stats">
          <view class="er-stat">
            <text class="er-stat__val">{{ result?.total ?? 0 }}</text>
            <text class="er-stat__label">总题数</text>
          </view>
          <view class="er-stat">
            <text class="er-stat__val er-stat__val--correct">{{ result?.correct ?? 0 }}</text>
            <text class="er-stat__label">答对</text>
          </view>
          <view class="er-stat">
            <text class="er-stat__val er-stat__val--wrong">{{ result?.wrong ?? 0 }}</text>
            <text class="er-stat__label">答错</text>
          </view>
          <view class="er-stat">
            <text class="er-stat__val er-stat__val--skip">{{ result?.unanswered ?? 0 }}</text>
            <text class="er-stat__label">未答</text>
          </view>
        </view>
      </view>

      <!-- 得分明细（按题型） -->
      <view class="er-card" v-if="typeBreakdown.length">
        <text class="er-card__title">得分明细</text>
        <view class="er-breakdown">
          <view v-for="tb in typeBreakdown" :key="tb.type" class="er-bd-item">
            <text class="er-bd-item__type">{{ tb.label }}</text>
            <view class="er-bd-item__bar-wrap">
              <view class="er-bd-item__bar" :style="{ width: tb.pct + '%' }"></view>
            </view>
            <text class="er-bd-item__score">{{ tb.correct }}/{{ tb.total }}</text>
          </view>
        </view>
      </view>

      <!-- 错题回顾 -->
      <view class="er-card" v-if="wrongQuestions.length">
        <text class="er-card__title">错题回顾</text>
        <view class="er-wrong-list">
          <view v-for="(wq, idx) in wrongQuestions" :key="idx" class="er-wrong-item">
            <view class="er-wrong-item__head">
              <view class="er-wrong-item__num"><text>{{ idx + 1 }}</text></view>
              <text class="er-wrong-item__stem">{{ wq.title }}</text>
            </view>
            <view class="er-wrong-item__answer">
              <text class="er-wrong-item__label">正确答案：</text>
              <text class="er-wrong-item__correct">{{ formatAnswer(wq.correct_answer, wq.options) }}</text>
            </view>
            <view class="er-wrong-item__answer" v-if="wq.user_answer !== undefined">
              <text class="er-wrong-item__label">你的答案：</text>
              <text class="er-wrong-item__user">{{ formatAnswer(wq.user_answer, wq.options) }}</text>
            </view>
          </view>
        </view>
      </view>

    </scroll-view>

    <!-- 底部按钮 -->
    <view class="er-footer safe-area-bottom">
      <view class="er-footer__btn er-footer__btn--outline" @tap="retakeExam">
        <text>再做一次</text>
      </view>
      <view class="er-footer__btn er-footer__btn--primary" @tap="goBack">
        <text>返回课程</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const sessionId = ref(0)
const result    = ref<any>(null)

const PASS_SCORE = 60

const isPassed = computed(() => (result.value?.score ?? 0) >= PASS_SCORE)
const passGap  = computed(() => Math.max(0, PASS_SCORE - (result.value?.score ?? 0)))

const typeBreakdown = computed(() => {
  const bd = result.value?.type_breakdown || []
  return bd.map((item: any) => ({
    type:    item.type,
    label:   TYPE_LABELS[item.type] || item.type,
    correct: item.correct ?? 0,
    total:   item.total ?? 0,
    pct:     item.total > 0 ? Math.round((item.correct / item.total) * 100) : 0,
  }))
})

const wrongQuestions = computed(() => result.value?.wrong_questions || [])

const TYPE_LABELS: Record<string, string> = {
  single:      '单选题',
  multi:       '多选题',
  case_image:  '案例题(图)',
  case_video:  '案例题(视频)',
  case:        '案例题',
}

onLoad((query: any) => {
  sessionId.value = Number(query?.id || query?.session_id || 0)
})

onMounted(async () => {
  if (sessionId.value) await loadResult()
})

async function loadResult() {
  try {
    const res = await http.get<any>(`/v1/certification/sessions/${sessionId.value}/result`)
    result.value = res
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

function formatAnswer(answer: any, options: any[]): string {
  if (answer === null || answer === undefined) return '未作答'
  if (Array.isArray(answer)) {
    return answer.map(a => formatSingleAnswer(a, options)).join('、')
  }
  return formatSingleAnswer(answer, options)
}

function formatSingleAnswer(a: any, options: any[]): string {
  if (typeof a === 'number' && options?.[a]) {
    const opt = options[a]
    return String.fromCharCode(65 + a) + '. ' + (opt.text || opt)
  }
  return String(a)
}

function retakeExam() {
  const examId = result.value?.exam_id || result.value?.certification_id
  if (examId) {
    uni.redirectTo({ url: `/pages/exam/session?id=${examId}` })
  } else {
    uni.navigateBack()
  }
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.er-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

.er-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.er-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.er-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.er-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.er-navbar__placeholder { width: 64rpx; }

.er-body { flex: 1; padding: 20rpx 32rpx 200rpx; }

/* 分数圆环 */
.er-score-section {
  display: flex; flex-direction: column; align-items: center; padding: 40rpx 0 20rpx;
}
.er-score-ring {
  width: 240rpx; height: 240rpx; border-radius: 50%;
  display: flex; align-items: baseline; justify-content: center;
  padding-top: 72rpx; border: 8rpx solid;
}
.er-score-ring--pass { border-color: #10b981; background: rgba(16,185,129,0.06); }
.er-score-ring--fail { border-color: #ef4444; background: rgba(239,68,68,0.06); }
.er-score-ring__num { font-size: 80rpx; font-weight: 800; }
.er-score-ring--pass .er-score-ring__num { color: #10b981; }
.er-score-ring--fail .er-score-ring__num { color: #ef4444; }
.er-score-ring__unit { font-size: 28rpx; color: var(--text-secondary); margin-left: 4rpx; }

.er-score-msg { margin-top: 20rpx; }
.er-score-msg__text { font-size: 28rpx; font-weight: 700; }
.er-score-msg__text--pass { color: #10b981; }
.er-score-msg__text--fail { color: #ef4444; }

/* 卡片 */
.er-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light);
}
.er-card__title { font-size: 28rpx; font-weight: 700; color: var(--text-primary); display: block; margin-bottom: 16rpx; }

/* 答题统计 */
.er-stats { display: flex; gap: 8rpx; }
.er-stat {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4rpx;
  padding: 16rpx 0; background: var(--surface-secondary); border-radius: var(--radius-md);
}
.er-stat__val { font-size: 36rpx; font-weight: 800; color: var(--text-primary); }
.er-stat__val--correct { color: #10b981; }
.er-stat__val--wrong { color: #ef4444; }
.er-stat__val--skip { color: #f59e0b; }
.er-stat__label { font-size: 22rpx; color: var(--text-secondary); }

/* 得分明细 */
.er-breakdown { display: flex; flex-direction: column; gap: 16rpx; }
.er-bd-item { display: flex; align-items: center; gap: 12rpx; }
.er-bd-item__type { width: 140rpx; font-size: 24rpx; color: var(--text-secondary); text-align: right; flex-shrink: 0; }
.er-bd-item__bar-wrap { flex: 1; height: 20rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.er-bd-item__bar { height: 100%; background: var(--bhp-primary-500); border-radius: var(--radius-full); transition: width 0.5s; }
.er-bd-item__score { width: 80rpx; font-size: 24rpx; font-weight: 700; color: var(--text-primary); }

/* 错题回顾 */
.er-wrong-list { display: flex; flex-direction: column; gap: 20rpx; }
.er-wrong-item {
  padding: 16rpx; background: var(--surface-secondary); border-radius: var(--radius-md);
}
.er-wrong-item__head { display: flex; align-items: flex-start; gap: 12rpx; margin-bottom: 12rpx; }
.er-wrong-item__num {
  width: 40rpx; height: 40rpx; border-radius: 50%; flex-shrink: 0;
  background: #ef4444; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; font-weight: 700;
}
.er-wrong-item__stem { font-size: 26rpx; font-weight: 600; color: var(--text-primary); line-height: 1.5; flex: 1; }
.er-wrong-item__answer { display: flex; align-items: flex-start; gap: 4rpx; margin-top: 6rpx; padding-left: 52rpx; }
.er-wrong-item__label { font-size: 24rpx; color: var(--text-tertiary); flex-shrink: 0; }
.er-wrong-item__correct { font-size: 24rpx; color: #10b981; font-weight: 600; flex: 1; }
.er-wrong-item__user { font-size: 24rpx; color: #ef4444; font-weight: 600; flex: 1; }

/* 底部 */
.er-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  display: flex; gap: 16rpx; padding: 16rpx 32rpx;
  background: var(--surface); border-top: 1px solid var(--border-light);
}
.er-footer__btn {
  flex: 1; height: 88rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 700; cursor: pointer;
}
.er-footer__btn:active { opacity: 0.85; }
.er-footer__btn--primary { background: var(--bhp-primary-500); color: #fff; }
.er-footer__btn--outline { background: var(--surface); color: var(--bhp-primary-500); border: 2px solid var(--bhp-primary-500); }
</style>
