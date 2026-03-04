<template>
  <view class="do-page">
    <!-- 自定义导航栏 -->
    <view class="do-navbar">
      <view class="do-nav-back" @tap="confirmExit">←</view>
      <view class="do-nav-center">
        <text class="do-nav-group">第{{ currentGroupIndex + 1 }}组/共{{ groups.length }}组</text>
        <text class="do-nav-scale">{{ currentGroupName }}</text>
      </view>
      <text class="do-nav-timer">{{ timerText }}</text>
    </view>

    <!-- 量表进度 -->
    <view class="do-group-progress">
      <view
        v-for="(g, i) in groups" :key="i"
        class="do-group-dot"
        :class="{ 'do-group-dot--done': i < currentGroupIndex, 'do-group-dot--active': i === currentGroupIndex }"
      ></view>
    </view>

    <!-- 题目进度条 -->
    <view class="do-progress-bar">
      <view class="do-progress-fill" :style="{ width: progressPercent + '%' }"></view>
    </view>
    <text class="do-progress-text">{{ currentQuestionIndex + 1 }} / {{ currentGroupQuestions.length }}</text>

    <!-- 题目内容 -->
    <scroll-view scroll-y class="do-question-area" v-if="currentQuestion">
      <view class="do-question-card">
        <text class="do-question-num">Q{{ currentQuestionIndex + 1 }}</text>
        <text class="do-question-text">{{ currentQuestion.text || currentQuestion.question || currentQuestion.title }}</text>

        <!-- 单选 -->
        <view v-if="currentQuestion.type === 'single' || currentQuestion.type === 'radio'" class="do-options">
          <view
            v-for="(opt, oi) in currentQuestion.options" :key="oi"
            class="do-option" :class="{ 'do-option--selected': answers[questionKey] === oi }"
            @tap="selectSingle(oi)"
          >
            <view class="do-option-indicator">{{ answers[questionKey] === oi ? '✓' : String.fromCharCode(65 + oi) }}</view>
            <text class="do-option-text">{{ typeof opt === 'string' ? opt : opt.text || opt.label }}</text>
          </view>
        </view>

        <!-- 多选 -->
        <view v-else-if="currentQuestion.type === 'multiple' || currentQuestion.type === 'checkbox'" class="do-options">
          <view
            v-for="(opt, oi) in currentQuestion.options" :key="oi"
            class="do-option" :class="{ 'do-option--selected': (answers[questionKey] || []).includes(oi) }"
            @tap="selectMultiple(oi)"
          >
            <view class="do-option-indicator">{{ (answers[questionKey] || []).includes(oi) ? '✓' : '○' }}</view>
            <text class="do-option-text">{{ typeof opt === 'string' ? opt : opt.text || opt.label }}</text>
          </view>
        </view>

        <!-- 量表滑动 1-7 -->
        <view v-else-if="currentQuestion.type === 'scale' || currentQuestion.type === 'likert'" class="do-scale">
          <view class="do-scale-labels">
            <text class="do-scale-min">{{ currentQuestion.min_label || '非常不同意' }}</text>
            <text class="do-scale-max">{{ currentQuestion.max_label || '非常同意' }}</text>
          </view>
          <view class="do-scale-dots">
            <view
              v-for="n in (currentQuestion.max || 7)" :key="n"
              class="do-scale-dot" :class="{ 'do-scale-dot--selected': answers[questionKey] === n }"
              @tap="answers[questionKey] = n; saveDraft()"
            >
              {{ n }}
            </view>
          </view>
        </view>

        <!-- 布尔 -->
        <view v-else-if="currentQuestion.type === 'boolean'" class="do-boolean">
          <view class="do-bool-btn" :class="{ 'do-bool-btn--yes': answers[questionKey] === true }" @tap="answers[questionKey] = true; saveDraft()">
            <text class="do-bool-icon">✓</text>
            <text>是</text>
          </view>
          <view class="do-bool-btn" :class="{ 'do-bool-btn--no': answers[questionKey] === false }" @tap="answers[questionKey] = false; saveDraft()">
            <text class="do-bool-icon">✕</text>
            <text>否</text>
          </view>
        </view>

        <!-- 文本 -->
        <view v-else-if="currentQuestion.type === 'text' || currentQuestion.type === 'essay'" class="do-text">
          <textarea class="do-text-input" placeholder="请输入您的回答..." v-model="answers[questionKey]" @blur="saveDraft" maxlength="500" />
        </view>

        <!-- 默认按单选处理 -->
        <view v-else class="do-options">
          <view
            v-for="(opt, oi) in (currentQuestion.options || [])" :key="oi"
            class="do-option" :class="{ 'do-option--selected': answers[questionKey] === oi }"
            @tap="selectSingle(oi)"
          >
            <view class="do-option-indicator">{{ answers[questionKey] === oi ? '✓' : String.fromCharCode(65 + oi) }}</view>
            <text class="do-option-text">{{ typeof opt === 'string' ? opt : opt.text || opt.label }}</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 底部操作 -->
    <view class="do-bottom">
      <view class="do-bottom-btns">
        <view class="do-btn do-btn-prev" v-if="canPrev" @tap="prevQuestion">← 上一题</view>
        <view class="do-btn do-btn-next" v-if="canNext" @tap="nextQuestion">下一题 →</view>
        <!-- 最后一题：始终显示提交按钮；有未答题时点击跳转到第一个未答题 -->
        <view
          class="do-btn"
          :class="allAnswered ? 'do-btn-submit' : 'do-btn-submit-warn'"
          v-if="isLastQuestion"
          @tap="submitAssessment"
        >{{ allAnswered ? '提交评估 ✓' : `提交 (还有${unansweredCount}题)` }}</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import { httpReq as http } from '@/api/request'

