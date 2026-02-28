<template>
  <view class="quiz-page">

    <!-- 顶部进度 -->
    <view class="quiz-header">
      <view class="quiz-header__progress-bar">
        <view
          class="quiz-header__progress-fill"
          :style="{ width: ((currentIndex + 1) / questions.length * 100) + '%' }"
        ></view>
      </view>
      <text class="quiz-header__counter">{{ currentIndex + 1 }} / {{ questions.length }}</text>
    </view>

    <!-- 骨架屏 -->
    <template v-if="loading">
      <view class="px-4 mt-6">
        <view class="bhp-skeleton" style="height: 36rpx; width: 80%; margin-bottom: 32rpx;"></view>
        <view v-for="i in 4" :key="i" class="bhp-skeleton" style="height: 80rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </view>
    </template>

    <template v-else-if="currentQuestion">
      <!-- 题目 -->
      <view class="quiz-question-area px-4">
        <view class="quiz-type-badge">
          <text>{{ TYPE_LABEL[currentQuestion.type] }}</text>
        </view>
        <text class="quiz-question-text">{{ currentQuestion.content }}</text>
      </view>

      <!-- 选项 -->
      <view class="quiz-options px-4">
        <view
          v-for="opt in currentQuestion.options"
          :key="opt.key"
          class="quiz-option"
          :class="{
            'quiz-option--selected': isSelected(currentQuestion.id, opt.key),
            'quiz-option--single': currentQuestion.type === 'single' || currentQuestion.type === 'true_false'
          }"
          @tap="toggleOption(currentQuestion, opt.key)"
        >
          <view class="quiz-option__key">
            <text>{{ opt.key }}</text>
          </view>
          <text class="quiz-option__text">{{ opt.text }}</text>
          <view class="quiz-option__check" v-if="isSelected(currentQuestion.id, opt.key)">
            <text>✓</text>
          </view>
        </view>
      </view>

      <!-- 多选提示 -->
      <view class="quiz-hint px-4" v-if="currentQuestion.type === 'multiple'">
        <text class="text-xs text-secondary-color">多选题：请选择所有正确答案</text>
      </view>
    </template>

    <!-- 底部按钮 -->
    <view class="quiz-footer" v-if="!loading && questions.length > 0">
      <!-- 上一题 -->
      <view
        v-if="currentIndex > 0"
        class="quiz-footer-btn quiz-footer-btn--secondary"
        @tap="goPrev"
      >
        <text>上一题</text>
      </view>
      <view v-else style="flex: 1;"></view>

      <!-- 下一题 / 提交 -->
      <view
        class="quiz-footer-btn quiz-footer-btn--primary"
        :class="{ 'quiz-footer-btn--disabled': !hasAnswered(currentQuestion?.id) }"
        @tap="goNext"
      >
        <text v-if="currentIndex < questions.length - 1">下一题</text>
        <text v-else-if="!submitting">提交答案</text>
        <text v-else>提交中...</text>
      </view>
    </view>

    <!-- 倒计时（有时间限制时）-->
    <view class="quiz-timer" v-if="quiz?.time_limit && timeLeft > 0">
      <text class="quiz-timer__text" :class="{ 'quiz-timer__text--warn': timeLeft <= 60 }">
        {{ formatTime(timeLeft) }}
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { examApi, type Quiz, type QuizQuestion } from '@/api/learning'

const quizId     = ref(0)
const contentId  = ref(0)
const quiz       = ref<Quiz | null>(null)
const questions  = ref<QuizQuestion[]>([])
const loading    = ref(false)
const submitting = ref(false)
const currentIndex = ref(0)
const answers    = ref<Record<number, string | string[]>>({})   // question_id → answer
const timeLeft   = ref(0)
const startTime  = Date.now()

let timerInterval: any = null

const TYPE_LABEL: Record<string, string> = {
  single:     '单选题',
  multiple:   '多选题',
  true_false: '判断题'
}

const currentQuestion = computed(
  () => questions.value[currentIndex.value] || null
)

onMounted(async () => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}
  quizId.value   = Number(query.quiz_id || 0)
  contentId.value= Number(query.content_id || 0)
  if (quizId.value) await loadQuiz()
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})

