<template>
  <view class="do-page">

    <!-- 自定义导航栏 -->
    <view class="do-navbar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="do-navbar__inner">
        <view class="do-navbar__back" @tap="confirmExit">
          <text class="do-navbar__back-icon">‹</text>
        </view>
        <view class="do-navbar__center">
          <text class="do-navbar__title">{{ assessment?.title || '评估作答' }}</text>
          <text class="do-navbar__sub" v-if="totalQuestions > 0">
            {{ currentIndex + 1 }} / {{ totalQuestions }}
          </text>
        </view>
        <!-- 计时器（有时间限制时显示） -->
        <view class="do-navbar__timer" v-if="assessment?.time_limit">
          <text :class="['do-timer', timerWarning ? 'do-timer--warn' : '']">
            {{ formatTimer(remainSeconds) }}
          </text>
        </view>
        <view class="do-navbar__timer" v-else>
          <text class="text-xs text-tertiary-color">{{ elapsedLabel }}</text>
        </view>
      </view>
      <!-- 进度条 -->
      <view class="do-progress">
        <view class="do-progress__fill" :style="{ width: progressPct + '%' }"></view>
      </view>
    </view>

    <!-- 加载中 -->
    <view class="do-loading" v-if="loading">
      <view v-for="i in 4" :key="i" class="bhp-skeleton" style="height: 80rpx; margin-bottom: 16rpx; border-radius: var(--radius-lg);"></view>
    </view>

    <!-- 评估说明（未开始时显示） -->
    <view class="do-intro" v-else-if="!started">
      <view class="do-intro__icon">{{ TYPE_ICON[assessment?.type || ''] || '📋' }}</view>
      <text class="do-intro__title">{{ assessment?.title }}</text>
      <text class="do-intro__desc" v-if="assessment?.description">{{ assessment.description }}</text>

      <view class="do-intro__meta-grid">
        <view class="do-intro__meta-item">
          <text class="do-intro__meta-icon">❓</text>
          <text class="do-intro__meta-val">{{ totalQuestions }}</text>
          <text class="do-intro__meta-label">题目数</text>
        </view>
        <view class="do-intro__meta-item" v-if="assessment?.time_limit">
          <text class="do-intro__meta-icon">⏱</text>
          <text class="do-intro__meta-val">{{ assessment.time_limit }}</text>
          <text class="do-intro__meta-label">分钟</text>
        </view>
        <view class="do-intro__meta-item">
          <text class="do-intro__meta-icon">📝</text>
          <text class="do-intro__meta-val">{{ TYPE_LABEL[assessment?.type || ''] }}</text>
          <text class="do-intro__meta-label">评估类型</text>
        </view>
      </view>

      <view class="do-intro__instructions" v-if="assessment?.instructions">
        <text class="do-intro__instructions-title">注意事项</text>
        <text class="do-intro__instructions-text">{{ assessment.instructions }}</text>
      </view>

      <view class="do-intro__default-tips">
        <text class="do-intro__tip">• 请根据您最近两周的实际感受如实回答</text>
        <text class="do-intro__tip">• 答案无对错之分，选择最符合您情况的选项</text>
        <text class="do-intro__tip">• 中途退出后可继续作答，进度会自动保存</text>
      </view>

      <view class="do-intro__btn" @tap="startAssessment">
        <text>开始评估</text>
      </view>
    </view>

    <!-- 题目作答区 -->
    <scroll-view class="do-content" scroll-y v-else-if="currentQuestion">
      <view class="do-question px-4">

        <!-- 题号 + 必填标记 -->
        <view class="do-q-header">
          <view class="do-q-num">
            <text>{{ currentIndex + 1 }}</text>
          </view>
          <text class="do-q-required" v-if="currentQuestion.required">*必答</text>
          <text class="do-q-hint text-xs text-tertiary-color" v-if="currentQuestion.hint">{{ currentQuestion.hint }}</text>
        </view>

        <!-- 题目文本 -->
        <text class="do-q-text">{{ currentQuestion.text }}</text>

        <!-- ─── 单选题 ─────────────────────────────────────── -->
        <view class="do-options" v-if="currentQuestion.type === 'single'">
          <view
            v-for="opt in currentQuestion.options"
            :key="opt.key"
            class="do-option"
            :class="{ 'do-option--selected': answers[currentQuestion.id] === opt.key }"
            @tap="selectSingle(currentQuestion.id, opt.key)"
          >
            <view class="do-option__radio">
              <view class="do-option__radio-dot" v-if="answers[currentQuestion.id] === opt.key"></view>
            </view>
            <text class="do-option__text">{{ opt.text }}</text>
          </view>
        </view>

        <!-- ─── 多选题 ─────────────────────────────────────── -->
        <view class="do-options" v-else-if="currentQuestion.type === 'multiple'">
          <text class="do-q-sub text-xs text-secondary-color">可多选</text>
          <view
            v-for="opt in currentQuestion.options"
            :key="opt.key"
            class="do-option do-option--checkbox"
            :class="{ 'do-option--selected': isMultiSelected(currentQuestion.id, opt.key) }"
            @tap="toggleMulti(currentQuestion.id, opt.key)"
          >
            <view class="do-option__checkbox">
              <text v-if="isMultiSelected(currentQuestion.id, opt.key)">✓</text>
            </view>
            <text class="do-option__text">{{ opt.text }}</text>
          </view>
        </view>

        <!-- ─── 量表题 ─────────────────────────────────────── -->
        <view class="do-scale" v-else-if="currentQuestion.type === 'scale'">
          <view class="do-scale__labels">
            <text class="text-xs text-secondary-color">{{ currentQuestion.scale_labels?.min || scaleMin }}</text>
            <text class="text-xs text-secondary-color">{{ currentQuestion.scale_labels?.max || scaleMax }}</text>
          </view>
          <slider
            class="do-scale__slider"
            :min="currentQuestion.scale_min ?? 0"
            :max="currentQuestion.scale_max ?? 10"
            :step="currentQuestion.scale_step ?? 1"
            :value="Number(answers[currentQuestion.id] ?? currentQuestion.scale_min ?? 0)"
            show-value
            active-color="var(--bhp-primary-500)"
            @change="onScaleChange(currentQuestion.id, $event)"
          />
          <view class="do-scale__ticks">
            <text
              v-for="n in scaleRange(currentQuestion)"
              :key="n"
              class="do-scale__tick text-xs"
              :class="{ 'do-scale__tick--active': Number(answers[currentQuestion.id]) === n }"
            >{{ n }}</text>
          </view>
        </view>

        <!-- ─── 文本题 ─────────────────────────────────────── -->
        <view class="do-text-input" v-else-if="currentQuestion.type === 'text'">
          <textarea
            class="do-text-input__area"
            :value="String(answers[currentQuestion.id] || '')"
            placeholder="请输入您的回答..."
            placeholder-class="do-text-placeholder"
            :maxlength="500"
            auto-height
            @input="onTextInput(currentQuestion.id, $event)"
          />
          <text class="do-text-input__count text-xs text-tertiary-color">
            {{ String(answers[currentQuestion.id] || '').length }}/500
          </text>
        </view>

        <!-- ─── 是否题 ─────────────────────────────────────── -->
        <view class="do-boolean" v-else-if="currentQuestion.type === 'boolean'">
          <view
            class="do-boolean__btn"
            :class="{ 'do-boolean__btn--yes': answers[currentQuestion.id] === 'yes' }"
            @tap="selectSingle(currentQuestion.id, 'yes')"
          >
            <text class="do-boolean__icon">✓</text>
            <text>是</text>
          </view>
          <view
            class="do-boolean__btn"
            :class="{ 'do-boolean__btn--no': answers[currentQuestion.id] === 'no' }"
            @tap="selectSingle(currentQuestion.id, 'no')"
          >
            <text class="do-boolean__icon">✗</text>
            <text>否</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 底部导航 -->
    <view class="do-footer" v-if="started">
      <view
        class="do-footer__prev"
        :class="{ 'do-footer__prev--disabled': currentIndex === 0 }"
        @tap="prevQuestion"
      >
        <text>‹ 上一题</text>
      </view>

      <!-- 题目网格（点击快速跳转） -->
      <scroll-view class="do-footer__grid-scroll" scroll-x>
        <view class="do-footer__grid">
          <view
            v-for="(q, idx) in questions"
            :key="q.id"
            class="do-footer__dot"
            :class="{
              'do-footer__dot--current':   idx === currentIndex,
              'do-footer__dot--answered':  isAnswered(q.id),
              'do-footer__dot--unanswered': !isAnswered(q.id) && idx !== currentIndex
            }"
            @tap="currentIndex = idx"
          >
            <text>{{ idx + 1 }}</text>
          </view>
        </view>
      </scroll-view>

      <view
        v-if="currentIndex < totalQuestions - 1"
        class="do-footer__next"
        :class="{ 'do-footer__next--active': isAnswered(currentQuestion?.id) }"
        @tap="nextQuestion"
      >
        <text>下一题 ›</text>
      </view>
      <view
        v-else
        class="do-footer__submit"
        :class="{ 'do-footer__submit--active': canSubmit && !submitting }"
        @tap="confirmSubmit"
      >
        <text v-if="!submitting">提交评估</text>
        <text v-else>提交中...</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  myAssessmentApi,
  type MyAssignment,
  type AssessmentDef,
  type AssessmentQuestion,
} from '@/api/assessment'