const assessmentId = ref('')
const groups = ref<any[]>([])
const currentGroupIndex = ref(0)
const currentQuestionIndex = ref(0)
const answers = reactive<Record<string, any>>({})
const timer = ref(0)
let timerInterval: any = null

// 量表分组定义
const scaleGroups = [
  { key: 'ttm7', name: 'TTM 行为阶段' },
  { key: 'big5', name: 'BIG5 大五人格' },
  { key: 'bpt6', name: 'BPT6 行为类型' },
  { key: 'capacity', name: '能力评估' },
  { key: 'spi', name: 'SPI 自我评估' },
]

const currentGroupName = computed(() => groups.value[currentGroupIndex.value]?.name || '评估')
const currentGroupQuestions = computed(() => groups.value[currentGroupIndex.value]?.questions || [])
const currentQuestion = computed(() => currentGroupQuestions.value[currentQuestionIndex.value])
const questionKey = computed(() => `${currentGroupIndex.value}_${currentQuestionIndex.value}`)

const progressPercent = computed(() => {
  const total = currentGroupQuestions.value.length
  return total > 0 ? Math.round((currentQuestionIndex.value / total) * 100) : 0
})

const canPrev = computed(() => currentQuestionIndex.value > 0 || currentGroupIndex.value > 0)
const canNext = computed(() => {
  if (currentQuestionIndex.value < currentGroupQuestions.value.length - 1) return true
  if (currentGroupIndex.value < groups.value.length - 1) return true
  return false
})
const isLastQuestion = computed(() =>
  currentGroupIndex.value === groups.value.length - 1 &&
  currentQuestionIndex.value === currentGroupQuestions.value.length - 1
)
const allAnswered = computed(() => {
  let total = 0, answered = 0
  groups.value.forEach((g, gi) => {
    g.questions.forEach((_: any, qi: number) => {
      total++
      if (answers[`${gi}_${qi}`] !== undefined && answers[`${gi}_${qi}`] !== null && answers[`${gi}_${qi}`] !== '') answered++
    })
  })
  return total > 0 && answered >= total
})

const unansweredCount = computed(() => {
  let count = 0
  groups.value.forEach((g, gi) => {
    g.questions.forEach((_: any, qi: number) => {
      const v = answers[`${gi}_${qi}`]
      if (v === undefined || v === null || v === '') count++
    })
  })
  return count
})

