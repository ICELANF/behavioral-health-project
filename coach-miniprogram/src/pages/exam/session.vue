<template>
  <view class="es-page">

    <!-- 自定义导航栏 -->
    <view class="es-navbar safe-area-top">
      <view class="es-navbar__back" @tap="confirmExit">
        <text class="es-navbar__arrow">‹</text>
      </view>
      <text class="es-navbar__title">{{ examTitle }}</text>
      <view class="es-navbar__timer" :class="{ 'es-navbar__timer--warn': remainSeconds <= 300 }">
        <text>{{ formatCountdown(remainSeconds) }}</text>
      </view>
    </view>

    <!-- 题号进度 -->
    <view class="es-progress">
      <text class="es-progress__text">{{ currentIndex + 1 }} / {{ questions.length }}</text>
      <view class="es-progress__bar">
        <view class="es-progress__fill" :style="{ width: progressPct + '%' }"></view>
      </view>
    </view>

    <!-- 题目区 -->
    <view class="es-body" v-if="currentQ">

      <!-- 案例内容（图文） -->
      <view class="es-case" v-if="currentQ.question_type === 'case_image' && currentQ.case_content">
        <view class="es-case__label">案例资料</view>
        <rich-text class="es-case__rich" :nodes="currentQ.case_content"></rich-text>
        <image
          v-if="currentQ.case_image_url"
          class="es-case__img"
          :src="currentQ.case_image_url"
          mode="widthFix"
          @tap="previewImage(currentQ.case_image_url)"
        />
      </view>

      <!-- 案例内容（视频） -->
      <view class="es-case" v-if="currentQ.question_type === 'case_video' && currentQ.case_video_url">
        <view class="es-case__label">案例视频</view>
        <video
          class="es-case__video"
          :src="currentQ.case_video_url"
          :poster="currentQ.case_cover_url || ''"
          :show-fullscreen-btn="true"
          :show-play-btn="true"
          object-fit="contain"
        />
      </view>

      <!-- 题干 -->
      <view class="es-stem">
        <view class="es-stem__type-tag">{{ questionTypeLabel(currentQ.question_type) }}</view>
        <text class="es-stem__text">{{ currentQ.title }}</text>
      </view>

      <!-- 单选 / 案例题选项 -->
      <view class="es-options" v-if="currentQ.question_type !== 'multi'">
        <view
          v-for="(opt, oi) in currentQ.options"
          :key="oi"
          class="es-option"
          :class="{ 'es-option--selected': isSingleSelected(oi) }"
          @tap="selectSingle(oi)"
        >
          <view class="es-option__index" :class="{ 'es-option__index--selected': isSingleSelected(oi) }">
            <text>{{ optionLetter(oi) }}</text>
          </view>
          <text class="es-option__text">{{ opt.text || opt }}</text>
        </view>
      </view>

      <!-- 多选 -->
      <view class="es-options" v-else>
        <view
          v-for="(opt, oi) in currentQ.options"
          :key="oi"
          class="es-option"
          :class="{ 'es-option--selected': isMultiSelected(oi) }"
          @tap="toggleMulti(oi)"
        >
          <view class="es-option__check" :class="{ 'es-option__check--selected': isMultiSelected(oi) }">
            <text v-if="isMultiSelected(oi)">✓</text>
          </view>
          <text class="es-option__text">{{ opt.text || opt }}</text>
        </view>
      </view>
    </view>

    <!-- 底部操作栏 -->
    <view class="es-footer safe-area-bottom">
      <view class="es-footer__nav">
        <view class="es-footer__btn" :class="{ 'es-footer__btn--disabled': currentIndex === 0 }" @tap="prevQ">
          <text>上一题</text>
        </view>
        <view class="es-footer__btn es-footer__btn--card" @tap="showCard = true">
          <text>答题卡</text>
        </view>
        <view
          v-if="currentIndex < questions.length - 1"
          class="es-footer__btn es-footer__btn--primary"
          @tap="nextQ"
        >
          <text>下一题</text>
        </view>
        <view
          v-else
          class="es-footer__btn es-footer__btn--submit"
          @tap="confirmSubmit"
        >
          <text>提交</text>
        </view>
      </view>
    </view>

    <!-- 答题卡弹窗 -->
    <view class="es-card-mask" v-if="showCard" @tap="showCard = false">
      <view class="es-card-panel" @tap.stop>
        <text class="es-card-panel__title">答题卡</text>
        <view class="es-card-grid">
          <view
            v-for="(q, qi) in questions"
            :key="qi"
            class="es-card-cell"
            :class="{
              'es-card-cell--answered': isAnswered(qi),
              'es-card-cell--current': qi === currentIndex,
            }"
            @tap="jumpTo(qi)"
          >
            <text>{{ qi + 1 }}</text>
          </view>
        </view>
        <view class="es-card-legend">
          <view class="es-card-legend__item">
            <view class="es-card-legend__dot es-card-legend__dot--answered"></view>
            <text class="es-card-legend__text">已答 {{ answeredCount }}</text>
          </view>
          <view class="es-card-legend__item">
            <view class="es-card-legend__dot es-card-legend__dot--unanswered"></view>
            <text class="es-card-legend__text">未答 {{ questions.length - answeredCount }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 提交确认弹窗 -->
    <view class="es-card-mask" v-if="showSubmitModal">
      <view class="es-card-panel" @tap.stop>
        <text class="es-card-panel__title">确认提交</text>
        <text class="es-modal-desc" v-if="unansweredCount > 0">
          还有 {{ unansweredCount }} 题未作答，确定提交吗？
        </text>
        <text class="es-modal-desc" v-else>所有题目已作答，确认提交？</text>
        <view class="es-modal-btns">
          <view class="es-modal-btn es-modal-btn--secondary" @tap="showSubmitModal = false">
            <text>继续答题</text>
          </view>
          <view class="es-modal-btn es-modal-btn--primary" @tap="doSubmit">
            <text>确认提交</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 切后台警告弹窗 -->
    <view class="es-card-mask" v-if="showBgWarning">
      <view class="es-card-panel" @tap.stop>
        <text class="es-card-panel__title">考试警告</text>
        <text class="es-modal-desc">您已离开考试页面超过30秒，请注意考试纪律。</text>
        <view class="es-modal-btns">
          <view class="es-modal-btn es-modal-btn--primary" style="flex:1;" @tap="showBgWarning = false">
            <text>我知道了</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import http from '@/api/request'

// ── 状态 ─────────────────────────────────────────────
const examTitle      = ref('')
const sessionId      = ref(0)
const questions      = ref<any[]>([])
const currentIndex   = ref(0)
const answers        = ref<Record<number, any>>({})   // questionIndex -> answer
const remainSeconds  = ref(0)
const showCard       = ref(false)
const showSubmitModal = ref(false)
const showBgWarning  = ref(false)
const submitting     = ref(false)

let countdownTimer: ReturnType<typeof setInterval> | null = null
let hideTimestamp = 0

// ── Computed ─────────────────────────────────────────
const currentQ      = computed(() => questions.value[currentIndex.value] || null)
const progressPct   = computed(() => questions.value.length ? Math.round(((currentIndex.value + 1) / questions.value.length) * 100) : 0)
const answeredCount = computed(() => Object.keys(answers.value).length)
const unansweredCount = computed(() => questions.value.length - answeredCount.value)

// ── 生命周期 ──────────────────────────────────────────
onLoad((query: any) => {
  sessionId.value = Number(query?.session_id || query?.id || 0)
})

onMounted(async () => {
  if (sessionId.value) await loadSession()
})

onHide(() => {
  hideTimestamp = Date.now()
})

onShow(() => {
  if (hideTimestamp > 0) {
    const away = (Date.now() - hideTimestamp) / 1000
    if (away >= 30) showBgWarning.value = true
    hideTimestamp = 0
  }
})

onUnmounted(() => {
  stopCountdown()
})

// ── 加载考试 ──────────────────────────────────────────
async function loadSession() {
  try {
    const res = await http.get<any>(`/v1/certification/sessions/${sessionId.value}/questions`)
    examTitle.value = res.exam_title || '认证考试'
    questions.value = res.questions || []
    remainSeconds.value = (res.remaining_seconds ?? (res.time_limit_minutes || 60) * 60)

    // 恢复已答状态
    if (res.questions) {
      res.questions.forEach((q: any, i: number) => {
        if (q.user_answer !== undefined && q.user_answer !== null) {
          answers.value[i] = q.user_answer
        }
      })
    }

    startCountdown()
  } catch {
    uni.showToast({ title: '加载考试失败', icon: 'none' })
  }
}

// ── 倒计时 ───────────────────────────────────────────
function startCountdown() {
  stopCountdown()
  countdownTimer = setInterval(() => {
    if (remainSeconds.value <= 0) {
      stopCountdown()
      autoSubmit()
      return
    }
    remainSeconds.value--
  }, 1000)
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

async function autoSubmit() {
  uni.showToast({ title: '考试时间到，自动提交', icon: 'none', duration: 2000 })
  await doSubmit()
}

// ── 选择答案 ──────────────────────────────────────────
function isSingleSelected(oi: number): boolean {
  return answers.value[currentIndex.value] === oi
}

function selectSingle(oi: number) {
  answers.value[currentIndex.value] = oi
  saveAnswer(currentIndex.value)
}

function isMultiSelected(oi: number): boolean {
  const arr = answers.value[currentIndex.value]
  return Array.isArray(arr) && arr.includes(oi)
}

function toggleMulti(oi: number) {
  const idx = currentIndex.value
  if (!Array.isArray(answers.value[idx])) answers.value[idx] = []
  const arr = answers.value[idx] as number[]
  const pos = arr.indexOf(oi)
  if (pos >= 0) arr.splice(pos, 1)
  else arr.push(oi)
  answers.value[idx] = [...arr]
  saveAnswer(idx)
}

// ── 立即保存单题 ─────────────────────────────────────
async function saveAnswer(qIndex: number) {
  const q = questions.value[qIndex]
  if (!q) return
  const qid = q.id || q.question_id
  try {
    await http.post(`/v1/certification/sessions/${sessionId.value}/answer`, {
      question_id: qid,
      answer: answers.value[qIndex],
    })
  } catch {/* 静默，下次重试 */}
}

// ── 导航 ─────────────────────────────────────────────
function prevQ() { if (currentIndex.value > 0) currentIndex.value-- }
function nextQ() { if (currentIndex.value < questions.length - 1) currentIndex.value++ }
function jumpTo(i: number) { currentIndex.value = i; showCard.value = false }

function isAnswered(i: number): boolean {
  const a = answers.value[i]
  if (a === undefined || a === null) return false
  if (Array.isArray(a) && a.length === 0) return false
  return true
}

// ── 提交 ─────────────────────────────────────────────
function confirmSubmit() {
  showSubmitModal.value = true
}

async function doSubmit() {
  if (submitting.value) return
  submitting.value = true
  showSubmitModal.value = false
  stopCountdown()
  try {
    await http.post(`/v1/certification/sessions/${sessionId.value}/submit`, {})
    uni.redirectTo({ url: `/pages/exam/result?session_id=${sessionId.value}` })
  } catch {
    uni.showToast({ title: '提交失败，请重试', icon: 'none' })
    submitting.value = false
    startCountdown()
  }
}

function confirmExit() {
  uni.showModal({
    title: '退出考试',
    content: '答题进度已实时保存，确定退出吗？',
    confirmText: '退出',
    cancelText: '继续答题',
    success: (res) => {
      if (res.confirm) uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
    },
  })
}

// ── 工具 ─────────────────────────────────────────────
function formatCountdown(s: number): string {
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

function optionLetter(i: number): string {
  return String.fromCharCode(65 + i)
}

function questionTypeLabel(type: string): string {
  const map: Record<string, string> = {
    single: '单选题', multi: '多选题', case_image: '案例题(图文)', case_video: '案例题(视频)',
  }
  return map[type] || '选择题'
}

function previewImage(url: string) {
  uni.previewImage({ urls: [url], current: url })
}
</script>

<style scoped>
.es-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 导航栏 */
.es-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface);
  border-bottom: 1px solid var(--border-light);
}
.es-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.es-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.es-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); max-width: 40%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.es-navbar__timer {
  background: var(--bhp-gray-100); border-radius: var(--radius-full);
  padding: 6rpx 20rpx; font-size: 26rpx; font-weight: 700; color: var(--text-primary);
}
.es-navbar__timer--warn { background: #fef2f2; color: #dc2626; }

/* 进度条 */
.es-progress { padding: 16rpx 32rpx; display: flex; align-items: center; gap: 16rpx; background: var(--surface); }
.es-progress__text { font-size: 24rpx; color: var(--text-secondary); font-weight: 600; white-space: nowrap; }
.es-progress__bar { flex: 1; height: 8rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.es-progress__fill { height: 100%; background: var(--bhp-primary-500); border-radius: var(--radius-full); transition: width 0.3s; }

/* 题目区 */
.es-body { flex: 1; padding: 24rpx 32rpx 180rpx; overflow-y: auto; }

/* 案例 */
.es-case { background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light); }
.es-case__label { font-size: 22rpx; color: var(--bhp-primary-500); font-weight: 700; margin-bottom: 12rpx; }
.es-case__rich { font-size: 26rpx; color: var(--text-primary); line-height: 1.6; }
.es-case__img { width: 100%; border-radius: var(--radius-md); margin-top: 16rpx; }
.es-case__video { width: 100%; height: 360rpx; border-radius: var(--radius-md); margin-top: 16rpx; }

/* 题干 */
.es-stem { margin-bottom: 24rpx; }
.es-stem__type-tag {
  display: inline-block; font-size: 20rpx; font-weight: 700; color: var(--bhp-primary-500);
  background: rgba(16,185,129,0.1); padding: 4rpx 16rpx; border-radius: var(--radius-full); margin-bottom: 12rpx;
}
.es-stem__text { font-size: 30rpx; font-weight: 600; color: var(--text-primary); line-height: 1.5; display: block; }

/* 选项 */
.es-options { display: flex; flex-direction: column; gap: 16rpx; }
.es-option {
  display: flex; align-items: flex-start; gap: 16rpx;
  padding: 24rpx; background: var(--surface); border-radius: var(--radius-lg);
  border: 2px solid var(--border-light); cursor: pointer; transition: all 0.15s;
}
.es-option:active { opacity: 0.8; }
.es-option--selected { border-color: var(--bhp-primary-500); background: rgba(16,185,129,0.04); }
.es-option__index {
  width: 48rpx; height: 48rpx; border-radius: 50%;
  border: 2px solid var(--bhp-gray-300); display: flex; align-items: center; justify-content: center;
  font-size: 24rpx; font-weight: 700; color: var(--text-secondary); flex-shrink: 0;
}
.es-option__index--selected { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); color: #fff; }
.es-option__check {
  width: 40rpx; height: 40rpx; border-radius: var(--radius-sm);
  border: 2px solid var(--bhp-gray-300); display: flex; align-items: center; justify-content: center;
  font-size: 24rpx; color: #fff; flex-shrink: 0;
}
.es-option__check--selected { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); }
.es-option__text { font-size: 28rpx; color: var(--text-primary); line-height: 1.5; flex: 1; padding-top: 4rpx; }

