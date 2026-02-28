<template>
  <view class="session-page">

    <!-- 自定义顶部导航栏 -->
    <view class="session-nav" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="session-nav__left" @tap="confirmExit">
        <text class="session-nav__back">✕</text>
      </view>
      <view class="session-nav__center">
        <text class="session-nav__title">{{ examTitle }}</text>
        <text class="session-nav__progress">{{ answeredCount }}/{{ questions.length }} 已作答</text>
      </view>
      <!-- 倒计时 -->
      <view class="session-nav__right">
        <view class="session-timer" :class="{ 'session-timer--warn': timeLeft <= 120, 'session-timer--critical': timeLeft <= 60 }">
          <text class="session-timer__icon">⏱</text>
          <text class="session-timer__text">{{ formatTime(timeLeft) }}</text>
        </view>
      </view>
    </view>

    <!-- 骨架屏 -->
    <view class="session-body" v-if="loading">
      <view class="px-4 mt-4">
        <view class="bhp-skeleton" style="height: 160rpx; margin-bottom: 24rpx; border-radius: var(--radius-lg);"></view>
        <view v-for="i in 4" :key="i" class="bhp-skeleton" style="height: 80rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </view>
    </view>

    <!-- 题目区 -->
    <view class="session-body" v-else-if="currentQ">

      <!-- 题目卡 -->
      <view class="session-question px-4">
        <view class="session-question__header">
          <view class="session-question__type-tag">
            <text>{{ TYPE_LABEL[currentQ.type] }}</text>
          </view>
          <view
            class="session-question__mark-btn"
            :class="{ 'session-question__mark-btn--marked': isMarked(currentQ.id) }"
            @tap="toggleMark(currentQ.id)"
          >
            <text>{{ isMarked(currentQ.id) ? '★' : '☆' }}</text>
            <text style="font-size: 20rpx; margin-left: 4rpx;">标记</text>
          </view>
        </view>
        <view class="session-question__num">
          <text>第 {{ currentIndex + 1 }} 题</text>
        </view>
        <text class="session-question__content">{{ currentQ.content }}</text>
      </view>

      <!-- 选项 -->
      <view class="session-options px-4">
        <view
          v-for="opt in currentQ.options"
          :key="opt.key"
          class="session-option"
          :class="{ 'session-option--selected': isSelected(currentQ.id, opt.key) }"
          @tap="toggleOption(currentQ, opt.key)"
        >
          <view class="session-option__key" :class="{ 'session-option__key--selected': isSelected(currentQ.id, opt.key) }">
            <text>{{ opt.key }}</text>
          </view>
          <text class="session-option__text">{{ opt.text }}</text>
        </view>
      </view>

      <!-- 多选提示 -->
      <view class="session-hint px-4" v-if="currentQ.type === 'multiple'">
        <text class="text-xs text-secondary-color">多选题：选择所有正确答案</text>
      </view>
    </view>

    <!-- 题目导航网格 -->
    <view class="session-grid-area" v-if="!loading && questions.length">
      <scroll-view scroll-x class="session-grid-scroll">
        <view class="session-grid">
          <view
            v-for="(q, idx) in questions"
            :key="q.id"
            class="session-grid-dot"
            :class="{
              'session-grid-dot--current':   idx === currentIndex,
              'session-grid-dot--answered':  hasAnswered(q.id),
              'session-grid-dot--marked':    isMarked(q.id),
              'session-grid-dot--unanswered': !hasAnswered(q.id) && idx !== currentIndex,
            }"
            @tap="jumpTo(idx)"
          >
            <text>{{ idx + 1 }}</text>
          </view>
        </view>
      </scroll-view>
      <!-- 图例 -->
      <view class="session-grid-legend">
        <view class="session-legend-item">
          <view class="session-legend-dot session-legend-dot--answered"></view>
          <text>已答</text>
        </view>
        <view class="session-legend-item">
          <view class="session-legend-dot session-legend-dot--marked"></view>
          <text>标记</text>
        </view>
        <view class="session-legend-item">
          <view class="session-legend-dot session-legend-dot--unanswered"></view>
          <text>未答</text>
        </view>
      </view>
    </view>

    <!-- 底部导航 -->
    <view class="session-footer">
      <view
        class="session-footer-btn session-footer-btn--prev"
        :class="{ 'session-footer-btn--disabled': currentIndex <= 0 }"
        @tap="goPrev"
      >
        <text>‹ 上一题</text>
      </view>

      <view
        v-if="currentIndex < questions.length - 1"
        class="session-footer-btn session-footer-btn--next"
        :class="{ 'session-footer-btn--gray': !hasAnswered(currentQ?.id) }"
        @tap="goNext"
      >
        <text>下一题 ›</text>
      </view>
      <view
        v-else
        class="session-footer-btn session-footer-btn--submit"
        @tap="confirmSubmit"
      >
        <text v-if="!submitting">交卷</text>
        <text v-else>提交中...</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { certExamApi, type ExamQuestion, type ExamInfo } from '@/api/exam'