const timerText = computed(() => {
  const m = Math.floor(timer.value / 60)
  const s = timer.value % 60
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
})

function selectSingle(oi: number) {
  answers[questionKey.value] = oi
  saveDraft()
  // 自动下一题
  setTimeout(() => { if (canNext.value) nextQuestion() }, 300)
}

function selectMultiple(oi: number) {
  const cur = answers[questionKey.value] || []
  const idx = cur.indexOf(oi)
  if (idx >= 0) cur.splice(idx, 1)
  else cur.push(oi)
  answers[questionKey.value] = [...cur]
  saveDraft()
}

function nextQuestion() {
  if (currentQuestionIndex.value < currentGroupQuestions.value.length - 1) {
    currentQuestionIndex.value++
  } else if (currentGroupIndex.value < groups.value.length - 1) {
    currentGroupIndex.value++
    currentQuestionIndex.value = 0
  }
  saveDraft()
}

function prevQuestion() {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
  } else if (currentGroupIndex.value > 0) {
    currentGroupIndex.value--
    currentQuestionIndex.value = groups.value[currentGroupIndex.value].questions.length - 1
  }
}

function saveDraft() {
  try {
    uni.setStorageSync('assessment_draft_' + assessmentId.value, JSON.stringify({
      answers, currentGroupIndex: currentGroupIndex.value, currentQuestionIndex: currentQuestionIndex.value, timer: timer.value
    }))
  } catch (e) { console.warn('[assessment/do] saveDraft:', e) }
}

function loadDraft() {
  try {
    const d = uni.getStorageSync('assessment_draft_' + assessmentId.value)
    if (d) {
      const parsed = JSON.parse(d)
      Object.assign(answers, parsed.answers || {})
      currentGroupIndex.value = parsed.currentGroupIndex || 0
      currentQuestionIndex.value = parsed.currentQuestionIndex || 0
      timer.value = parsed.timer || 0
    }
  } catch (e) { console.warn('[assessment/do] loadDraft:', e) }
}

async function loadQuestions() {
  // 从缓存读取 assignment 配置（pending.vue 跳转时存入）
  let scaleKeys: string[] = []
  try {
    const stored = uni.getStorageSync('assignment_' + assessmentId.value)
    if (stored) {
      const asgn = JSON.parse(stored)
      const s = asgn.scales
      scaleKeys = Array.isArray(s) ? s : (s?.scales || [])
    }
  } catch (e) { /* ignore */ }

  const allGroups = generateDemoQuestions()
  // 按 assignment 的量表配置筛选题目分组；无配置则全量展示
  const filtered = scaleKeys.length ? allGroups.filter(g => scaleKeys.includes(g.key)) : []
  groups.value = filtered.length ? filtered : allGroups
  loadDraft()
}

function generateDemoQuestions(): any[] {
  return [
    { key: 'ttm7', name: 'TTM 行为阶段', questions: [
      { type: 'single', text: '关于改变不健康的行为习惯，您目前处于哪个阶段？', options: ['我没想过要改变', '我在考虑改变', '我准备在近期开始改变', '我已经开始改变了', '我已经保持改变超过6个月'] },
      { type: 'scale', text: '您对改变当前不健康行为的信心程度如何？', min_label: '完全没有信心', max_label: '非常有信心', max: 7 },
      { type: 'boolean', text: '在过去一个月内，您是否尝试过改变某个不健康的生活习惯？' },
    ]},
    { key: 'big5', name: 'BIG5 大五人格', questions: [
      { type: 'scale', text: '我喜欢尝试新事物和新体验。', min_label: '非常不同意', max_label: '非常同意', max: 7 },
      { type: 'scale', text: '我做事有条理且注重细节。', min_label: '非常不同意', max_label: '非常同意', max: 7 },
      { type: 'scale', text: '我在社交场合中感到自在。', min_label: '非常不同意', max_label: '非常同意', max: 7 },
      { type: 'scale', text: '我容易与他人产生共鸣。', min_label: '非常不同意', max_label: '非常同意', max: 7 },
      { type: 'scale', text: '我在压力下容易感到焦虑。', min_label: '非常不同意', max_label: '非常同意', max: 7 },
    ]},
    { key: 'bpt6', name: 'BPT6 行为类型', questions: [
      { type: 'multiple', text: '以下哪些描述最符合您的日常行为模式？（可多选）', options: ['规律运动型', '健康饮食型', '社交活跃型', '学习成长型', '情绪管理型', '作息规律型'] },
      { type: 'single', text: '面对健康目标时，您通常的行动模式是？', options: ['立即行动', '制定计划后行动', '等待合适时机', '需要他人督促'] },
    ]},
  ]
}

