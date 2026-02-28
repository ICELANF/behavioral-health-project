<template>
  <view class="ad-page">

    <!-- 自定义导航栏 -->
    <view class="ad-navbar safe-area-top">
      <view class="ad-navbar__back" @tap="confirmExit">
        <text class="ad-navbar__arrow">‹</text>
      </view>
      <text class="ad-navbar__title">{{ currentGroup?.label || '评估作答' }}</text>
      <view class="ad-navbar__timer">
        <text>{{ formatElapsed(elapsed) }}</text>
      </view>
    </view>

    <!-- 量表分组进度 -->
    <view class="ad-group-bar">
      <text class="ad-group-bar__text">第{{ groupIndex + 1 }}组 / 共{{ groups.length }}组 · {{ currentGroup?.label || '' }}</text>
      <view class="ad-group-bar__track">
        <view class="ad-group-bar__fill" :style="{ width: groupProgress + '%' }"></view>
      </view>
    </view>

    <!-- 组内题目进度 -->
    <view class="ad-q-bar">
      <text class="ad-q-bar__text">{{ qIndex + 1 }} / {{ currentQuestions.length }}</text>
    </view>

    <!-- 题目区 -->
    <scroll-view scroll-y class="ad-body" v-if="currentQ">

      <!-- 题干 -->
      <view class="ad-stem">
        <text class="ad-stem__text">{{ currentQ.title }}</text>
        <text class="ad-stem__hint" v-if="currentQ.description">{{ currentQ.description }}</text>
      </view>

      <!-- ─── single 单选 ─── -->
      <view class="ad-options" v-if="currentQ.question_type === 'single'">
        <view
          v-for="(opt, oi) in currentQ.options"
          :key="oi"
          class="ad-option"
          :class="{ 'ad-option--selected': currentAnswer === oi }"
          @tap="answerSingle(oi)"
        >
          <view class="ad-option__dot" :class="{ 'ad-option__dot--selected': currentAnswer === oi }"></view>
          <text class="ad-option__text">{{ opt.text || opt }}</text>
        </view>
      </view>

      <!-- ─── multiple 多选 ─── -->
      <view class="ad-options" v-else-if="currentQ.question_type === 'multiple'">
        <view
          v-for="(opt, oi) in currentQ.options"
          :key="oi"
          class="ad-option"
          :class="{ 'ad-option--selected': isMultiSelected(oi) }"
          @tap="toggleMulti(oi)"
        >
          <view class="ad-option__check" :class="{ 'ad-option__check--selected': isMultiSelected(oi) }">
            <text v-if="isMultiSelected(oi)">✓</text>
          </view>
          <text class="ad-option__text">{{ opt.text || opt }}</text>
        </view>
      </view>

      <!-- ─── scale 量表滑动 ─── -->
      <view class="ad-scale" v-else-if="currentQ.question_type === 'scale'">
        <view class="ad-scale__labels">
          <text class="ad-scale__label-left">{{ currentQ.scale_min_label || '非常不同意' }}</text>
          <text class="ad-scale__label-right">{{ currentQ.scale_max_label || '非常同意' }}</text>
        </view>
        <view class="ad-scale__dots">
          <view
            v-for="v in 7"
            :key="v"
            class="ad-scale__dot"
            :class="{ 'ad-scale__dot--selected': currentAnswer === v }"
            @tap="answerScale(v)"
          >
            <text>{{ v }}</text>
          </view>
        </view>
      </view>

      <!-- ─── boolean 是/否 ─── -->
      <view class="ad-boolean" v-else-if="currentQ.question_type === 'boolean'">
        <view
          class="ad-bool-btn"
          :class="{ 'ad-bool-btn--selected': currentAnswer === true }"
          @tap="answerBool(true)"
        >
          <text>是</text>
        </view>
        <view
          class="ad-bool-btn"
          :class="{ 'ad-bool-btn--selected': currentAnswer === false }"
          @tap="answerBool(false)"
        >
          <text>否</text>
        </view>
      </view>

      <!-- ─── text 文本输入 ─── -->
      <view class="ad-text" v-else-if="currentQ.question_type === 'text'">
        <textarea
          class="ad-textarea"
          :value="currentAnswer || ''"
          placeholder="请输入您的回答..."
          maxlength="500"
          @input="onTextInput"
        />
      </view>

    </scroll-view>

    <!-- 底部操作栏 -->
    <view class="ad-footer safe-area-bottom">
      <view class="ad-footer__nav">
        <view
          class="ad-footer__btn"
          :class="{ 'ad-footer__btn--disabled': qIndex === 0 && groupIndex === 0 }"
          @tap="goPrev"
        >
          <text>上一题</text>
        </view>
        <!-- 非最后一题：下一题 -->
        <view
          v-if="!(isLastGroup && isLastQ)"
          class="ad-footer__btn ad-footer__btn--primary"
          @tap="goNext"
        >
          <text>{{ isLastQ ? '下一组' : '下一题' }}</text>
        </view>
        <!-- 最后一题：提交 -->
        <view
          v-else
          class="ad-footer__btn ad-footer__btn--submit"
          @tap="confirmSubmit"
        >
          <text>提交评估</text>
        </view>
      </view>
    </view>

    <!-- 提交确认弹窗 -->
    <view class="ad-modal-mask" v-if="showSubmitModal">
      <view class="ad-modal" @tap.stop>
        <text class="ad-modal__title">确认提交</text>
        <text class="ad-modal__desc" v-if="unansweredTotal > 0">还有 {{ unansweredTotal }} 题未作答，确定提交吗？</text>
        <text class="ad-modal__desc" v-else>所有题目已作答，确认提交评估？</text>
        <view class="ad-modal__btns">
          <view class="ad-modal__btn ad-modal__btn--secondary" @tap="showSubmitModal = false">
            <text>继续答题</text>
          </view>
          <view class="ad-modal__btn ad-modal__btn--primary" @tap="doSubmit">
            <text>确认提交</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import http from '@/api/request'