// ─── 常量 ─────────────────────────────────────────────────────
const TYPE_LABEL: Record<string, string> = {
  baps: 'BAPS行为评估', survey: '问卷调查', health_check: '健康检查',
  phq9: 'PHQ-9', gad7: 'GAD-7', custom: '自定义'
}
const TYPE_ICON: Record<string, string> = {
  baps: '🧠', survey: '📝', health_check: '🏥',
  phq9: '💭', gad7: '😰', custom: '📋'
}

// ─── 状态 ─────────────────────────────────────────────────────
const statusBarHeight = ref(0)
const assignmentId    = ref(0)
const assignment      = ref<MyAssignment | null>(null)
const assessment      = ref<AssessmentDef | null>(null)
const questions       = ref<AssessmentQuestion[]>([])
const loading         = ref(false)
const started         = ref(false)
const submitting      = ref(false)

const currentIndex = ref(0)
const answers      = ref<Record<number, string | string[] | number>>({})

// 计时器
let timerInterval: ReturnType<typeof setInterval> | null = null
const remainSeconds = ref(0)
const elapsedSeconds = ref(0)

// ─── 计算属性 ─────────────────────────────────────────────────
const totalQuestions   = computed(() => questions.value.length)
const currentQuestion  = computed(() => questions.value[currentIndex.value] || null)
const progressPct      = computed(() =>
  totalQuestions.value ? Math.round(((currentIndex.value + 1) / totalQuestions.value) * 100) : 0
)
const answeredCount  = computed(() =>
  questions.value.filter(q => isAnswered(q.id)).length
)
const canSubmit = computed(() => {
  const required = questions.value.filter(q => q.required)
  return required.every(q => isAnswered(q.id))
})
const timerWarning = computed(() => remainSeconds.value > 0 && remainSeconds.value <= 120)