async function loadQuiz() {
  loading.value = true
  try {
    quiz.value = await examApi.getQuiz(quizId.value)
    questions.value = quiz.value.questions.sort((a, b) => a.order - b.order)
    uni.setNavigationBarTitle({ title: quiz.value.title })
    // 启动倒计时
    if (quiz.value.time_limit) {
      timeLeft.value = quiz.value.time_limit * 60
      timerInterval = setInterval(() => {
        timeLeft.value--
        if (timeLeft.value <= 0) {
          clearInterval(timerInterval)
          submitAnswers()
        }
      }, 1000)
    }
  } catch {
    uni.showToast({ title: '测验加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function isSelected(questionId: number, optKey: string): boolean {
  const ans = answers.value[questionId]
  if (!ans) return false
  return Array.isArray(ans) ? ans.includes(optKey) : ans === optKey
}

function hasAnswered(questionId?: number): boolean {
  if (!questionId) return false
  const ans = answers.value[questionId]
  if (!ans) return false
  if (Array.isArray(ans)) return ans.length > 0
  return !!ans
}

function toggleOption(q: QuizQuestion, key: string) {
  if (q.type === 'single' || q.type === 'true_false') {
    answers.value = { ...answers.value, [q.id]: key }
  } else {
    // 多选
    const current = (answers.value[q.id] as string[]) || []
    const idx = current.indexOf(key)
    if (idx >= 0) {
      answers.value = { ...answers.value, [q.id]: current.filter(k => k !== key) }
    } else {
      answers.value = { ...answers.value, [q.id]: [...current, key] }
    }
  }
}

function goPrev() {
  if (currentIndex.value > 0) currentIndex.value--
}

function goNext() {
  if (!hasAnswered(currentQuestion.value?.id)) {
    uni.showToast({ title: '请先作答', icon: 'none' })
    return
  }
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
  } else {
    submitAnswers()
  }
}

async function submitAnswers() {
  if (submitting.value) return
  submitting.value = true
  if (timerInterval) clearInterval(timerInterval)

  try {
    const timeSpent = Math.round((Date.now() - startTime) / 1000)
    const result = await examApi.submit({
      quiz_id: quizId.value,
      answers: answers.value,
      time_spent_seconds: timeSpent
    })
    // 跳到结果页
    uni.redirectTo({
      url: `/pages/learning/quiz-result?` +
           `session_id=${result.session_id}` +
           `&score=${result.score}` +
           `&pass=${result.pass ? 1 : 0}` +
           `&pass_score=${result.pass_score}` +
           `&points_earned=${result.points_earned}` +
           `&credits_earned=${result.credits_earned}` +
           `&correct_count=${result.correct_count}` +
           `&total_count=${result.total_count}` +
           `&content_id=${contentId.value}`
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
.quiz-page {
  background: var(--surface);
  min-height: 100vh;
  padding-bottom: 160rpx;
}

/* 顶部进度 */
.quiz-header {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 28rpx 16rpx;
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
}
.quiz-header__progress-bar {
  flex: 1;
  height: 8rpx;
  background: var(--bhp-gray-200);
  border-radius: 9999px;
  overflow: hidden;
}
.quiz-header__progress-fill {
  height: 100%;
  background: var(--bhp-primary-500);
  border-radius: 9999px;
  transition: width 0.3s;
}
.quiz-header__counter { font-size: 24rpx; color: var(--text-secondary); white-space: nowrap; }

/* 题目 */
.quiz-question-area { padding-top: 32rpx; }
.quiz-type-badge {
  display: inline-block;
  background: var(--bhp-primary-100, #d1fae5);
  color: var(--bhp-primary-700, #047857);
  font-size: 22rpx;
  font-weight: 600;
  padding: 4rpx 16rpx;
  border-radius: var(--radius-full);
  margin-bottom: 16rpx;
}
.quiz-question-text {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.6;
}

/* 选项 */
.quiz-options { padding-top: 32rpx; display: flex; flex-direction: column; gap: 12rpx; }
.quiz-option {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  padding: 20rpx 24rpx;
  border: 2px solid var(--border-light);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.15s;
}
.quiz-option:active { opacity: 0.8; }
.quiz-option--selected {
  border-color: var(--bhp-primary-500);
  background: var(--bhp-primary-50);
}
.quiz-option__key {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: var(--bhp-gray-100);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.quiz-option--selected .quiz-option__key {
  background: var(--bhp-primary-500);
  color: #fff;
}
.quiz-option__text {
  flex: 1;
  font-size: 28rpx;
  color: var(--text-primary);
  line-height: 1.5;
}
.quiz-option__check {
  font-size: 28rpx;
  color: var(--bhp-primary-500);
  font-weight: 700;
}
.quiz-hint { padding-top: 12rpx; }

/* 底部按钮 */
.quiz-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16rpx 28rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: var(--surface);
  border-top: 1px solid var(--border-light);
  display: flex;
  gap: 16rpx;
}
.quiz-footer-btn {
  flex: 1;
  text-align: center;
  padding: 22rpx;
  border-radius: var(--radius-lg);
  font-size: 28rpx;
  font-weight: 600;
  cursor: pointer;
}
.quiz-footer-btn--secondary {
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
}
.quiz-footer-btn--primary {
  background: var(--bhp-primary-500);
  color: #fff;
}
.quiz-footer-btn--disabled {
  opacity: 0.4;
  pointer-events: none;
}
.quiz-footer-btn:active { opacity: 0.8; }

/* 倒计时 */
.quiz-timer {
  position: fixed;
  top: 0;
  right: 24rpx;
  padding-top: 20rpx;
  z-index: 100;
}
.quiz-timer__text {
  font-size: 26rpx;
  color: var(--text-secondary);
  font-weight: 600;
}
.quiz-timer__text--warn { color: var(--bhp-error-500, #ef4444); }
</style>
