<template>
  <view class="vp-page">

    <!-- 视频播放器 -->
    <view class="vp-video-wrap">
      <video
        id="bhp-video"
        class="vp-video"
        :src="videoUrl"
        :title="content?.title || ''"
        :initial-time="initialTime"
        :enable-progress-gesture="true"
        :show-fullscreen-btn="true"
        :show-play-btn="true"
        :show-center-play-btn="true"
        :show-mute-btn="true"
        object-fit="contain"
        @timeupdate="onTimeUpdate"
        @ended="onEnded"
        @error="onError"
      ></video>
    </view>

    <!-- 骨架屏 -->
    <template v-if="loading">
      <view class="px-4 mt-4">
        <view class="bhp-skeleton" style="height: 36rpx; width: 80%; margin-bottom: 12rpx;"></view>
        <view class="bhp-skeleton" style="height: 28rpx; width: 50%; margin-bottom: 8rpx;"></view>
      </view>
    </template>

    <template v-else-if="content">
      <!-- 标题与元信息 -->
      <view class="vp-info px-4">
        <text class="vp-title">{{ content.title }}</text>
        <view class="vp-meta flex-start gap-4 mt-2">
          <view class="bhp-badge bhp-badge--primary" v-if="content.module">
            <text>{{ content.module?.toUpperCase() }}</text>
          </view>
          <text class="text-xs text-secondary-color">{{ content.author_name || '行健平台' }}</text>
          <text class="text-xs text-secondary-color" v-if="content.duration">
            {{ formatDuration(content.duration) }}
          </text>
          <text class="text-xs text-secondary-color">{{ content.view_count || 0 }} 播放</text>
        </view>
      </view>

      <!-- 进度条 -->
      <view class="vp-progress-row px-4">
        <view class="vp-progress-bar">
          <view class="vp-progress-fill" :style="{ width: progressPercent + '%' }"></view>
        </view>
        <text class="vp-progress-text">{{ Math.round(progressPercent) }}%</text>
      </view>

      <!-- 摘要 -->
      <view class="vp-summary px-4" v-if="content.summary">
        <view class="vp-summary__card">
          <text class="text-sm text-secondary-color">{{ content.summary }}</text>
        </view>
      </view>

      <!-- 完成提示 -->
      <view class="vp-complete-tip px-4" v-if="videoCompleted">
        <view class="vp-complete-tip__card">
          <text class="vp-complete-tip__icon">🎉</text>
          <view class="flex-1">
            <text class="vp-complete-tip__title">视频已看完！</text>
            <text class="vp-complete-tip__sub" v-if="!quizDone && content.has_quiz">
              完成随堂测验获得学分和积分
            </text>
          </view>
          <view
            v-if="content.has_quiz && content.quiz_id && !quizDone"
            class="bhp-btn bhp-btn--primary"
            style="padding: 8rpx 24rpx;"
            @tap="goQuiz"
          >
            <text>测验</text>
          </view>
        </view>
      </view>
    </template>

    <!-- 返回按钮（自定义导航栏区域）-->
    <view class="vp-nav-back" @tap="goBack">
      <text>‹</text>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useLearningStore } from '@/stores/learning'
import { contentApi, learningApi, type ContentDetail } from '@/api/learning'

const userStore    = useUserStore()
const learningStore= useLearningStore()

const contentId     = ref(0)
const content       = ref<ContentDetail | null>(null)
const loading       = ref(false)
const videoUrl      = ref('')
const initialTime   = ref(0)
const currentTime   = ref(0)
const duration      = ref(0)
const videoCompleted= ref(false)
const quizDone      = ref(false)

// 30s 心跳定时器
let heartbeatTimer: any = null
let lastSavedTime = 0

const progressPercent = computed(() => {
  if (!duration.value) return 0
  return Math.min((currentTime.value / duration.value) * 100, 100)
})

onMounted(async () => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}
  contentId.value = Number(query.id || 0)
  if (contentId.value) {
    await loadContent()
    await loadProgress()
    startHeartbeat()
  }
})

onUnmounted(() => {
  stopHeartbeat()
  saveProgress() // 离开时保存
})