const elapsedLabel = computed(() => {
  const m = Math.floor(elapsedSeconds.value / 60)
  const s = elapsedSeconds.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const scaleMin = computed(() => currentQuestion.value?.scale_min ?? 0)
const scaleMax = computed(() => currentQuestion.value?.scale_max ?? 10)

// ─── 初始化 ───────────────────────────────────────────────────
onMounted(async () => {
  const sysInfo = uni.getSystemInfoSync()
  statusBarHeight.value = sysInfo.statusBarHeight || 0

  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  assignmentId.value = Number(cur?.options?.id || 0)

  if (!assignmentId.value) {
    uni.showToast({ title: '参数错误', icon: 'none' })
    return
  }

  loading.value = true
  try {
    const asgn = await myAssessmentApi.detail(assignmentId.value)
    assignment.value = asgn

    // 如果已提交，直接跳转到结果页
    if (asgn.status === 'reviewed') {
      uni.redirectTo({ url: `/pages/assessment/result?id=${assignmentId.value}` })
      return
    }

    const def = await myAssessmentApi.getAssessment(asgn.assessment_id)
    assessment.value = def
    questions.value = (def.questions || []).sort((a, b) => a.order - b.order)

    // 进行中的评估直接进入作答
    if (asgn.status === 'in_progress') {
      startAssessment()
    }
  } catch (e: any) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})

onUnmounted(() => stopTimer())

// ─── 方法 ─────────────────────────────────────────────────────
async function startAssessment() {
  if (assignment.value?.status === 'assigned') {
    try { await myAssessmentApi.start(assignmentId.value) } catch { /* 静默 */ }
  }
  started.value = true
  currentIndex.value = 0
  startTimer()
}

function startTimer() {
  if (assessment.value?.time_limit) {
    remainSeconds.value = assessment.value.time_limit * 60
    timerInterval = setInterval(() => {
      remainSeconds.value--
      if (remainSeconds.value <= 0) {
        stopTimer()
        uni.showToast({ title: '时间到，自动提交', icon: 'none' })
        doSubmit()
      }
    }, 1000)
  } else {
    timerInterval = setInterval(() => { elapsedSeconds.value++ }, 1000)
  }
}

function stopTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
}

function formatTimer(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// ─── 答题逻辑 ─────────────────────────────────────────────────
function selectSingle(qid: number, key: string) {
  answers.value = { ...answers.value, [qid]: key }
}

function isMultiSelected(qid: number, key: string): boolean {
  const arr = answers.value[qid]
  return Array.isArray(arr) && arr.includes(key)
}

function toggleMulti(qid: number, key: string) {
  const arr = (answers.value[qid] as string[]) || []
  const exists = arr.includes(key)
  answers.value = {
    ...answers.value,
    [qid]: exists ? arr.filter(k => k !== key) : [...arr, key]
  }
}

function onScaleChange(qid: number, e: any) {
  answers.value = { ...answers.value, [qid]: e.detail.value }
}

function onTextInput(qid: number, e: any) {
  answers.value = { ...answers.value, [qid]: e.detail.value }
}

function isAnswered(qid: number | undefined): boolean {
  if (qid == null) return false
  const ans = answers.value[qid]
  if (ans === undefined || ans === null || ans === '') return false
  if (Array.isArray(ans)) return ans.length > 0
  return true
}

function scaleRange(q: AssessmentQuestion): number[] {
  const min = q.scale_min ?? 0
  const max = q.scale_max ?? 10
  const step = q.scale_step ?? 1
  const result = []
  for (let i = min; i <= max; i += step) result.push(i)
  return result
}

// ─── 导航 ─────────────────────────────────────────────────────
function prevQuestion() {
  if (currentIndex.value > 0) currentIndex.value--
}

function nextQuestion() {
  if (currentQuestion.value?.required && !isAnswered(currentQuestion.value.id)) {
    uni.showToast({ title: '请先回答此题', icon: 'none' })
    return
  }
  if (currentIndex.value < totalQuestions.value - 1) currentIndex.value++
}

function confirmExit() {
  uni.showModal({
    title: '退出评估',
    content: '当前进度将保留，下次可继续作答。确认退出吗？',
    confirmText: '确认退出',
    success: (res) => {
      if (res.confirm) {
        stopTimer()
        uni.navigateBack()
      }
    }
  })
}

function confirmSubmit() {
  if (!canSubmit.value || submitting.value) return
  const unanswered = questions.value.filter(q => !isAnswered(q.id)).length
  uni.showModal({
    title: '提交评估',
    content: unanswered > 0
      ? `还有 ${unanswered} 题未作答（非必答题），确认提交吗？`
      : '确认提交本次评估？提交后无法修改。',
    confirmText: '确认提交',
    success: (res) => { if (res.confirm) doSubmit() }
  })
}

async function doSubmit() {
  submitting.value = true
  stopTimer()
  try {
    const responses = questions.value
      .filter(q => isAnswered(q.id))
      .map(q => ({ question_id: q.id, answer: answers.value[q.id] }))

    await myAssessmentApi.submit({
      assignment_id: assignmentId.value,
      responses,
      time_spent_seconds: elapsedSeconds.value || 0
    })

    uni.showToast({ title: '提交成功！', icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: `/pages/assessment/result?id=${assignmentId.value}&just_submitted=1` })
    }, 800)
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || '提交失败，请重试', icon: 'none' })
    submitting.value = false
  }
}
</script>