const examId       = ref(0)
const quizId       = ref(0)
const examTitle    = ref('认证考试')
const questions    = ref<ExamQuestion[]>([])
const loading      = ref(false)
const submitting   = ref(false)
const currentIndex = ref(0)
const answers      = ref<Record<number, string | string[]>>({})
const markedSet    = ref<Set<number>>(new Set())
const timeLeft     = ref(0)
const statusBarHeight = ref(20)
const startTime    = Date.now()
const passScore    = ref(60)
const timeLimitMin = ref(60)

let timerInterval: any = null

const TYPE_LABEL: Record<string, string> = {
  single: '单选', multiple: '多选', true_false: '判断'
}

const currentQ = computed(() => questions.value[currentIndex.value] || null)

const answeredCount = computed(() =>
  questions.value.filter(q => hasAnswered(q.id)).length
)

onMounted(async () => {
  // 获取状态栏高度
  try {
    const sys = uni.getSystemInfoSync()
    statusBarHeight.value = sys.statusBarHeight || 20
  } catch { /* 静默 */ }

  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}
  examId.value = Number(query.exam_id || 0)
  quizId.value = Number(query.quiz_id || 0)

  await loadQuestions()
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})

async function loadQuestions() {
  if (!quizId.value && !examId.value) {
    uni.showToast({ title: '参数错误', icon: 'none' })
    return
  }
  loading.value = true
  try {
    const targetId = quizId.value || examId.value
    const data = await certExamApi.getQuestions(targetId)
    questions.value = (data.questions || []).sort((a, b) => a.order - b.order)
    passScore.value = data.pass_score || 60
    timeLimitMin.value = data.time_limit || 60
    timeLeft.value = timeLimitMin.value * 60
    startTimer()
  } catch {
    uni.showToast({ title: '题目加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function startTimer() {
  timerInterval = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
      if (timeLeft.value === 60) {
        uni.showToast({ title: '还剩1分钟！', icon: 'none' })
      }
    } else {
      clearInterval(timerInterval)
      uni.showToast({ title: '时间到！自动交卷', icon: 'none' })
      setTimeout(() => submitAnswers(), 1500)
    }
  }, 1000)
}

function isSelected(qid: number, key: string): boolean {
  const ans = answers.value[qid]
  if (!ans) return false
  return Array.isArray(ans) ? ans.includes(key) : ans === key
}

function hasAnswered(qid?: number): boolean {
  if (!qid) return false
  const ans = answers.value[qid]
  if (!ans) return false
  return Array.isArray(ans) ? ans.length > 0 : !!ans
}

function isMarked(qid: number): boolean {
  return markedSet.value.has(qid)
}

function toggleMark(qid: number) {
  const s = new Set(markedSet.value)
  s.has(qid) ? s.delete(qid) : s.add(qid)
  markedSet.value = s
}

function toggleOption(q: ExamQuestion, key: string) {
  if (q.type === 'single' || q.type === 'true_false') {
    answers.value = { ...answers.value, [q.id]: key }
  } else {
    const current = (answers.value[q.id] as string[]) || []
    const idx = current.indexOf(key)
    answers.value = {
      ...answers.value,
      [q.id]: idx >= 0
        ? current.filter(k => k !== key)
        : [...current, key]
    }
  }
}

