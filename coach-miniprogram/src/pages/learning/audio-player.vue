<template>
  <view class="ap-page">
    <view class="ap-navbar safe-area-top">
      <view class="ap-navbar__back" @tap="goBack"><text class="ap-navbar__arrow">‹</text></view>
      <text class="ap-navbar__title">音频播放</text>
      <view class="ap-navbar__placeholder"></view>
    </view>

    <view class="ap-content" v-if="content">
      <!-- 封面 -->
      <view class="ap-cover-wrap">
        <image class="ap-cover" :src="content.cover_url || '/static/covers/default.jpg'" mode="aspectFill" />
      </view>

      <!-- 标题信息 -->
      <view class="ap-info">
        <text class="ap-info__title">{{ content.title }}</text>
        <text class="ap-info__author">{{ content.author?.name || '平台' }}</text>
      </view>

      <!-- 播放控制 -->
      <view class="ap-controls">
        <!-- 进度条 -->
        <view class="ap-progress">
          <slider
            :value="progress"
            :max="duration"
            activeColor="var(--bhp-primary-500)"
            block-size="16"
            @change="seekTo"
          />
          <view class="ap-progress__time">
            <text>{{ formatSec(progress) }}</text>
            <text>{{ formatSec(duration) }}</text>
          </view>
        </view>

        <!-- 控制按钮 -->
        <view class="ap-btns">
          <view class="ap-btn ap-btn--speed" @tap="cycleSpeed">
            <text>{{ playbackRate }}x</text>
          </view>
          <view class="ap-btn ap-btn--play" @tap="togglePlay">
            <text>{{ playing ? '⏸' : '▶' }}</text>
          </view>
          <view class="ap-btn ap-btn--speed" @tap="forward15">
            <text>+15s</text>
          </view>
        </view>
      </view>

      <!-- 互动栏 -->
      <view class="ap-actions">
        <view class="ap-action" @tap="toggleLike">
          <text>{{ liked ? '❤️' : '🤍' }}</text>
          <text class="ap-action__count">{{ content.like_count || 0 }}</text>
        </view>
        <view class="ap-action" @tap="toggleCollect">
          <text>{{ collected ? '⭐' : '☆' }}</text>
          <text class="ap-action__count">{{ content.collect_count || 0 }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import http from '@/api/request'

const content      = ref<any>(null)
const playing      = ref(false)
const progress     = ref(0)
const duration     = ref(0)
const playbackRate = ref(1.0)
const liked        = ref(false)
const collected    = ref(false)
const contentId    = ref(0)

const SPEEDS = [0.75, 1.0, 1.25, 1.5]
let audioCtx: any = null
let timer: any = null

onMounted(() => {
  const pages = getCurrentPages()
  const pg = pages[pages.length - 1] as any
  contentId.value = Number(pg.$page?.options?.id || pg.options?.id || 0)
  if (contentId.value) loadContent()
})

onUnmounted(() => {
  if (audioCtx) { audioCtx.stop(); audioCtx.destroy() }
  if (timer) clearInterval(timer)
})

async function loadContent() {
  try {
    content.value = await http.get<any>(`/v1/content/detail/audio/${contentId.value}`)
    if (content.value.media_url) initAudio(content.value.media_url)
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

function initAudio(src: string) {
  audioCtx = uni.createInnerAudioContext()
  audioCtx.src = src
  audioCtx.onCanplay(() => { duration.value = Math.floor(audioCtx.duration || 0) })
  audioCtx.onTimeUpdate(() => { progress.value = Math.floor(audioCtx.currentTime || 0); duration.value = Math.floor(audioCtx.duration || 0) })
  audioCtx.onEnded(() => { playing.value = false; recordProgress(100) })
  audioCtx.onError(() => { uni.showToast({ title: '播放失败', icon: 'none' }) })
}

function togglePlay() {
  if (!audioCtx) return
  if (playing.value) { audioCtx.pause() } else { audioCtx.play() }
  playing.value = !playing.value
}

function seekTo(e: any) {
  if (!audioCtx) return
  audioCtx.seek(e.detail.value)
  progress.value = e.detail.value
}

function cycleSpeed() {
  const idx = SPEEDS.indexOf(playbackRate.value)
  playbackRate.value = SPEEDS[(idx + 1) % SPEEDS.length]
  if (audioCtx) audioCtx.playbackRate = playbackRate.value
}

function forward15() {
  if (!audioCtx) return
  const t = Math.min(progress.value + 15, duration.value)
  audioCtx.seek(t)
}

function formatSec(s: number): string {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${String(sec).padStart(2, '0')}`
}

async function toggleLike() {
  try {
    await http.post(`/v1/content/${contentId.value}/like`, {})
    liked.value = !liked.value
    if (content.value) content.value.like_count += liked.value ? 1 : -1
  } catch { /* ignore */ }
}

async function toggleCollect() {
  try {
    await http.post(`/v1/content/${contentId.value}/collect`, {})
    collected.value = !collected.value
  } catch { /* ignore */ }
}

async function recordProgress(pct: number) {
  try {
    await http.post('/v1/content/user/learning-progress', {
      content_id: contentId.value, progress_pct: pct, completed: pct >= 100,
      last_position: progress.value, time_spent_seconds: progress.value,
    })
  } catch { /* ignore */ }
}

function goBack() {
  if (duration.value > 0) {
    const pct = Math.min(100, Math.round((progress.value / duration.value) * 100))
    recordProgress(pct)
  }
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.ap-page { background: var(--surface); min-height: 100vh; display: flex; flex-direction: column; }
.ap-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.ap-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ap-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.ap-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.ap-navbar__placeholder { width: 64rpx; }

.ap-content { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 40rpx 32rpx; }

.ap-cover-wrap { margin-bottom: 40rpx; }
.ap-cover { width: 400rpx; height: 400rpx; border-radius: var(--radius-xl); background: var(--bhp-gray-100); }

.ap-info { text-align: center; margin-bottom: 48rpx; }
.ap-info__title { display: block; font-size: 32rpx; font-weight: 800; color: var(--text-primary); margin-bottom: 8rpx; }
.ap-info__author { display: block; font-size: 24rpx; color: var(--text-secondary); }

.ap-controls { width: 100%; margin-bottom: 40rpx; }
.ap-progress { margin-bottom: 24rpx; }
.ap-progress__time { display: flex; justify-content: space-between; font-size: 22rpx; color: var(--text-tertiary); margin-top: -8rpx; }

.ap-btns { display: flex; align-items: center; justify-content: center; gap: 48rpx; }
.ap-btn { display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ap-btn--play {
  width: 112rpx; height: 112rpx; border-radius: 50%;
  background: var(--bhp-primary-500); font-size: 40rpx; color: #fff;
}
.ap-btn--play:active { opacity: 0.85; }
.ap-btn--speed {
  width: 80rpx; height: 80rpx; border-radius: 50%;
  background: var(--surface-secondary); font-size: 22rpx; font-weight: 700; color: var(--text-secondary);
}

.ap-actions { display: flex; gap: 48rpx; }
.ap-action { display: flex; align-items: center; gap: 8rpx; cursor: pointer; font-size: 32rpx; }
.ap-action__count { font-size: 24rpx; color: var(--text-secondary); }
</style>