// ── 常量 ─────────────────────────────────────────────
const GROUP_DEFS = [
  { key: 'TTM7',     label: 'TTM7 行为改变阶段' },
  { key: 'BIG5',     label: 'BIG5 大五人格' },
  { key: 'BPT6',     label: 'BPT6 行为类型' },
  { key: 'CAPACITY', label: 'CAPACITY 行为能力' },
  { key: 'SPI',      label: 'SPI 社会参与指数' },
]

// ── 状态 ─────────────────────────────────────────────
const assessmentId   = ref(0)
const groups         = ref<{ key: string; label: string; questions: any[] }[]>([])
const groupIndex     = ref(0)
const qIndex         = ref(0)
const answers        = ref<Record<string, any>>({})  // "groupKey:qIndex" -> answer
const elapsed        = ref(0)
const showSubmitModal = ref(false)
const submitting     = ref(false)

let elapsedTimer: ReturnType<typeof setInterval> | null = null
const draftKey = computed(() => `assessment_draft_${assessmentId.value}`)

// ── Computed ─────────────────────────────────────────
const currentGroup     = computed(() => groups.value[groupIndex.value])
const currentQuestions  = computed(() => currentGroup.value?.questions || [])
const currentQ         = computed(() => currentQuestions.value[qIndex.value])
const answerKey        = computed(() => `${currentGroup.value?.key}:${qIndex.value}`)
const currentAnswer    = computed(() => answers.value[answerKey.value])
const isLastQ          = computed(() => qIndex.value >= currentQuestions.value.length - 1)
const isLastGroup      = computed(() => groupIndex.value >= groups.value.length - 1)

const groupProgress = computed(() => {
  if (!groups.value.length) return 0
  return Math.round(((groupIndex.value + 1) / groups.value.length) * 100)
})

const unansweredTotal = computed(() => {
  let count = 0
  groups.value.forEach(g => {
    g.questions.forEach((_: any, qi: number) => {
      const key = `${g.key}:${qi}`
      const a = answers.value[key]
      if (a === undefined || a === null || a === '') count++
      if (Array.isArray(a) && a.length === 0) count++
    })
  })
  return count
})

// ── 生命周期 ──────────────────────────────────────────
onLoad((query: any) => {
  assessmentId.value = Number(query?.id || query?.assignment_id || 0)
})

onMounted(async () => {
  if (assessmentId.value) {
    restoreDraft()
    await loadQuestions()
  }
  startTimer()
})

onUnmounted(() => {
  stopTimer()
})

