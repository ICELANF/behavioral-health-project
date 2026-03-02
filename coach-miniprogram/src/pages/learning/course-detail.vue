<template>
  <view class="cdet-page">
    <view v-if="loading" class="cdet-loading"><text>加载中...</text></view>

    <scroll-view v-else-if="course" scroll-y class="cdet-scroll">
      <image v-if="course.cover_url" :src="course.cover_url" class="cdet-cover" mode="aspectFill" />
      <view v-else class="cdet-cover cdet-cover--ph"><text>📚</text></view>

      <view class="cdet-body">
        <text class="cdet-title">{{ course.title }}</text>
        <text class="cdet-desc">{{ course.description }}</text>
        <view class="cdet-meta">
          <text class="cdet-meta-item">📝 {{ course.lesson_count || 0 }} 课时</text>
          <text class="cdet-meta-item">⏱ 约{{ course.estimated_hours || 0 }}小时</text>
          <text class="cdet-meta-item">🏅 {{ course.total_points || 0 }}学分</text>
        </view>
      </view>

      <!-- 章节列表 -->
      <view class="cdet-chapters">
        <text class="cdet-chapters-title">课程章节</text>
        <view v-for="(ch, i) in chapters" :key="i" class="cdet-ch-item" @tap="goChapter(ch, i)">
          <text class="cdet-ch-num">{{ i + 1 }}</text>
          <view class="cdet-ch-info">
            <text class="cdet-ch-title">{{ ch.title }}</text>
            <text class="cdet-ch-duration">{{ ch.duration_min || 10 }}分钟</text>
          </view>
          <text class="cdet-ch-arrow">›</text>
        </view>
        <view v-if="chapters.length === 0" class="cdet-no-chapters">
          <text>章节内容即将更新</text>
        </view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>

    <view v-else class="cdet-empty">
      <text class="cdet-empty-icon">📚</text>
      <text class="cdet-empty-text">课程加载失败</text>
    </view>
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

const course = ref<any>(null)
const chapters = ref<any[]>([])
const loading = ref(false)
let courseId = 0

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  courseId = Number(page?.options?.id || 0)
  if (!courseId) return
  loading.value = true
  try {
    const data = await http<any>(`/api/v1/content/courses/${courseId}`)
    course.value = data
    chapters.value = data?.chapters || []
  } catch { course.value = null } finally { loading.value = false }
})

function goChapter(ch: any, idx: number) {
  uni.navigateTo({ url: `/pages/learning/course-chapter?course_id=${courseId}&chapter_index=${idx}&chapter_id=${ch.id || ''}` })
}
</script>

<style scoped>
.cdet-page { min-height: 100vh; background: #F5F6FA; }
.cdet-loading { display: flex; align-items: center; justify-content: center; height: 100vh; font-size: 28rpx; color: #8E99A4; }
.cdet-scroll { height: 100vh; }
.cdet-cover { width: 100%; height: 400rpx; display: block; }
.cdet-cover--ph { display: flex; align-items: center; justify-content: center; background: #E8F8F0; font-size: 80rpx; }
.cdet-body { background: #fff; padding: 24rpx 32rpx; }
.cdet-title { display: block; font-size: 36rpx; font-weight: 700; color: #2C3E50; margin-bottom: 12rpx; }
.cdet-desc { display: block; font-size: 26rpx; color: #5B6B7F; line-height: 1.6; margin-bottom: 20rpx; }
.cdet-meta { display: flex; gap: 20rpx; flex-wrap: wrap; }
.cdet-meta-item { font-size: 22rpx; color: #8E99A4; }
.cdet-chapters { background: #fff; margin: 16rpx 24rpx; border-radius: 16rpx; padding: 20rpx 0; }
.cdet-chapters-title { display: block; font-size: 28rpx; font-weight: 700; color: #2C3E50; padding: 0 24rpx 16rpx; }
.cdet-ch-item { display: flex; align-items: center; gap: 16rpx; padding: 18rpx 24rpx; border-bottom: 1rpx solid #F8F8F8; }
.cdet-ch-item:last-child { border-bottom: none; }
.cdet-ch-num { width: 48rpx; height: 48rpx; border-radius: 50%; background: #E8F8F0; color: #2D8E69; font-size: 24rpx; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.cdet-ch-info { flex: 1; }
.cdet-ch-title { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.cdet-ch-duration { font-size: 20rpx; color: #8E99A4; }
.cdet-ch-arrow { font-size: 32rpx; color: #CCC; }
.cdet-no-chapters { padding: 24rpx; text-align: center; font-size: 24rpx; color: #8E99A4; }
.cdet-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; gap: 16rpx; }
.cdet-empty-icon { font-size: 64rpx; }
.cdet-empty-text { font-size: 26rpx; color: #8E99A4; }
</style>
