<template>
  <view class="ap-page">

    <!-- 封面 -->
    <view class="ap-cover-area">
      <view class="ap-cover" :class="{ 'ap-cover--playing': playing }">
        <image
          v-if="content?.cover_url"
          class="ap-cover__img"
          :src="content.cover_url"
          mode="aspectFill"
        />
        <view v-else class="ap-cover__default">
          <text>🎵</text>
        </view>
      </view>
    </view>

    <!-- 标题 -->
    <view class="ap-title-area px-4">
      <text class="ap-title">{{ content?.title || '加载中...' }}</text>
      <view class="flex-start gap-2 mt-2 justify-center">
        <view class="bhp-badge bhp-badge--primary" v-if="content?.module">
          <text>{{ content?.module?.toUpperCase() }}</text>
        </view>
        <text class="text-xs text-secondary-color">{{ content?.author_name || '行健平台' }}</text>
        <text class="text-xs text-secondary-color" v-if="content?.duration">
          共 {{ formatDuration(content.duration) }}
        </text>
      </view>
    </view>

    <!-- 进度条 -->
    <view class="ap-progress-area px-4">
      <slider
        class="ap-slider"
        :value="sliderValue"
        :min="0"
        :max="100"
        :step="0.1"
        block-color="var(--bhp-primary-500)"
        active-color="var(--bhp-primary-500)"
        background-color="var(--bhp-gray-200)"
        @changing="onSliderChanging"
        @change="onSliderChange"
      />
      <view class="ap-time-row">
        <text class="ap-time">{{ formatDuration(currentTime) }}</text>
        <text class="ap-time">{{ formatDuration(totalDuration) }}</text>
      </view>
    </view>

    <!-- 播放控制 -->
    <view class="ap-controls">
      <!-- 后退15s -->
      <view class="ap-ctrl-btn" @tap="seek(-15)">
        <text class="ap-ctrl-icon">⏪</text>
        <text class="ap-ctrl-label">15</text>
      </view>

      <!-- 播放/暂停 -->
      <view class="ap-play-btn" @tap="togglePlay">
        <text class="ap-play-icon">{{ playing ? '⏸' : '▶' }}</text>
      </view>

      <!-- 前进15s -->
      <view class="ap-ctrl-btn" @tap="seek(15)">
        <text class="ap-ctrl-icon">⏩</text>
        <text class="ap-ctrl-label">15</text>
      </view>
    </view>

    <!-- 倍速选择 -->
    <view class="ap-speed-area px-4">
      <view class="ap-speed-row">
        <view
          v-for="speed in speeds"
          :key="speed"
          class="ap-speed-btn"
          :class="{ 'ap-speed-btn--active': playbackRate === speed }"
          @tap="setSpeed(speed)"
        >
          <text>{{ speed }}x</text>
        </view>
      </view>
    </view>

    <!-- 摘要 -->
    <view class="ap-summary px-4" v-if="content?.summary">
      <view class="ap-summary__card">
        <text class="ap-summary__label">内容摘要</text>
        <text class="ap-summary__text">{{ content.summary }}</text>
      </view>
    </view>

    <!-- 完成提示 -->
    <view class="ap-complete px-4" v-if="audioCompleted && content?.has_quiz && content?.quiz_id && !quizDone">
      <view class="bhp-btn bhp-btn--primary bhp-btn--full" @tap="goQuiz">
        <text>完成！开始测验 →</text>
      </view>
    </view>

    <view style="height: 60rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { contentApi, learningApi, type ContentDetail } from '@/api/learning'

const userStore = useUserStore()

const contentId     = ref(0)
const content       = ref<ContentDetail | null>(null)
const loading       = ref(false)
const playing       = ref(false)
const currentTime   = ref(0)
const totalDuration = ref(0)
const sliderValue   = ref(0)   // 0-100
const sliderDragging= ref(false)
const playbackRate  = ref(1)
const audioCompleted= ref(false)
const quizDone      = ref(false)

const speeds = [0.75, 1, 1.25, 1.5, 2]

let audioContext: UniApp.InnerAudioContext | null = null
let heartbeatTimer: any = null
let lastSavedTime = 0

onMounted(async () => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}
  contentId.value = Number(query.id || 0)
  if (contentId.value) {
    await loadContent()
    await loadProgress()
    initAudio()
  }
})

onUnmounted(() => {
  stopHeartbeat()
  saveProgress()
  destroyAudio()
})