// ── 加载题目 ──────────────────────────────────────────
async function loadQuestions() {
  try {
    const res = await http.get<any>(`/v1/assessment-assignments/${assessmentId.value}`)
    const rawGroups = res.groups || res.scales || []

    if (rawGroups.length) {
      groups.value = rawGroups.map((g: any) => ({
        key: g.key || g.scale_key || g.name,
        label: g.label || g.scale_name || g.name,
        questions: g.questions || [],
      }))
    } else if (res.questions?.length) {
      // 没有分组时，按 GROUP_DEFS 顺序归组
      const qMap: Record<string, any[]> = {}
      res.questions.forEach((q: any) => {
        const gk = q.group || q.scale || 'GENERAL'
        if (!qMap[gk]) qMap[gk] = []
        qMap[gk].push(q)
      })
      groups.value = Object.entries(qMap).map(([k, qs]) => {
        const def = GROUP_DEFS.find(d => d.key === k)
        return { key: k, label: def?.label || k, questions: qs }
      })
    }
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

// ── 作答 ─────────────────────────────────────────────
function setAnswer(val: any) {
  answers.value[answerKey.value] = val
  saveDraft()
}

function answerSingle(oi: number) { setAnswer(oi) }
function answerScale(v: number)   { setAnswer(v) }
function answerBool(v: boolean)   { setAnswer(v) }

function isMultiSelected(oi: number): boolean {
  const arr = currentAnswer.value
  return Array.isArray(arr) && arr.includes(oi)
}

function toggleMulti(oi: number) {
  let arr = Array.isArray(currentAnswer.value) ? [...currentAnswer.value] : []
  const pos = arr.indexOf(oi)
  if (pos >= 0) arr.splice(pos, 1)
  else arr.push(oi)
  setAnswer(arr)
}

function onTextInput(e: any) {
  setAnswer(e.detail?.value || '')
}

// ── 导航 ─────────────────────────────────────────────
function goNext() {
  if (!isLastQ.value) {
    qIndex.value++
  } else if (!isLastGroup.value) {
    groupIndex.value++
    qIndex.value = 0
  }
}

function goPrev() {
  if (qIndex.value > 0) {
    qIndex.value--
  } else if (groupIndex.value > 0) {
    groupIndex.value--
    qIndex.value = groups.value[groupIndex.value].questions.length - 1
  }
}

// ── 草稿 ─────────────────────────────────────────────
function saveDraft() {
  try {
    uni.setStorageSync(draftKey.value, JSON.stringify({
      answers: answers.value,
      groupIndex: groupIndex.value,
      qIndex: qIndex.value,
      elapsed: elapsed.value,
    }))
  } catch {/* ignore */}
}

function restoreDraft() {
  try {
    const raw = uni.getStorageSync(draftKey.value)
    if (!raw) return
    const draft = JSON.parse(raw)
    if (draft.answers) answers.value = draft.answers
    if (draft.groupIndex !== undefined) groupIndex.value = draft.groupIndex
    if (draft.qIndex !== undefined) qIndex.value = draft.qIndex
    if (draft.elapsed) elapsed.value = draft.elapsed
  } catch {/* ignore */}
}

function clearDraft() {
  try { uni.removeStorageSync(draftKey.value) } catch {/* ignore */}
}

// ── 提交 ─────────────────────────────────────────────
function confirmSubmit() {
  showSubmitModal.value = true
}

async function doSubmit() {
  if (submitting.value) return
  submitting.value = true
  showSubmitModal.value = false
  try {
    await http.post(`/v1/assessment/evaluate`, {
      assignment_id: assessmentId.value,
      answers: answers.value,
      elapsed_seconds: elapsed.value,
    })
    clearDraft()
    uni.redirectTo({ url: `/pages/assessment/result?id=${assessmentId.value}` })
  } catch {
    uni.showToast({ title: '提交失败，请重试', icon: 'none' })
    submitting.value = false
  }
}

// ── 退出保护 ─────────────────────────────────────────
function confirmExit() {
  const hasAnswers = Object.keys(answers.value).length > 0
  if (!hasAnswers) {
    goBack()
    return
  }
  uni.showModal({
    title: '退出评估',
    content: '答案已暂存为草稿，下次进入可恢复。确认退出吗？',
    confirmText: '退出',
    cancelText: '继续答题',
    success: (res) => {
      if (res.confirm) {
        saveDraft()
        goBack()
      }
    },
  })
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}

// ── 计时 ─────────────────────────────────────────────
function startTimer() {
  stopTimer()
  elapsedTimer = setInterval(() => { elapsed.value++ }, 1000)
}

function stopTimer() {
  if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null }
}

function formatElapsed(s: number): string {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}
</script>

<style scoped>
.ad-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 导航栏 */
.ad-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface);
  border-bottom: 1px solid var(--border-light);
}
.ad-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ad-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.ad-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); max-width: 50%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ad-navbar__timer {
  background: var(--bhp-gray-100); border-radius: var(--radius-full);
  padding: 6rpx 20rpx; font-size: 24rpx; font-weight: 700; color: var(--text-secondary);
}