async function loadContent() {
  loading.value = true
  try {
    content.value = await contentApi.detail(contentId.value)
    videoUrl.value = content.value.media_url || ''
    if (content.value.duration) duration.value = content.value.duration
    uni.setNavigationBarTitle({ title: content.value.title })
  } catch {
    uni.showToast({ title: '内容加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function loadProgress() {
  try {
    const p = await contentApi.getProgress(contentId.value)
    const pct = p.progress_percent || 0
    if (pct >= 100) {
      videoCompleted.value = true
    }
    // 恢复播放位置
    if (p.last_position) {
      initialTime.value = Number(p.last_position) || 0
      currentTime.value = initialTime.value
    }
  } catch { /* 静默 */ }
}

function onTimeUpdate(e: any) {
  currentTime.value = e.detail?.currentTime || 0
  if (e.detail?.duration) duration.value = e.detail.duration
}

function onEnded() {
  videoCompleted.value = true
  stopHeartbeat()
  saveProgressNow(100, 'completed')
  // 如无测验，弹出完成积分
  if (!content.value?.has_quiz || !content.value?.quiz_id) {
    triggerComplete()
  }
}

function onError(e: any) {
  uni.showToast({ title: '视频播放失败', icon: 'none' })
}

function startHeartbeat() {
  heartbeatTimer = setInterval(() => {
    if (Math.abs(currentTime.value - lastSavedTime) >= 30) {
      saveProgress()
    }
  }, 5000) // 5s 轮询，满足30s变化才上报
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

function saveProgress() {
  if (!contentId.value || !duration.value) return
  const pct = Math.round((currentTime.value / duration.value) * 100)
  saveProgressNow(pct, pct >= 95 ? 'completed' : 'in_progress')
}

async function saveProgressNow(pct: number, status: 'in_progress' | 'completed' = 'in_progress') {
  lastSavedTime = currentTime.value
  try {
    await contentApi.saveProgress({
      content_id: contentId.value,
      progress_percent: pct,
      last_position: String(Math.round(currentTime.value)),
      time_spent_seconds: Math.round(currentTime.value),
      status
    })
  } catch { /* 静默，不打扰用户 */ }
}

async function triggerComplete() {
  if (!content.value?.module) return
  try {
    const res = await learningApi.completeModule(
      `${content.value.module}_${contentId.value}`,
      'content'
    )
    if (res.points_earned > 0 || res.credits_earned > 0) {
      uni.showToast({
        title: `恭喜！+${res.points_earned}积分${res.credits_earned > 0 ? ` +${res.credits_earned}学分` : ''}`,
        icon: 'none',
        duration: 3000
      })
      userStore.addPoints(res.points_earned, 0, 0)
    }
  } catch { /* 静默 */ }
}

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

function goQuiz() {
  if (!content.value?.quiz_id) return
  uni.navigateTo({
    url: `/pages/learning/quiz?quiz_id=${content.value.quiz_id}&content_id=${contentId.value}`
  })
}

function goBack() {
  uni.navigateBack()
}
</script>

<style scoped>
.vp-page { background: #000; min-height: 100vh; }

/* 视频区 */
.vp-video-wrap {
  width: 100%;
  background: #000;
}
.vp-video {
  width: 100%;
  height: 420rpx;
}

/* 返回按钮（覆盖自定义导航栏区域）*/
.vp-nav-back {
  position: fixed;
  top: 0;
  left: 0;
  padding: 60rpx 28rpx 20rpx;
  z-index: 100;
  font-size: 56rpx;
  color: #fff;
  text-shadow: 0 1px 4px rgba(0,0,0,0.8);
}

/* 信息区 */
.vp-info {
  background: var(--surface);
  padding-top: 24rpx;
  padding-bottom: 16rpx;
}
.vp-title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.4;
}

/* 进度条 */
.vp-progress-row {
  background: var(--surface);
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding-top: 16rpx;
  padding-bottom: 16rpx;
  border-bottom: 1px solid var(--border-light);
}
.vp-progress-bar {
  flex: 1;
  height: 8rpx;
  background: var(--bhp-gray-200);
  border-radius: 9999px;
  overflow: hidden;
}
.vp-progress-fill {
  height: 100%;
  background: var(--bhp-primary-500);
  border-radius: 9999px;
  transition: width 0.5s;
}
.vp-progress-text { font-size: 22rpx; color: var(--text-secondary); width: 60rpx; text-align: right; }

/* 摘要 */
.vp-summary { padding-top: 16rpx; }
.vp-summary__card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 20rpx;
}

/* 完成提示 */
.vp-complete-tip { padding-top: 16rpx; }
.vp-complete-tip__card {
  background: var(--bhp-success-50, #f0fdf4);
  border: 1px solid var(--bhp-success-200, #bbf7d0);
  border-radius: var(--radius-lg);
  padding: 20rpx 24rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.vp-complete-tip__icon { font-size: 40rpx; }
.vp-complete-tip__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--bhp-success-700, #15803d); }
.vp-complete-tip__sub { display: block; font-size: 22rpx; color: var(--bhp-success-600, #16a34a); margin-top: 4rpx; }
</style>
