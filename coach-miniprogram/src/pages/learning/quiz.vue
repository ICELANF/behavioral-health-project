<template>
  <view class="qz-page">

    <!-- 导航栏 -->
    <view class="qz-navbar safe-area-top">
      <view class="qz-navbar__back" @tap="goBack">
        <text class="qz-navbar__arrow">‹</text>
      </view>
      <text class="qz-navbar__title">随堂测验</text>
      <view class="qz-navbar__placeholder"></view>
    </view>

    <!-- 答题中 -->
    <template v-if="!finished">
      <!-- 进度 -->
      <view class="qz-progress">
        <text class="qz-progress__text">{{ currentIndex + 1 }} / {{ questions.length }}</text>
        <view class="qz-progress__bar">
          <view class="qz-progress__fill" :style="{ width: progressPct + '%' }"></view>
        </view>
      </view>

      <!-- 题目 -->
      <view class="qz-body" v-if="currentQ">
        <view class="qz-stem">
          <view class="qz-stem__tag">{{ currentQ.question_type === 'multi' ? '多选题' : '单选题' }}</view>
          <text class="qz-stem__text">{{ currentQ.title }}</text>
        </view>

        <!-- 单选 -->
        <view class="qz-options" v-if="currentQ.question_type !== 'multi'">
          <view
            v-for="(opt, oi) in currentQ.options"
            :key="oi"
            class="qz-option"
            :class="{
              'qz-option--selected': !submitted && userAnswer === oi,
              'qz-option--correct': submitted && oi === currentQ.correct_answer,
              'qz-option--wrong': submitted && userAnswer === oi && oi !== currentQ.correct_answer,
            }"
            @tap="selectSingle(oi)"
          >
            <view class="qz-option__index">
              <text>{{ optionLetter(oi) }}</text>
            </view>
            <text class="qz-option__text">{{ opt.text || opt }}</text>
          </view>
        </view>

        <!-- 多选 -->
        <view class="qz-options" v-else>
          <view
            v-for="(opt, oi) in currentQ.options"
            :key="oi"
            class="qz-option"
            :class="{
              'qz-option--selected': !submitted && isMultiSelected(oi),
              'qz-option--correct': submitted && isCorrectOption(oi),
              'qz-option--wrong': submitted && isMultiSelected(oi) && !isCorrectOption(oi),
            }"
            @tap="toggleMulti(oi)"
          >
            <view class="qz-option__check" :class="{ 'qz-option__check--selected': isMultiSelected(oi) }">
              <text v-if="isMultiSelected(oi)">✓</text>
            </view>
            <text class="qz-option__text">{{ opt.text || opt }}</text>
          </view>
        </view>

        <!-- 解析（提交后显示） -->
        <view class="qz-explain" v-if="submitted">
          <view class="qz-explain__header">
            <text class="qz-explain__icon">{{ isCurrentCorrect ? '✅' : '❌' }}</text>
            <text class="qz-explain__result" :class="isCurrentCorrect ? 'text-primary-color' : 'text-error-color'">
              {{ isCurrentCorrect ? '回答正确' : '回答错误' }}
            </text>
          </view>
          <text class="qz-explain__text" v-if="currentQ.explanation">{{ currentQ.explanation }}</text>
        </view>
      </view>

      <!-- 底部按钮 -->
      <view class="qz-footer safe-area-bottom">
        <view v-if="!submitted" class="qz-footer__btn qz-footer__btn--primary" @tap="submitAnswer">
          <text>确认答案</text>
        </view>
        <view v-else class="qz-footer__btn qz-footer__btn--primary" @tap="nextQuestion">
          <text>{{ currentIndex < questions.length - 1 ? '下一题' : '查看结果' }}</text>
        </view>
      </view>
    </template>

    <!-- 结果页 -->
    <template v-else>
      <view class="qz-result">
        <view class="qz-result__score-ring">
          <text class="qz-result__score">{{ correctCount }}</text>
          <text class="qz-result__total">/ {{ questions.length }}</text>
        </view>
        <text class="qz-result__label">答对题数</text>
        <view class="qz-result__bonus" v-if="isPerfect">
          <text>🎉 满分！额外获得 +5 积分</text>
        </view>
        <view class="qz-result__actions">
          <view class="qz-footer__btn qz-footer__btn--primary" @tap="goBack">
            <text>返回继续学习</text>
          </view>
        </view>
      </view>
    </template>

  </view>
