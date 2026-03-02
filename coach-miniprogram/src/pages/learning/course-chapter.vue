<template>
  <view class="cc-page">
    <view v-if="loading" class="cc-loading"><text>加载中...</text></view>
    <scroll-view v-else scroll-y class="cc-scroll">
      <view class="cc-hero">
        <text class="cc-title">{{ title }}</text>
        <view class="cc-meta">
          <text class="cc-meta-item">⏱ {{ duration }}分钟</text>
        </view>
      </view>

      <view class="cc-content">
        <rich-text v-if="content" :nodes="content" class="cc-richtext" />
        <text v-else class="cc-placeholder">本章节内容正在整理中...</text>
      </view>

      <view class="cc-nav">
        <view class="cc-nav-btn" @tap="goBack"><text>← 返回课程</text></view>
        <view v-if="hasQuiz" class="cc-quiz-btn" @tap="goQuiz">
          <text>章节测验 →</text>
        </view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'
function getToken() { return uni.getStorageSync('access_token') || '' }

async function http<T = any>(url: string): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url, method: 'GET',
      header: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' },
      success: (res: any) => {
        if (res.statusCode === 401) { uni.removeStorageSync('access_token'); uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('401')); return }
        res.statusCode < 300 ? resolve(res.data as T) : reject(new Error(`${res.statusCode}`))
      },
      fail: (e: any) => reject(e),
    })
  })
}

const title = ref('章节学习')
const content = ref('')
const duration = ref(10)
const hasQuiz = ref(false)
const loading = ref(false)
let courseId = 0, chapterId = 0, chapterIndex = 0

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  courseId = Number(page?.options?.course_id || 0)
  chapterId = Number(page?.options?.chapter_id || 0)
  chapterIndex = Number(page?.options?.chapter_index || 0)
  if (chapterId) {
    loading.value = true
    try {
      const data = await http<any>(`/api/v1/content/${chapterId}`)
      title.value = data?.title || `第 ${chapterIndex + 1} 章`
      content.value = data?.subtitle || data?.content || ''
      duration.value = data?.estimated_minutes || 10
      hasQuiz.value = !!data?.has_quiz
    } catch {} finally { loading.value = false }
  }
})

function goBack() { uni.navigateBack() }
function goQuiz() { uni.navigateTo({ url: `/pages/learning/quiz?content_id=${chapterId}` }) }
</script>

<style scoped>
.cc-page { min-height: 100vh; background: #F5F6FA; }
.cc-loading { display: flex; align-items: center; justify-content: center; height: 100vh; font-size: 28rpx; color: #8E99A4; }
.cc-scroll { height: 100vh; }
.cc-hero { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); padding: 40rpx 32rpx; color: #fff; padding-top: calc(40rpx + env(safe-area-inset-top)); }
.cc-title { display: block; font-size: 36rpx; font-weight: 700; margin-bottom: 12rpx; }
.cc-meta { display: flex; gap: 16rpx; }
.cc-meta-item { font-size: 22rpx; opacity: 0.85; }
.cc-content { background: #fff; margin: 24rpx; border-radius: 16rpx; padding: 28rpx; }
.cc-richtext { font-size: 28rpx; color: #2C3E50; line-height: 1.9; }
.cc-placeholder { display: block; font-size: 26rpx; color: #8E99A4; text-align: center; padding: 40rpx 0; }
.cc-nav { display: flex; gap: 16rpx; padding: 0 24rpx; }
.cc-nav-btn, .cc-quiz-btn { flex: 1; padding: 20rpx; border-radius: 16rpx; text-align: center; font-size: 28rpx; font-weight: 600; }
.cc-nav-btn { background: #fff; color: #2D8E69; border: 2rpx solid #2D8E69; }
.cc-quiz-btn { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
</style>