<style scoped>
.do-page {
  background: var(--surface-secondary);
  min-height: 100vh;
  display: flex; flex-direction: column;
}

/* 自定义导航栏 */
.do-navbar {
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}
.do-navbar__inner {
  display: flex; align-items: center;
  padding: 12rpx 16rpx;
  height: 88rpx;
  gap: 12rpx;
}
.do-navbar__back {
  width: 64rpx; height: 64rpx;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; flex-shrink: 0;
}
.do-navbar__back-icon { font-size: 44rpx; color: var(--text-primary); font-weight: 300; }
.do-navbar__center { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4rpx; }
.do-navbar__title { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.do-navbar__sub   { font-size: 20rpx; color: var(--text-tertiary); }
.do-navbar__timer { flex-shrink: 0; width: 100rpx; text-align: right; }
.do-timer         { font-size: 28rpx; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.do-timer--warn   { color: #ff4d4f; animation: do-blink 0.8s ease-in-out infinite; }
@keyframes do-blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.do-progress { height: 6rpx; background: var(--bhp-gray-100); }
.do-progress__fill {
  height: 100%; background: var(--bhp-primary-500);
  transition: width 0.3s ease;
}

/* 加载 */
.do-loading { padding: 24rpx 32rpx; }

/* 评估说明 */
.do-intro {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  padding: 40rpx 48rpx; gap: 24rpx;
}
.do-intro__icon  { font-size: 80rpx; }
.do-intro__title { font-size: 34rpx; font-weight: 700; color: var(--text-primary); text-align: center; }
.do-intro__desc  { font-size: 26rpx; color: var(--text-secondary); text-align: center; line-height: 1.6; }

.do-intro__meta-grid {
  display: flex; gap: 24rpx; width: 100%;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; border: 1px solid var(--border-light);
}
.do-intro__meta-item {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6rpx;
}
.do-intro__meta-icon { font-size: 32rpx; }
.do-intro__meta-val  { font-size: 30rpx; font-weight: 700; color: var(--text-primary); }
.do-intro__meta-label { font-size: 20rpx; color: var(--text-tertiary); }

.do-intro__instructions {
  width: 100%;
  background: var(--bhp-warn-50, #fffbeb); border-radius: var(--radius-lg);
  padding: 16rpx 20rpx;
}
.do-intro__instructions-title {
  display: block; font-size: 24rpx; font-weight: 600;
  color: var(--bhp-warn-700, #b45309); margin-bottom: 8rpx;
}
.do-intro__instructions-text { font-size: 22rpx; color: var(--text-secondary); line-height: 1.6; }

.do-intro__default-tips { width: 100%; display: flex; flex-direction: column; gap: 8rpx; }
.do-intro__tip { font-size: 24rpx; color: var(--text-secondary); line-height: 1.6; }

.do-intro__btn {
  width: 100%; height: 96rpx;
  background: var(--bhp-primary-500); color: #fff;
  border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 32rpx; font-weight: 700; cursor: pointer;
  margin-top: 8rpx;
}
.do-intro__btn:active { opacity: 0.85; }

/* 作答区 */
.do-content { flex: 1; }

.do-question { padding: 32rpx 32rpx 160rpx; }

.do-q-header { display: flex; align-items: center; gap: 12rpx; margin-bottom: 16rpx; }
.do-q-num {
  width: 48rpx; height: 48rpx; border-radius: 50%;
  background: var(--bhp-primary-500); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; font-weight: 700; flex-shrink: 0;
}
.do-q-required { font-size: 22rpx; color: #ff4d4f; font-weight: 600; }
.do-q-hint     { flex: 1; text-align: right; }

.do-q-text {
  display: block; font-size: 30rpx; font-weight: 600;
  color: var(--text-primary); line-height: 1.6; margin-bottom: 28rpx;
}
.do-q-sub { display: block; margin-bottom: 12rpx; }

/* 选项 */
.do-options { display: flex; flex-direction: column; gap: 12rpx; }
.do-option {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--surface); border: 2rpx solid var(--border-light);
  border-radius: var(--radius-lg); padding: 20rpx 24rpx;
  cursor: pointer; transition: all 0.15s;
}
.do-option:active { opacity: 0.8; }
.do-option--selected {
  border-color: var(--bhp-primary-500);
  background: var(--bhp-primary-50);
}

.do-option__radio {
  width: 36rpx; height: 36rpx; border-radius: 50%;
  border: 3rpx solid var(--bhp-gray-300);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.do-option--selected .do-option__radio { border-color: var(--bhp-primary-500); }
.do-option__radio-dot {
  width: 18rpx; height: 18rpx; border-radius: 50%;
  background: var(--bhp-primary-500);
}

.do-option__checkbox {
  width: 36rpx; height: 36rpx; border-radius: var(--radius-sm);
  border: 3rpx solid var(--bhp-gray-300);
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; color: #fff; font-weight: 700;
  flex-shrink: 0;
}
.do-option--checkbox.do-option--selected .do-option__checkbox {
  background: var(--bhp-primary-500); border-color: var(--bhp-primary-500);
}

.do-option__text { font-size: 26rpx; color: var(--text-primary); line-height: 1.4; }
.do-option--selected .do-option__text { color: var(--bhp-primary-700, #047857); font-weight: 500; }

/* 量表 */
.do-scale { display: flex; flex-direction: column; gap: 12rpx; }
.do-scale__labels { display: flex; justify-content: space-between; }
.do-scale__slider { width: 100%; }
.do-scale__ticks { display: flex; justify-content: space-between; padding: 0 4rpx; }
.do-scale__tick { color: var(--text-tertiary); }
.do-scale__tick--active { color: var(--bhp-primary-500); font-weight: 700; }

/* 文本输入 */
.do-text-input { }
.do-text-input__area {
  width: 100%; min-height: 200rpx;
  background: var(--surface);
  border: 2rpx solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 20rpx 24rpx;
  font-size: 28rpx; color: var(--text-primary);
  box-sizing: border-box; line-height: 1.6;
}
.do-text-placeholder { color: var(--text-tertiary); font-size: 26rpx; }
.do-text-input__count { display: block; text-align: right; margin-top: 8rpx; }

/* 是否题 */
.do-boolean { display: flex; gap: 24rpx; }
.do-boolean__btn {
  flex: 1; height: 120rpx;
  border-radius: var(--radius-lg);
  border: 3rpx solid var(--border-light);
  background: var(--surface);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8rpx; cursor: pointer; font-size: 28rpx; color: var(--text-secondary);
  font-weight: 600;
}
.do-boolean__btn:active { opacity: 0.8; }
.do-boolean__icon { font-size: 36rpx; }
.do-boolean__btn--yes {
  border-color: var(--bhp-success-400, #4ade80);
  background: var(--bhp-success-50); color: var(--bhp-success-700, #15803d);
}
.do-boolean__btn--no {
  border-color: var(--bhp-error-300, #fca5a5);
  background: var(--bhp-error-50, #fef2f2); color: var(--bhp-error-700, #b91c1c);
}

/* 底部导航 */
.do-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: var(--surface);
  border-top: 1px solid var(--border-light);
  padding: 16rpx 24rpx env(safe-area-inset-bottom);
  display: flex; align-items: center; gap: 12rpx;
  z-index: 100;
}
.do-footer__prev {
  padding: 16rpx 20rpx;
  border-radius: var(--radius-lg);
  background: var(--bhp-gray-100); color: var(--text-secondary);
  font-size: 24rpx; font-weight: 600; cursor: pointer; flex-shrink: 0;
}
.do-footer__prev--disabled { opacity: 0.4; }

.do-footer__grid-scroll { flex: 1; white-space: nowrap; }
.do-footer__grid { display: inline-flex; gap: 8rpx; }
.do-footer__dot {
  width: 40rpx; height: 40rpx; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 18rpx; font-weight: 600; cursor: pointer;
  flex-shrink: 0;
}
.do-footer__dot--current    { background: var(--bhp-primary-500); color: #fff; }
.do-footer__dot--answered   { background: var(--bhp-success-100, #dcfce7); color: var(--bhp-success-700, #15803d); }
.do-footer__dot--unanswered { background: var(--bhp-gray-100); color: var(--text-tertiary); }

.do-footer__next {
  padding: 16rpx 20rpx;
  border-radius: var(--radius-lg);
  background: var(--bhp-gray-200); color: var(--text-tertiary);
  font-size: 24rpx; font-weight: 600; flex-shrink: 0;
}
.do-footer__next--active { background: var(--bhp-primary-500); color: #fff; cursor: pointer; }
.do-footer__next--active:active { opacity: 0.8; }

.do-footer__submit {
  padding: 16rpx 24rpx;
  border-radius: var(--radius-lg);
  background: var(--bhp-gray-200); color: var(--text-tertiary);
  font-size: 24rpx; font-weight: 600; flex-shrink: 0;
}
.do-footer__submit--active { background: var(--bhp-success-500, #22c55e); color: #fff; cursor: pointer; }
.do-footer__submit--active:active { opacity: 0.8; }
</style>