/* 量表分组进度 */
.ad-group-bar { padding: 16rpx 32rpx 8rpx; background: var(--surface); }
.ad-group-bar__text { font-size: 24rpx; font-weight: 600; color: var(--bhp-primary-500); display: block; margin-bottom: 8rpx; }
.ad-group-bar__track { height: 6rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.ad-group-bar__fill { height: 100%; background: var(--bhp-primary-500); border-radius: var(--radius-full); transition: width 0.3s; }

/* 题号进度 */
.ad-q-bar { padding: 8rpx 32rpx 12rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.ad-q-bar__text { font-size: 22rpx; color: var(--text-tertiary); }

/* 题目区 */
.ad-body { flex: 1; padding: 24rpx 32rpx 180rpx; }

.ad-stem { margin-bottom: 28rpx; }
.ad-stem__text { font-size: 30rpx; font-weight: 600; color: var(--text-primary); line-height: 1.5; display: block; }
.ad-stem__hint { font-size: 24rpx; color: var(--text-tertiary); margin-top: 8rpx; display: block; }

/* 单选/多选 选项 */
.ad-options { display: flex; flex-direction: column; gap: 16rpx; }
.ad-option {
  display: flex; align-items: center; gap: 16rpx;
  padding: 24rpx; background: var(--surface); border-radius: var(--radius-lg);
  border: 2px solid var(--border-light); cursor: pointer; transition: all 0.15s;
}
.ad-option:active { opacity: 0.8; }
.ad-option--selected { border-color: var(--bhp-primary-500); background: rgba(16,185,129,0.04); }
.ad-option__dot {
  width: 40rpx; height: 40rpx; border-radius: 50%;
  border: 2px solid var(--bhp-gray-300); flex-shrink: 0;
}
.ad-option__dot--selected { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); }
.ad-option__check {
  width: 40rpx; height: 40rpx; border-radius: var(--radius-sm);
  border: 2px solid var(--bhp-gray-300); display: flex; align-items: center; justify-content: center;
  font-size: 24rpx; color: #fff; flex-shrink: 0;
}
.ad-option__check--selected { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); }
.ad-option__text { font-size: 28rpx; color: var(--text-primary); line-height: 1.5; flex: 1; }

/* 量表滑动 */
.ad-scale { background: var(--surface); border-radius: var(--radius-lg); padding: 32rpx; }
.ad-scale__labels { display: flex; justify-content: space-between; margin-bottom: 20rpx; }
.ad-scale__label-left,
.ad-scale__label-right { font-size: 22rpx; color: var(--text-tertiary); }
.ad-scale__dots { display: flex; justify-content: space-between; }
.ad-scale__dot {
  width: 72rpx; height: 72rpx; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 700; cursor: pointer;
  background: var(--bhp-gray-100); color: var(--text-secondary);
  border: 2px solid transparent; transition: all 0.15s;
}
.ad-scale__dot:active { opacity: 0.8; }
.ad-scale__dot--selected { background: var(--bhp-primary-500); color: #fff; border-color: var(--bhp-primary-500); }

/* 是/否 */
.ad-boolean { display: flex; gap: 24rpx; }
.ad-bool-btn {
  flex: 1; height: 120rpx; border-radius: var(--radius-xl);
  display: flex; align-items: center; justify-content: center;
  font-size: 32rpx; font-weight: 700; cursor: pointer;
  background: var(--surface); border: 2px solid var(--border-light); color: var(--text-primary);
  transition: all 0.15s;
}
.ad-bool-btn:active { opacity: 0.8; }
.ad-bool-btn--selected { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); color: #fff; }

/* 文本输入 */
.ad-text { background: var(--surface); border-radius: var(--radius-lg); padding: 4rpx; }
.ad-textarea {
  width: 100%; min-height: 240rpx; padding: 20rpx;
  font-size: 28rpx; color: var(--text-primary); line-height: 1.6;
  background: transparent; border: none;
}

/* 底部操作栏 */
.ad-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: var(--surface); border-top: 1px solid var(--border-light);
  padding: 16rpx 32rpx;
}
.ad-footer__nav { display: flex; gap: 16rpx; }
.ad-footer__btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
  background: var(--bhp-gray-100); color: var(--text-secondary);
}
.ad-footer__btn:active { opacity: 0.8; }
.ad-footer__btn--disabled { opacity: 0.4; pointer-events: none; }
.ad-footer__btn--primary { background: var(--bhp-primary-500); color: #fff; }
.ad-footer__btn--submit { background: #f59e0b; color: #fff; }

/* 弹窗 */
.ad-modal-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
  z-index: 999;
}
.ad-modal {
  width: 560rpx; background: var(--surface); border-radius: var(--radius-xl);
  padding: 48rpx 40rpx 36rpx; display: flex; flex-direction: column; gap: 20rpx;
}
.ad-modal__title { font-size: 32rpx; font-weight: 700; color: var(--text-primary); text-align: center; }
.ad-modal__desc { font-size: 26rpx; color: var(--text-secondary); text-align: center; line-height: 1.5; }
.ad-modal__btns { display: flex; gap: 20rpx; margin-top: 12rpx; }
.ad-modal__btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
}
.ad-modal__btn:active { opacity: 0.8; }
.ad-modal__btn--primary { background: var(--bhp-primary-500); color: #fff; }
.ad-modal__btn--secondary { background: var(--bhp-gray-100); color: var(--text-secondary); }
</style>
