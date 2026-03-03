<template>
  <view class="intro-page">
    <view v-if="loading" class="intro-loading"><text>加载中...</text></view>

    <scroll-view v-else-if="exam" scroll-y class="intro-scroll">
      <!-- 考试信息卡 -->
      <view class="intro-hero">
        <view class="intro-level-badge">{{ exam.level || 'L1' }}</view>
        <text class="intro-title">{{ exam.exam_name || exam.title }}</text>
        <text class="intro-desc">{{ exam.description }}</text>
      </view>

      <!-- 考试规则 -->
      <view class="intro-rules">
        <view class="intro-rule-title">考试须知</view>
        <view class="intro-rule-item">
          <text class="intro-rule-icon">📝</text>
          <text class="intro-rule-text">共 <text class="intro-rule-em">{{ exam.question_count || 0 }}</text> 道题目</text>
        </view>
        <view class="intro-rule-item">
          <text class="intro-rule-icon">⏱</text>
          <text class="intro-rule-text">考试时间 <text class="intro-rule-em">{{ exam.duration_minutes }}</text> 分钟</text>
        </view>
        <view class="intro-rule-item">
          <text class="intro-rule-icon">🎯</text>
          <text class="intro-rule-text">满分100分，<text class="intro-rule-em">{{ exam.passing_score }}</text> 分及以上通过</text>
        </view>
        <view class="intro-rule-item">
          <text class="intro-rule-icon">🔁</text>
          <text class="intro-rule-text">最多可参加 <text class="intro-rule-em">{{ exam.max_attempts }}</text> 次</text>
        </view>
        <view class="intro-rule-item">
          <text class="intro-rule-icon">📌</text>
          <text class="intro-rule-text">答题过程中请勿离开页面</text>
        </view>
      </view>

      <!-- 开始按钮 -->
      <view class="intro-actions">
        <view class="intro-start-btn" @tap="startExam">
          <text>开始考试</text>
        </view>
        <view class="intro-history-btn" @tap="goHistory">
          <text>查看记录</text>
        </view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>

    <view v-else class="intro-error">
      <text class="intro-error-icon">😕</text>
      <text class="intro-error-text">考试信息加载失败</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const exam = ref<any>(null)
const loading = ref(false)
let examId = 0

onMounted(() => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  examId = Number(page?.options?.id || 0)
  if (examId) loadData()
})

async function loadData() {
  loading.value = true
  try {
    exam.value = await http<any>(`/api/v1/certification/exams/${examId}`)
  } catch {
    // fallback: get from list
    try {
      const res = await http<any>('/api/v1/certification/exams')
      exam.value = (res?.items || []).find((e: any) => e.id === examId) || null
    } catch { exam.value = null }
  } finally { loading.value = false }
}

async function startExam() {
  uni.showModal({
    title: '确认开始考试',
    content: `本次考试共${exam.value?.question_count || 0}题，${exam.value?.duration_minutes}分钟内完成`,
    success: async (res) => {
      if (res.confirm) {
        try {
          const session = await http<any>(`/api/v1/certification/exams/${examId}/start`, { method: 'POST' })
          if (session?.session_id || session?.id) {
            const sid = session.session_id || session.id
            uni.navigateTo({ url: '/pages/exam/session?session_id=' + sid + '&exam_id=' + examId })
          } else {
            uni.showToast({ title: '考试开始失败', icon: 'none' })
          }
        } catch {
          uni.showToast({ title: '无法开始考试', icon: 'none' })
        }
      }
    }
  })
}

function goHistory() {
  uni.navigateTo({ url: '/pages/exam/history' })
}
</script>

<style scoped>
.intro-page { min-height: 100vh; background: #F5F6FA; }
.intro-loading { display: flex; align-items: center; justify-content: center; height: 100vh; font-size: 28rpx; color: #8E99A4; }
.intro-scroll { height: 100vh; }

.intro-hero {
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  padding: 48rpx 32rpx; color: #fff; text-align: center;
  padding-top: calc(48rpx + env(safe-area-inset-top));
}
.intro-level-badge { display: inline-block; background: rgba(255,255,255,0.25); color: #fff; font-size: 22rpx; font-weight: 700; padding: 6rpx 20rpx; border-radius: 12rpx; margin-bottom: 16rpx; }
.intro-title { display: block; font-size: 40rpx; font-weight: 700; margin-bottom: 16rpx; }
.intro-desc { display: block; font-size: 24rpx; opacity: 0.85; line-height: 1.6; }

.intro-rules { background: #fff; margin: 24rpx; border-radius: 16rpx; padding: 24rpx; }
.intro-rule-title { font-size: 28rpx; font-weight: 700; color: #2C3E50; margin-bottom: 20rpx; }
.intro-rule-item { display: flex; align-items: center; gap: 16rpx; padding: 12rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.intro-rule-item:last-child { border-bottom: none; }
.intro-rule-icon { font-size: 30rpx; flex-shrink: 0; }
.intro-rule-text { font-size: 26rpx; color: #5B6B7F; }
.intro-rule-em { color: #2D8E69; font-weight: 700; }

.intro-actions { padding: 0 24rpx; display: flex; flex-direction: column; gap: 16rpx; }
.intro-start-btn { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); border-radius: 16rpx; padding: 24rpx; text-align: center; color: #fff; font-size: 32rpx; font-weight: 700; }
.intro-history-btn { border: 2rpx solid #2D8E69; border-radius: 16rpx; padding: 22rpx; text-align: center; color: #2D8E69; font-size: 28rpx; }

.intro-error { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; gap: 16rpx; }
.intro-error-icon { font-size: 80rpx; }
.intro-error-text { font-size: 28rpx; color: #8E99A4; }
</style>
