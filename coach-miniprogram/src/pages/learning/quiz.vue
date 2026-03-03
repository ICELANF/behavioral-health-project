<template>
  <view class="quiz-page">
    <view class="quiz-header">
      <text class="quiz-title">随堂测验</text>
      <text class="quiz-progress">{{ currentIndex + 1 }}/{{ questions.length }}</text>
    </view>

    <view class="quiz-progress-bar">
      <view class="quiz-progress-fill" :style="{ width: progressPct + '%' }" />
    </view>

    <scroll-view v-if="currentQ" scroll-y class="quiz-body">
      <view class="quiz-q-card">
        <text class="quiz-q-text">{{ currentQ.question_text }}</text>
      </view>

      <view class="quiz-options">
        <view v-for="opt in parsedOptions" :key="opt.key"
          class="quiz-option"
          :class="{ 'quiz-option--selected': answers[currentQ.id] === opt.key }"
          @tap="answers[currentQ.id] = opt.key">
          <view class="quiz-opt-key">{{ opt.key }}</view>
          <text class="quiz-opt-text">{{ opt.text }}</text>
        </view>
      </view>

      <view style="height:160rpx;"></view>
    </scroll-view>

    <view v-else class="quiz-empty">
      <text>暂无题目</text>
    </view>

    <view class="quiz-footer">
      <view v-if="currentIndex > 0" class="quiz-btn quiz-btn--prev" @tap="currentIndex--">
        <text>上一题</text>
      </view>
      <view v-else class="quiz-btn quiz-btn--placeholder" />
      <view v-if="currentIndex < questions.length - 1" class="quiz-btn quiz-btn--next" @tap="currentIndex++">
        <text>下一题</text>
      </view>
      <view v-else class="quiz-btn quiz-btn--submit" @tap="submitQuiz">
        <text>提交</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const questions = ref<any[]>([])
const answers = ref<Record<number, string>>({})
const currentIndex = ref(0)
let contentId = 0

const currentQ = computed(() => questions.value[currentIndex.value] || null)
const progressPct = computed(() => questions.value.length > 0 ? (currentIndex.value + 1) / questions.value.length * 100 : 0)

const parsedOptions = computed(() => {
  if (!currentQ.value?.options) return []
  const opts = typeof currentQ.value.options === 'string' ? JSON.parse(currentQ.value.options) : currentQ.value.options
  return (Array.isArray(opts) ? opts : []).map((o: string) => {
    const m = o.match(/^([A-D])[.、]\s*(.+)$/)
    return m ? { key: m[1], text: m[2] } : { key: o[0], text: o.slice(2).trim() }
  })
})

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  contentId = Number(page?.options?.content_id || 0)
  if (contentId) {
    try {
      const res = await http<any>(`/api/v1/content/${contentId}/quiz`)
      questions.value = res?.questions || []
    } catch { questions.value = [] }
  }
})

async function submitQuiz() {
  const answered = Object.keys(answers.value).length
  if (answered < questions.value.length) {
    const ok = await new Promise<boolean>((resolve) => {
      uni.showModal({ title: '提示', content: `还有 ${questions.value.length - answered} 题未作答，确认提交？`, success: r => resolve(!!r.confirm) })
    })
    if (!ok) return
  }
  try {
    const res = await http<any>(`/api/v1/content/${contentId}/quiz/submit`, { method: 'POST', data: answers.value })
    uni.redirectTo({ url: '/pages/learning/quiz-result?content_id=' + contentId + '&score=' + (res?.score || 0) + '&total=' + questions.value.length })
  } catch {
    uni.showToast({ title: '提交失败', icon: 'none' })
  }
}
</script>

<style scoped>
.quiz-page { min-height: 100vh; background: #F5F6FA; display: flex; flex-direction: column; }
.quiz-header { display: flex; justify-content: space-between; align-items: center; padding: 20rpx 32rpx; padding-top: calc(20rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
.quiz-title { font-size: 32rpx; font-weight: 700; }
.quiz-progress { font-size: 26rpx; opacity: 0.85; }
.quiz-progress-bar { height: 6rpx; background: rgba(45,142,105,0.15); }
.quiz-progress-fill { height: 100%; background: #2D8E69; }
.quiz-body { flex: 1; height: calc(100vh - 220rpx); }
.quiz-q-card { background: #fff; margin: 24rpx; padding: 28rpx; border-radius: 16rpx; }
.quiz-q-text { font-size: 30rpx; color: #2C3E50; line-height: 1.6; font-weight: 600; }
.quiz-options { padding: 0 24rpx; }
.quiz-option { display: flex; align-items: flex-start; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 20rpx 24rpx; margin-bottom: 12rpx; border: 2rpx solid transparent; }
.quiz-option--selected { border-color: #2D8E69; background: #EAFAF2; }
.quiz-opt-key { width: 44rpx; height: 44rpx; border-radius: 50%; background: #F0F0F0; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 700; color: #5B6B7F; flex-shrink: 0; }
.quiz-option--selected .quiz-opt-key { background: #2D8E69; color: #fff; }
.quiz-opt-text { flex: 1; font-size: 27rpx; color: #2C3E50; line-height: 1.5; }
.quiz-empty { flex: 1; display: flex; align-items: center; justify-content: center; font-size: 26rpx; color: #8E99A4; }
.quiz-footer { display: flex; gap: 12rpx; padding: 16rpx 24rpx; padding-bottom: calc(16rpx + env(safe-area-inset-bottom)); background: #fff; border-top: 1rpx solid #F0F0F0; }
.quiz-btn { flex: 1; padding: 20rpx; border-radius: 16rpx; text-align: center; font-size: 28rpx; font-weight: 600; }
.quiz-btn--placeholder { background: transparent; }
.quiz-btn--prev { background: #F5F6FA; color: #5B6B7F; border: 1rpx solid #E0E0E0; }
.quiz-btn--next { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
.quiz-btn--submit { background: linear-gradient(135deg, #E67E22 0%, #E74C3C 100%); color: #fff; }
</style>