async function loadContent() {
  loading.value = true
  try {
    content.value = await contentApi.detail(contentId.value)
    uni.setNavigationBarTitle({ title: content.value.title })
    if (content.value.duration) totalDuration.value = content.value.duration
  } catch {
    uni.showToast({ title: '内容加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function loadProgress() {
  try {
    const p = await contentApi.getProgress(contentId.value)
    if (p.last_position) {
      currentTime.value = Number(p.last_position) || 0
    }
    if (p.progress_percent >= 100) {
      audioCompleted.value = true
    }
  } catch { /* 静默 */ }
}

function initAudio() {
  if (!content.value?.media_url) return
  audioContext = uni.createInnerAudioContext()
  audioContext.src = content.value.media_url
  audioContext.startTime = currentTime.value
  audioContext.obeyMuteSwitch = false

  audioContext.onPlay(() => { playing.value = true })
  audioContext.onPause(() => { playing.value = false })
  audioContext.onStop(() => { playing.value = false })
  audioContext.onEnded(() => {
    playing.value = false
    audioCompleted.value = true
    stopHeartbeat()
    saveProgressNow(100, 'completed')
    if (!content.value?.has_quiz || !content.value?.quiz_id) {
      triggerComplete()
    }
  })
  audioContext.onTimeUpdate(() => {
    if (!audioContext) return
    currentTime.value = audioContext.currentTime || 0
    if (!totalDuration.value && audioContext.duration) {
      totalDuration.value = audioContext.duration
    }
    if (!sliderDragging.value && totalDuration.value > 0) {
      sliderValue.value = (currentTime.value / totalDuration.value) * 100
    }
  })
  audioContext.onError((e: any) => {
    uni.showToast({ title: '音频播放失败', icon: 'none' })
    playing.value = false
  })

  startHeartbeat()
}

function destroyAudio() {
  if (audioContext) {
    audioContext.stop()
    audioContext.destroy()
    audioContext = null
  }
}

function togglePlay() {
  if (!audioContext) return
  if (playing.value) {
    audioContext.pause()
  } else {
    audioContext.play()
  }
}

function seek(delta: number) {
  if (!audioContext || !totalDuration.value) return
  const target = Math.max(0, Math.min(totalDuration.value, currentTime.value + delta))
  audioContext.seek(target)
  currentTime.value = target
}

function onSliderChanging(e: any) {
  sliderDragging.value = true
  sliderValue.value = e.detail.value
}

function onSliderChange(e: any) {
  sliderDragging.value = false
  if (!audioContext || !totalDuration.value) return
  const target = (e.detail.value / 100) * totalDuration.value
  audioContext.seek(target)
  currentTime.value = target
}

function setSpeed(rate: number) {
  playbackRate.value = rate
  if (audioContext) {
    (audioContext as any).playbackRate = rate
  }
}

function startHeartbeat() {
  heartbeatTimer = setInterval(() => {
    if (playing.value && Math.abs(currentTime.value - lastSavedTime) >= 30) {
      saveProgress()
    }
  }, 5000)
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

function saveProgress() {
  if (!contentId.value || !totalDuration.value) return
  const pct = Math.round((currentTime.value / totalDuration.value) * 100)
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
  } catch { /* 静默 */ }
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
        title: `+${res.points_earned}积分${res.credits_earned > 0 ? ` +${res.credits_earned}学分` : ''}`,
        icon: 'none',
        duration: 3000
      })
      userStore.addPoints(res.points_earned, 0, 0)
    }
  } catch { /* 静默 */ }
}

function formatDuration(sec: number): string {
  if (!sec || isNaN(sec)) return '0:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function goQuiz() {
  if (!content.value?.quiz_id) return
  uni.navigateTo({
    url: `/pages/learning/quiz?quiz_id=${content.value.quiz_id}&content_id=${contentId.value}`
  })
}
</script>

<style scoped>
.ap-page {
  background: var(--surface);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 封面 */
.ap-cover-area {
  padding: 60rpx 0 40rpx;
  display: flex;
  justify-content: center;
}
.ap-cover {
  width: 360rpx;
  height: 360rpx;
  border-radius: var(--radius-2xl, 24px);
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  transition: transform 0.3s;
}
.ap-cover--playing {
  animation: ap-spin 20s linear infinite;
}
@keyframes ap-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.ap-cover__img { width: 100%; height: 100%; }
.ap-cover__default {
  width: 100%;
  height: 100%;
  background: var(--bhp-gray-100);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 120rpx;
}

/* 标题 */
.ap-title-area { text-align: center; width: 100%; }
.ap-title {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.4;
}

/* 进度条 */
.ap-progress-area { width: 100%; padding-top: 40rpx; }
.ap-slider { width: 100%; }
.ap-time-row { display: flex; justify-content: space-between; margin-top: -8rpx; }
.ap-time { font-size: 22rpx; color: var(--text-secondary); }

/* 控制 */
.ap-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 60rpx;
  padding: 40rpx 0 24rpx;
  width: 100%;
}
.ap-ctrl-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  cursor: pointer;
}
.ap-ctrl-btn:active { opacity: 0.6; }
.ap-ctrl-icon { font-size: 40rpx; }
.ap-ctrl-label { font-size: 18rpx; color: var(--text-secondary); }

.ap-play-btn {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: var(--bhp-primary-500);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(16,185,129,0.4);
  cursor: pointer;
}
.ap-play-btn:active { opacity: 0.8; transform: scale(0.95); }
.ap-play-icon { font-size: 48rpx; color: #fff; }

/* 倍速 */
.ap-speed-area { width: 100%; }
.ap-speed-row { display: flex; justify-content: center; gap: 16rpx; }
.ap-speed-btn {
  padding: 8rpx 24rpx;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-default);
  font-size: 24rpx;
  color: var(--text-secondary);
  cursor: pointer;
}
.ap-speed-btn--active {
  background: var(--bhp-primary-500);
  border-color: var(--bhp-primary-500);
  color: #fff;
  font-weight: 600;
}

/* 摘要 */
.ap-summary { width: 100%; padding-top: 32rpx; }
.ap-summary__card {
  background: var(--surface-secondary);
  border-radius: var(--radius-lg);
  padding: 20rpx;
}
.ap-summary__label { display: block; font-size: 22rpx; color: var(--text-tertiary); margin-bottom: 8rpx; }
.ap-summary__text { font-size: 26rpx; color: var(--text-secondary); line-height: 1.6; }

.ap-complete { width: 100%; padding-top: 24rpx; }
</style>