function goPrev() {
  if (currentIndex.value > 0) currentIndex.value--
}

function goNext() {
  if (currentIndex.value < questions.value.length - 1) currentIndex.value++
}

function jumpTo(idx: number) { currentIndex.value = idx }

function confirmExit() {
  uni.showModal({
    title: '退出考试',
    content: '退出后本次作答将丢失，确认退出吗？',
    confirmText: '退出',
    cancelText: '继续考试',
    confirmColor: '#ef4444',
    success: (res) => {
      if (res.confirm) {
        if (timerInterval) clearInterval(timerInterval)
        uni.navigateBack()
      }
    }
  })
}

function confirmSubmit() {
  const unanswered = questions.value.length - answeredCount.value
  const marked = markedSet.value.size

  let content = `已作答 ${answeredCount.value}/${questions.value.length} 题`
  if (unanswered > 0) content += `，还有 ${unanswered} 题未作答`
  if (marked > 0) content += `，${marked} 题已标记`
  content += '，确认交卷？'

  uni.showModal({
    title: '确认交卷',
    content,
    confirmText: '交卷',
    cancelText: '继续作答',
    success: (res) => {
      if (res.confirm) submitAnswers()
    }
  })
}

async function submitAnswers() {
  if (submitting.value) return
  submitting.value = true
  if (timerInterval) clearInterval(timerInterval)

  try {
    const timeSpent = Math.round((Date.now() - startTime) / 1000)
    const result = await certExamApi.submit({
      quiz_id: quizId.value || examId.value,
      exam_id: examId.value,
      answers: answers.value,
      time_spent_seconds: timeSpent
    })
    uni.redirectTo({
      url: `/pages/exam/result?` +
           `session_id=${result.session_id}` +
           `&score=${result.score}` +
           `&pass=${result.pass ? 1 : 0}` +
           `&pass_score=${result.pass_score}` +
           `&points_earned=${result.points_earned}` +
           `&credits_earned=${result.credits_earned}` +
           `&correct_count=${result.correct_count}` +
           `&total_count=${result.total_count}` +
           `&promotion_unlocked=${result.promotion_unlocked ? 1 : 0}` +
           `&exam_id=${examId.value}`
    })
  } catch {
    submitting.value = false
    uni.showToast({ title: '提交失败，请重试', icon: 'none' })
  }
}

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
}
</script>