// 将答案打包为 custom_answers 格式 → 后端走简化管道，不触发评分引擎
function buildSubmitPayload(): Record<string, any> {
  const custom: Record<string, number> = {}
  groups.value.forEach((g, gi) => {
    g.questions.forEach((_: any, qi: number) => {
      const val = answers[`${gi}_${qi}`]
      if (val === undefined || val === null || val === '') return
      let score: number
      if (typeof val === 'boolean') score = val ? 1 : 0
      else if (Array.isArray(val)) score = val.length  // 多选：选中数量
      else score = Number(val)
      custom[`${g.key}_q${qi + 1}`] = isNaN(score) ? 0 : score
    })
  })
  return { custom_answers: custom }
}

async function submitAssessment() {
  // 有未答题：跳到第一题提示
  if (!allAnswered.value) {
    let found = false
    for (let gi = 0; gi < groups.value.length && !found; gi++) {
      for (let qi = 0; qi < groups.value[gi].questions.length && !found; qi++) {
        const v = answers[`${gi}_${qi}`]
        if (v === undefined || v === null || v === '') {
          currentGroupIndex.value = gi
          currentQuestionIndex.value = qi
          found = true
          uni.showToast({ title: `第${gi + 1}组第${qi + 1}题还没回答`, icon: 'none', duration: 2000 })
        }
      }
    }
    return
  }
  uni.showModal({
    title: '确认提交',
    content: '提交后不可修改，确认提交评估？',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await http(`/api/v1/assessment-assignments/${assessmentId.value}/submit`, {
          method: 'POST',
          data: buildSubmitPayload(),
        })
        try { uni.removeStorageSync('assessment_draft_' + assessmentId.value) } catch (e) { console.warn('[assessment/do] draft:', e) }
        uni.showToast({ title: '提交成功', icon: 'success' })
        setTimeout(() => {
          uni.redirectTo({ url: '/pages/assessment/result?id=' + assessmentId.value })
        }, 800)
      } catch {
        uni.showToast({ title: '提交失败，请重试', icon: 'none' })
      }
    }
  })
}

function confirmExit() {
  const hasAnswers = Object.keys(answers).length > 0
  if (!hasAnswers) { goBack(); return }
  uni.showModal({
    title: '退出评估',
    content: '当前进度已自动保存为草稿，下次可继续',
    confirmText: '退出',
    success: (res) => { if (res.confirm) goBack() }
  })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => {
  const page = getCurrentPages().slice(-1)[0] as any
  assessmentId.value = page?.options?.id || 'demo'
  loadQuestions()
  timerInterval = setInterval(() => { timer.value++ }, 1000)
})

onUnmounted(() => { if (timerInterval) clearInterval(timerInterval) })
</script>