/* 底部栏 */
.es-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: var(--surface); border-top: 1px solid var(--border-light);
  padding: 16rpx 32rpx;
}
.es-footer__nav { display: flex; gap: 16rpx; }
.es-footer__btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
  background: var(--bhp-gray-100); color: var(--text-secondary);
}
.es-footer__btn:active { opacity: 0.8; }
.es-footer__btn--disabled { opacity: 0.4; pointer-events: none; }
.es-footer__btn--primary { background: var(--bhp-primary-500); color: #fff; }
.es-footer__btn--submit { background: #f59e0b; color: #fff; }
.es-footer__btn--card { flex: 0.8; }

/* 答题卡弹窗 */
.es-card-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: flex-end; justify-content: center;
  z-index: 999;
}
.es-card-panel {
  width: 100%; max-height: 70vh; background: var(--surface);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding: 36rpx 32rpx 48rpx; display: flex; flex-direction: column; gap: 24rpx;
}
.es-card-panel__title { font-size: 32rpx; font-weight: 700; color: var(--text-primary); text-align: center; }
.es-card-grid { display: flex; flex-wrap: wrap; gap: 16rpx; justify-content: flex-start; }
.es-card-cell {
  width: 72rpx; height: 72rpx; border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  font-size: 26rpx; font-weight: 600; cursor: pointer;
  background: var(--bhp-gray-100); color: var(--text-secondary);
}
.es-card-cell--answered { background: var(--bhp-primary-500); color: #fff; }
.es-card-cell--current { border: 2px solid var(--bhp-primary-500); }
.es-card-legend { display: flex; gap: 32rpx; justify-content: center; }
.es-card-legend__item { display: flex; align-items: center; gap: 8rpx; }
.es-card-legend__dot { width: 20rpx; height: 20rpx; border-radius: var(--radius-sm); }
.es-card-legend__dot--answered { background: var(--bhp-primary-500); }
.es-card-legend__dot--unanswered { background: var(--bhp-gray-100); }
.es-card-legend__text { font-size: 22rpx; color: var(--text-secondary); }

/* 确认弹窗 */
.es-modal-desc { font-size: 28rpx; color: var(--text-secondary); text-align: center; line-height: 1.5; }
.es-modal-btns { display: flex; gap: 20rpx; margin-top: 8rpx; }
.es-modal-btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
}
.es-modal-btn:active { opacity: 0.8; }
.es-modal-btn--primary { background: var(--bhp-primary-500); color: #fff; }
.es-modal-btn--secondary { background: var(--bhp-gray-100); color: var(--text-secondary); }
</style>