</template>

<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const contentId    = ref(0)
const questions    = ref<any[]>([])
const currentIndex = ref(0)
const userAnswer   = ref<any>(null)
const submitted    = ref(false)
const finished     = ref(false)
const correctCount = ref(0)

const currentQ   = computed(() => questions.value[currentIndex.value])
const progressPct = computed(() => questions.value.length ? Math.round(((currentIndex.value + 1) / questions.value.length) * 100) : 0)
const isPerfect  = computed(() => correctCount.value === questions.value.length && questions.value.length > 0)

const isCurrentCorrect = computed(() => {
  if (!currentQ.value) return false
  if (currentQ.value.question_type === 'multi') {
    const correct = [...(currentQ.value.correct_answer || [])].sort()
    const user = [...(Array.isArray(userAnswer.value) ? userAnswer.value : [])].sort()
    return JSON.stringify(correct) === JSON.stringify(user)
  }
  return userAnswer.value === currentQ.value.correct_answer
})

onLoad((query: any) => {
  contentId.value = Number(query?.content_id || query?.id || 0)
})

onMounted(async () => {
  if (contentId.value) await loadQuiz()
})

async function loadQuiz() {
  try {
    const res = await http.get<any>(`/v1/content/${contentId.value}/quiz`)
    questions.value = res.questions || res.items || []
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

function selectSingle(oi: number) {
  if (submitted.value) return
  userAnswer.value = oi
}

function isMultiSelected(oi: number): boolean {
  return Array.isArray(userAnswer.value) && userAnswer.value.includes(oi)
}

function isCorrectOption(oi: number): boolean {
  const ca = currentQ.value?.correct_answer
  return Array.isArray(ca) && ca.includes(oi)
}

function toggleMulti(oi: number) {
  if (submitted.value) return
  if (!Array.isArray(userAnswer.value)) userAnswer.value = []
  const arr = [...userAnswer.value]
  const pos = arr.indexOf(oi)
  if (pos >= 0) arr.splice(pos, 1)
  else arr.push(oi)
  userAnswer.value = arr
}

function submitAnswer() {
  if (userAnswer.value === null || (Array.isArray(userAnswer.value) && userAnswer.value.length === 0)) {
    uni.showToast({ title: '请先选择答案', icon: 'none' })
    return
  }
  submitted.value = true
  if (isCurrentCorrect.value) correctCount.value++
}

function nextQuestion() {
  if (currentIndex.value < questions.length - 1) {
    currentIndex.value++
    userAnswer.value = null
    submitted.value = false
  } else {
    finished.value = true
    // 提交结果到服务端
    http.post(`/v1/content/${contentId.value}/quiz/submit`, {
      correct_count: correctCount.value,
      total: questions.value.length,
    }).catch(() => {})
  }
}

function optionLetter(i: number): string { return String.fromCharCode(65 + i) }

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.qz-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

.qz-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.qz-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.qz-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.qz-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.qz-navbar__placeholder { width: 64rpx; }

.qz-progress { padding: 16rpx 32rpx; background: var(--surface); display: flex; align-items: center; gap: 16rpx; }
.qz-progress__text { font-size: 24rpx; color: var(--text-secondary); font-weight: 600; white-space: nowrap; }
.qz-progress__bar { flex: 1; height: 8rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.qz-progress__fill { height: 100%; background: var(--bhp-primary-500); border-radius: var(--radius-full); transition: width 0.3s; }

.qz-body { flex: 1; padding: 24rpx 32rpx 180rpx; }
.qz-stem { margin-bottom: 28rpx; }
.qz-stem__tag {
  display: inline-block; font-size: 20rpx; font-weight: 700; color: var(--bhp-primary-500);
  background: rgba(16,185,129,0.1); padding: 4rpx 16rpx; border-radius: var(--radius-full); margin-bottom: 12rpx;
}
.qz-stem__text { font-size: 30rpx; font-weight: 600; color: var(--text-primary); line-height: 1.5; display: block; }

.qz-options { display: flex; flex-direction: column; gap: 16rpx; }
.qz-option {
  display: flex; align-items: center; gap: 16rpx;
  padding: 24rpx; background: var(--surface); border-radius: var(--radius-lg);
  border: 2px solid var(--border-light); cursor: pointer; transition: all 0.15s;
}
.qz-option:active { opacity: 0.8; }
.qz-option--selected { border-color: var(--bhp-primary-500); background: rgba(16,185,129,0.04); }
.qz-option--correct { border-color: var(--bhp-primary-500); background: rgba(16,185,129,0.08); }
.qz-option--wrong { border-color: #ef4444; background: rgba(239,68,68,0.06); }
.qz-option__index {
  width: 48rpx; height: 48rpx; border-radius: 50%;
  border: 2px solid var(--bhp-gray-300); display: flex; align-items: center; justify-content: center;
  font-size: 24rpx; font-weight: 700; color: var(--text-secondary); flex-shrink: 0;
}
.qz-option--selected .qz-option__index { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); color: #fff; }
.qz-option--correct .qz-option__index { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); color: #fff; }
.qz-option--wrong .qz-option__index { background: #ef4444; border-color: #ef4444; color: #fff; }
.qz-option__check {
  width: 40rpx; height: 40rpx; border-radius: var(--radius-sm);
  border: 2px solid var(--bhp-gray-300); display: flex; align-items: center; justify-content: center;
  font-size: 24rpx; color: #fff; flex-shrink: 0;
}
.qz-option__check--selected { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); }
.qz-option__text { font-size: 28rpx; color: var(--text-primary); line-height: 1.5; flex: 1; }

.qz-explain {
  margin-top: 24rpx; padding: 20rpx 24rpx; background: var(--surface);
  border-radius: var(--radius-lg); border: 1px solid var(--border-light);
}
.qz-explain__header { display: flex; align-items: center; gap: 8rpx; margin-bottom: 8rpx; }
.qz-explain__icon { font-size: 32rpx; }
.qz-explain__result { font-size: 26rpx; font-weight: 700; }
.qz-explain__text { font-size: 26rpx; color: var(--text-secondary); line-height: 1.6; display: block; }

.qz-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  padding: 16rpx 32rpx; background: var(--surface); border-top: 1px solid var(--border-light);
}
.qz-footer__btn {
  width: 100%; height: 88rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; font-weight: 700; cursor: pointer;
}
.qz-footer__btn:active { opacity: 0.85; }
.qz-footer__btn--primary { background: var(--bhp-primary-500); color: #fff; }

/* 结果页 */
.qz-result {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 20rpx; padding: 60rpx 32rpx;
}
.qz-result__score-ring {
  width: 200rpx; height: 200rpx; border-radius: 50%;
  background: rgba(16,185,129,0.1); border: 6rpx solid var(--bhp-primary-500);
  display: flex; align-items: baseline; justify-content: center; padding-top: 60rpx;
}
.qz-result__score { font-size: 72rpx; font-weight: 800; color: var(--bhp-primary-500); }
.qz-result__total { font-size: 32rpx; color: var(--text-secondary); }
.qz-result__label { font-size: 28rpx; color: var(--text-secondary); }
.qz-result__bonus {
  background: #fffbe6; border: 1px solid #ffe58f; border-radius: var(--radius-lg);
  padding: 16rpx 32rpx; font-size: 26rpx; font-weight: 600; color: #d48806;
}
.qz-result__actions { width: 100%; padding: 0 32rpx; margin-top: 20rpx; }
</style>