<style scoped>
.do-page { min-height: 100vh; background: #F5F6FA; display: flex; flex-direction: column; }
.do-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.do-nav-back { font-size: 40rpx; padding: 16rpx; }
.do-nav-center { flex: 1; text-align: center; }
.do-nav-group { display: block; font-size: 22rpx; opacity: 0.8; }
.do-nav-scale { display: block; font-size: 30rpx; font-weight: 600; }
.do-nav-timer { font-size: 28rpx; font-family: monospace; background: rgba(255,255,255,0.2); padding: 8rpx 16rpx; border-radius: 8rpx; }

.do-group-progress { display: flex; justify-content: center; gap: 16rpx; padding: 16rpx; }
.do-group-dot { width: 16rpx; height: 16rpx; border-radius: 50%; background: #D0D0D0; }
.do-group-dot--done { background: #27AE60; }
.do-group-dot--active { background: #9B59B6; width: 24rpx; height: 24rpx; margin-top: -4rpx; }

.do-progress-bar { height: 6rpx; background: #E0E0E0; margin: 0 24rpx; border-radius: 3rpx; overflow: hidden; }
.do-progress-fill { height: 100%; background: #9B59B6; border-radius: 3rpx; transition: width 0.3s; }
.do-progress-text { text-align: center; font-size: 22rpx; color: #8E99A4; margin: 8rpx 0; }

.do-question-area { flex: 1; padding: 24rpx; }
.do-question-card { background: #fff; border-radius: 20rpx; padding: 32rpx; min-height: 400rpx; }
.do-question-num { display: inline-block; padding: 4rpx 16rpx; background: #9B59B6; color: #fff; border-radius: 8rpx; font-size: 22rpx; margin-bottom: 16rpx; }
.do-question-text { display: block; font-size: 32rpx; color: #2C3E50; line-height: 1.6; margin-bottom: 32rpx; font-weight: 500; }

.do-options { }
.do-option { display: flex; align-items: center; gap: 16rpx; padding: 24rpx; margin-bottom: 12rpx; border-radius: 12rpx; background: #F8F9FA; border: 2rpx solid transparent; }
.do-option--selected { background: #F0E6F6; border-color: #9B59B6; }
.do-option-indicator { width: 48rpx; height: 48rpx; border-radius: 50%; background: #E0E0E0; color: #5B6B7F; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 600; flex-shrink: 0; }
.do-option--selected .do-option-indicator { background: #9B59B6; color: #fff; }
.do-option-text { flex: 1; font-size: 28rpx; color: #2C3E50; line-height: 1.4; }

.do-scale { }
.do-scale-labels { display: flex; justify-content: space-between; margin-bottom: 16rpx; }
.do-scale-min, .do-scale-max { font-size: 22rpx; color: #8E99A4; }
.do-scale-dots { display: flex; justify-content: space-between; gap: 8rpx; }
.do-scale-dot { flex: 1; height: 80rpx; border-radius: 12rpx; background: #F0F0F0; display: flex; align-items: center; justify-content: center; font-size: 30rpx; color: #5B6B7F; font-weight: 600; }
.do-scale-dot--selected { background: #9B59B6; color: #fff; }

.do-boolean { display: flex; gap: 24rpx; }
.do-bool-btn { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 12rpx; padding: 40rpx; border-radius: 16rpx; background: #F0F0F0; font-size: 32rpx; color: #5B6B7F; }
.do-bool-btn--yes { background: #E8F8F0; color: #27AE60; }
.do-bool-btn--no { background: #FFF0ED; color: #E74C3C; }
.do-bool-icon { font-size: 48rpx; }

.do-text { }
.do-text-input { width: 100%; height: 200rpx; padding: 20rpx; background: #F8F9FA; border-radius: 12rpx; font-size: 28rpx; line-height: 1.6; }

.do-bottom { padding: 24rpx; padding-bottom: calc(24rpx + env(safe-area-inset-bottom)); background: #fff; box-shadow: 0 -2rpx 8rpx rgba(0,0,0,0.04); }
.do-bottom-btns { display: flex; gap: 16rpx; }
.do-btn { flex: 1; text-align: center; padding: 24rpx 0; border-radius: 12rpx; font-size: 28rpx; font-weight: 600; }
.do-btn-prev { background: #F0F0F0; color: #5B6B7F; }
.do-btn-next { background: #9B59B6; color: #fff; }
.do-btn-submit { background: #27AE60; color: #fff; }
.do-btn-submit-warn { background: #E65100; color: #fff; }
</style>