<style scoped>
.session-page {
  background: var(--surface);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 自定义导航 */
.session-nav {
  display: flex;
  align-items: flex-end;
  padding: 0 24rpx 16rpx;
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.session-nav__left { padding: 8rpx; cursor: pointer; }
.session-nav__back { font-size: 32rpx; color: var(--text-secondary); }
.session-nav__center { flex: 1; text-align: center; margin: 0 16rpx; }
.session-nav__title   { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.session-nav__progress{ display: block; font-size: 20rpx; color: var(--text-secondary); margin-top: 2rpx; }

/* 倒计时 */
.session-timer {
  display: flex;
  align-items: center;
  gap: 4rpx;
  background: var(--bhp-gray-100);
  border-radius: var(--radius-full);
  padding: 6rpx 16rpx;
}
.session-timer--warn     { background: var(--bhp-warn-100, #fef3c7); }
.session-timer--critical { background: var(--bhp-error-100, #fee2e2); animation: session-pulse 1s infinite; }
@keyframes session-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.6; }
}
.session-timer__icon { font-size: 24rpx; }
.session-timer__text { font-size: 26rpx; font-weight: 700; color: var(--text-primary); }
.session-timer--warn .session-timer__text     { color: var(--bhp-warn-700, #b45309); }
.session-timer--critical .session-timer__text { color: var(--bhp-error-600, #dc2626); }

/* 题目区 */
.session-body { flex: 1; padding-bottom: 16rpx; }
.session-question { padding-top: 24rpx; }
.session-question__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12rpx; }
.session-question__type-tag {
  background: var(--bhp-primary-100, #d1fae5);
  color: var(--bhp-primary-700, #047857);
  font-size: 22rpx;
  font-weight: 600;
  padding: 4rpx 16rpx;
  border-radius: var(--radius-full);
}
.session-question__mark-btn {
  display: flex;
  align-items: center;
  padding: 4rpx 16rpx;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-default);
  font-size: 26rpx;
  color: var(--text-secondary);
  cursor: pointer;
}
.session-question__mark-btn--marked {
  background: var(--bhp-warn-50, #fffbeb);
  border-color: var(--bhp-warn-400, #fbbf24);
  color: var(--bhp-warn-600, #d97706);
}
.session-question__num { font-size: 22rpx; color: var(--text-tertiary); margin-bottom: 12rpx; }
.session-question__content {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.6;
}

/* 选项 */
.session-options { padding-top: 24rpx; display: flex; flex-direction: column; gap: 12rpx; }
.session-option {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  padding: 18rpx 20rpx;
  border: 2px solid var(--border-light);
  border-radius: var(--radius-lg);
  cursor: pointer;
}
.session-option:active { opacity: 0.8; }
.session-option--selected { border-color: var(--bhp-primary-500); background: var(--bhp-primary-50); }
.session-option__key {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: var(--bhp-gray-100);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 700;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.session-option__key--selected { background: var(--bhp-primary-500); color: #fff; }
.session-option__text { flex: 1; font-size: 28rpx; color: var(--text-primary); line-height: 1.5; }
.session-hint { padding-top: 10rpx; }

/* 题目导航网格 */
.session-grid-area {
  background: var(--surface);
  border-top: 1px solid var(--border-light);
  padding: 12rpx 0 8rpx;
}
.session-grid-scroll { white-space: nowrap; }
.session-grid {
  display: flex;
  gap: 10rpx;
  padding: 0 24rpx;
  flex-wrap: nowrap;
}
.session-grid-dot {
  width: 52rpx;
  height: 52rpx;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  border: 2px solid transparent;
}
.session-grid-dot--current     { border-color: var(--bhp-primary-500); color: var(--bhp-primary-500); }
.session-grid-dot--answered    { background: var(--bhp-primary-500); color: #fff; }
.session-grid-dot--marked      { background: var(--bhp-warn-400, #fbbf24); color: #fff; }
.session-grid-dot--unanswered  { background: var(--bhp-gray-100); color: var(--text-secondary); }

.session-grid-legend {
  display: flex;
  gap: 24rpx;
  padding: 8rpx 24rpx 0;
}
.session-legend-item { display: flex; align-items: center; gap: 6rpx; font-size: 20rpx; color: var(--text-tertiary); }
.session-legend-dot { width: 16rpx; height: 16rpx; border-radius: 4rpx; }
.session-legend-dot--answered    { background: var(--bhp-primary-500); }
.session-legend-dot--marked      { background: var(--bhp-warn-400, #fbbf24); }
.session-legend-dot--unanswered  { background: var(--bhp-gray-200); }

/* 底部按钮 */
.session-footer {
  display: flex;
  gap: 16rpx;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: var(--surface);
  border-top: 1px solid var(--border-light);
}
.session-footer-btn {
  flex: 1;
  text-align: center;
  padding: 22rpx;
  border-radius: var(--radius-lg);
  font-size: 28rpx;
  font-weight: 600;
  cursor: pointer;
}
.session-footer-btn:active { opacity: 0.8; }
.session-footer-btn--prev   { border: 1px solid var(--border-default); color: var(--text-secondary); }
.session-footer-btn--next   { background: var(--bhp-primary-500); color: #fff; }
.session-footer-btn--gray   { background: var(--bhp-gray-300); color: var(--text-secondary); }
.session-footer-btn--submit { background: var(--bhp-warn-500, #f59e0b); color: #fff; }
.session-footer-btn--disabled { opacity: 0.4; pointer-events: none; }
</style>
