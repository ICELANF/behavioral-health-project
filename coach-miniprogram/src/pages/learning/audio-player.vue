<template>
  <view class="ap-page">
    <!-- 封面 -->
    <view class="ap-cover-wrap">
      <image v-if="cover" :src="cover" class="ap-cover" mode="aspectFill" />
      <view v-else class="ap-cover ap-cover--ph">
        <text class="ap-cover-icon">🎧</text>
      </view>
    </view>

    <view class="ap-content">
      <text class="ap-title">{{ title }}</text>
      <text class="ap-author">{{ author || '官方内容' }}</text>

      <!-- 进度条 -->
      <view class="ap-progress-wrap">
        <text class="ap-time">{{ formatTime(currentTime) }}</text>
        <view class="ap-progress-bar">
          <view class="ap-progress-fill" :style="{ width: progressPct + '%' }" />
        </view>
        <text class="ap-time">{{ formatTime(duration) }}</text>
      </view>

      <!-- 控制 -->
      <view class="ap-controls">
        <view class="ap-ctrl-btn ap-ctrl-prev" @tap="seekBack">
          <text>⏮ 15s</text>
        </view>
        <view class="ap-play-btn" @tap="togglePlay">
          <text class="ap-play-icon">{{ playing ? '⏸' : '▶' }}</text>
        </view>
        <view class="ap-ctrl-btn ap-ctrl-next" @tap="seekForward">
          <text>15s ⏭</text>
        </view>
      </view>

      <view v-if="!audioUrl" class="ap-no-audio">
        <text>音频文件暂不可用</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { httpReq as http } from '@/api/request'

const audioUrl = ref('')
const title = ref('音频学习')
const author = ref('')
const cover = ref('')
const playing = ref(false)
const currentTime = ref(0)
const duration = ref(0)

const progressPct = computed(() => duration.value > 0 ? currentTime.value / duration.value * 100 : 0)

let audioCtx: any = null

function formatTime(s: number): string {
  const m = Math.floor(s / 60), sec = Math.floor(s % 60)
  return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
}

function togglePlay() {
  if (!audioCtx || !audioUrl.value) return
  if (playing.value) { audioCtx.pause(); playing.value = false }
  else { audioCtx.play(); playing.value = true }
}

function seekBack() {
  if (audioCtx) { audioCtx.seek(Math.max(0, currentTime.value - 15)) }
}
function seekForward() {
  if (audioCtx) { audioCtx.seek(Math.min(duration.value, currentTime.value + 15)) }
}

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  const id = Number(page?.options?.id || 0)
  if (id) {
    try {
      const data = await http<any>(`/api/v1/content/${id}`)
      audioUrl.value = data?.media_url || ''
      title.value = data?.title || '音频学习'
      author.value = data?.author?.name || ''
      cover.value = data?.cover_url || ''
    } catch {}
  }

  if (audioUrl.value) {
    audioCtx = uni.createInnerAudioContext()
    audioCtx.src = audioUrl.value
    audioCtx.onTimeUpdate(() => { currentTime.value = audioCtx.currentTime })
    audioCtx.onCanplay(() => { duration.value = audioCtx.duration })
    audioCtx.onEnded(() => { playing.value = false })
  }
})

onUnmounted(() => { if (audioCtx) { audioCtx.stop(); audioCtx.destroy() } })
</script>

<style scoped>
.ap-page { min-height: 100vh; background: linear-gradient(180deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%); display: flex; flex-direction: column; }
.ap-cover-wrap { width: 100%; padding: 60rpx 80rpx 40rpx; box-sizing: border-box; }
.ap-cover { width: 100%; height: 400rpx; border-radius: 24rpx; display: block; }
.ap-cover--ph { display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.1); }
.ap-cover-icon { font-size: 120rpx; }
.ap-content { flex: 1; padding: 32rpx 48rpx; color: #fff; }
.ap-title { display: block; font-size: 36rpx; font-weight: 700; margin-bottom: 8rpx; }
.ap-author { display: block; font-size: 24rpx; opacity: 0.7; margin-bottom: 48rpx; }
.ap-progress-wrap { display: flex; align-items: center; gap: 16rpx; margin-bottom: 48rpx; }
.ap-time { font-size: 22rpx; opacity: 0.7; white-space: nowrap; }
.ap-progress-bar { flex: 1; height: 6rpx; background: rgba(255,255,255,0.2); border-radius: 3rpx; }
.ap-progress-fill { height: 100%; background: #fff; border-radius: 3rpx; min-width: 6rpx; }
.ap-controls { display: flex; align-items: center; justify-content: center; gap: 48rpx; margin-bottom: 32rpx; }
.ap-ctrl-btn { font-size: 24rpx; opacity: 0.7; padding: 16rpx; }
.ap-play-btn { width: 120rpx; height: 120rpx; border-radius: 50%; background: rgba(255,255,255,0.15); display: flex; align-items: center; justify-content: center; }
.ap-play-icon { font-size: 48rpx; }
.ap-no-audio { text-align: center; font-size: 24rpx; opacity: 0.5; margin-top: 32rpx; }
</style>
