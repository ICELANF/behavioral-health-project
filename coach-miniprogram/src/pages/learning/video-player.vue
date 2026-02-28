<template>
  <view class="vp-page">

    <!-- 自定义导航栏 -->
    <view class="vp-navbar safe-area-top">
      <view class="vp-navbar__back" @tap="goBack">
        <text class="vp-navbar__arrow">‹</text>
      </view>
      <text class="vp-navbar__title">{{ content?.title || '视频学习' }}</text>
      <view class="vp-navbar__placeholder"></view>
    </view>

    <!-- 视频播放器 -->
    <view class="vp-player">
      <video
        id="bhp-video"
        class="vp-video"
        :src="content?.video_url || ''"
        :title="content?.title || ''"
        :poster="content?.cover_url || ''"
        :autoplay="false"
        :show-progress="true"
        :show-fullscreen-btn="true"
        :show-play-btn="true"
        :enable-progress-gesture="true"
        object-fit="contain"
        @play="onPlay"
        @pause="onPause"
        @timeupdate="onTimeUpdate"
        @ended="onEnded"
        @error="onError"
      />
    </view>

    <!-- 视频信息 -->
    <view class="vp-info">
      <text class="vp-info__title">{{ content?.title || '' }}</text>
      <view class="vp-info__meta">
        <text class="vp-info__meta-item">{{ content?.estimated_minutes || 0 }}分钟</text>
        <text class="vp-info__meta-sep">·</text>
        <text class="vp-info__meta-item">{{ content?.view_count || 0 }}次播放</text>
        <text class="vp-info__meta-sep">·</text>
        <text class="vp-info__meta-item text-primary-color">+{{ content?.points || 10 }}积分</text>
      </view>
      <text class="vp-info__desc" v-if="content?.description">{{ content.description }}</text>
    </view>

    <!-- 互动栏 -->
    <view class="vp-actions">
      <view class="vp-action" @tap="toggleLike">
        <text class="vp-action__icon">{{ liked ? '❤️' : '🤍' }}</text>
        <text class="vp-action__label">{{ liked ? '已赞' : '点赞' }}</text>
      </view>
      <view class="vp-action" @tap="toggleFavorite">
        <text class="vp-action__icon">{{ favorited ? '⭐' : '☆' }}</text>
        <text class="vp-action__label">{{ favorited ? '已收藏' : '收藏' }}</text>
      </view>
      <view class="vp-action" @tap="goComment">
        <text class="vp-action__icon">💬</text>
        <text class="vp-action__label">评论</text>
      </view>
      <view class="vp-action" @tap="handleShare">
        <text class="vp-action__icon">📤</text>
        <text class="vp-action__label">分享</text>
      </view>
    </view>

    <!-- 断点续播弹窗 -->
    <view class="vp-modal-mask" v-if="showResumeModal" @tap="dismissResume">
      <view class="vp-modal" @tap.stop>
        <text class="vp-modal__title">继续播放</text>
        <text class="vp-modal__desc">上次观看到 {{ formatTime(savedPosition) }}，是否继续？</text>
        <view class="vp-modal__btns">
          <view class="vp-modal__btn vp-modal__btn--secondary" @tap="dismissResume">
            <text>从头播放</text>
          </view>
          <view class="vp-modal__btn vp-modal__btn--primary" @tap="resumePlay">
            <text>继续播放</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 测验提示弹窗 -->
    <view class="vp-modal-mask" v-if="showQuizModal">
      <view class="vp-modal" @tap.stop>
        <text class="vp-modal__title">随堂测验</text>
        <text class="vp-modal__desc">视频学习完成！本内容包含随堂测验，完成可获得额外积分。</text>
        <view class="vp-modal__btns">
          <view class="vp-modal__btn vp-modal__btn--secondary" @tap="showQuizModal = false">
            <text>稍后再说</text>
          </view>
          <view class="vp-modal__btn vp-modal__btn--primary" @tap="goQuiz">
            <text>开始测验</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { onLoad, onHide, onShareAppMessage } from '@dcloudio/uni-app'
import { ref, onMounted, onUnmounted } from 'vue'
import { useLearningStore } from '@/stores/learning'
import http from '@/api/request'

const learningStore = useLearningStore()

// ── 状态 ─────────────────────────────────────────────
const content        = ref<any>(null)
const contentId      = ref(0)
const liked          = ref(false)
const favorited      = ref(false)
const showResumeModal = ref(false)
const showQuizModal  = ref(false)
const savedPosition  = ref(0)

let videoCtx: UniApp.VideoContext | null = null
let heartbeatTimer: ReturnType<typeof setInterval> | null = null
let currentPosition  = 0
let duration         = 0
let isPlaying        = false
let hasCompleted     = false

// ── 生命周期 ──────────────────────────────────────────
onLoad((query: any) => {
  contentId.value = Number(query?.id || query?.content_id || 0)
})

onMounted(async () => {
  videoCtx = uni.createVideoContext('bhp-video')
  if (contentId.value) {
    await loadContent()
    await checkResume()
  }
})

onHide(() => {
  saveProgress()
  stopHeartbeat()
})

onUnmounted(() => {
  saveProgress()
  stopHeartbeat()
})

// ── 加载内容 ──────────────────────────────────────────
async function loadContent() {
  try {
    const res = await http.get<any>(`/v1/content/${contentId.value}`)
    content.value = res
    liked.value = !!res.user_liked
    favorited.value = !!res.user_favorited
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

// ── 断点续播 ──────────────────────────────────────────
async function checkResume() {
  try {
    const res = await http.get<{ last_position?: number; progress_pct?: number }>(
      `/v1/content/${contentId.value}/progress`
    )
    const pos = res?.last_position || 0
    if (pos > 10) {
      savedPosition.value = pos
      showResumeModal.value = true
    }
  } catch {
    // 无历史记录，从头播放
  }
}

function resumePlay() {
  showResumeModal.value = false
  if (videoCtx && savedPosition.value > 0) {
    videoCtx.seek(savedPosition.value)
    videoCtx.play()
  }
}

function dismissResume() {
  showResumeModal.value = false
}

// ── 播放事件 ──────────────────────────────────────────
function onPlay() {
  isPlaying = true
  startHeartbeat()
}

function onPause() {
  isPlaying = false
  saveProgress()
  stopHeartbeat()
}

function onTimeUpdate(e: any) {
  currentPosition = e.detail?.currentTime || 0
  duration = e.detail?.duration || 0
}

function onEnded() {
  isPlaying = false
  stopHeartbeat()
  currentPosition = duration
  saveProgress()
  checkCompletion()
}

function onError() {
  isPlaying = false
  stopHeartbeat()
  uni.showToast({ title: '视频加载失败', icon: 'none' })
}

// ── 30秒心跳 ─────────────────────────────────────────
function startHeartbeat() {
  stopHeartbeat()
  heartbeatTimer = setInterval(() => {
    if (isPlaying) saveProgress()
  }, 30_000)
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

// ── 保存进度 ──────────────────────────────────────────
function saveProgress() {
  if (!contentId.value || duration <= 0) return
  const pct = Math.min(Math.round((currentPosition / duration) * 100), 100)
  learningStore.recordProgress(contentId.value, {
    progress_pct: pct,
    last_position: Math.round(currentPosition),
    time_spent_seconds: Math.round(currentPosition),
  })
}

// ── 完成检测 ──────────────────────────────────────────
function checkCompletion() {
  if (hasCompleted) return
  const pct = duration > 0 ? (currentPosition / duration) * 100 : 0
  if (pct >= 90) {
    hasCompleted = true
    learningStore.recordProgress(contentId.value, {
      progress_pct: 100,
      completed: true,
      last_position: Math.round(currentPosition),
    })
    const pts = content.value?.points || 10
    uni.showToast({ title: `+${pts} 成长积分`, icon: 'none', duration: 2000 })

    if (content.value?.has_quiz) {
      setTimeout(() => { showQuizModal.value = true }, 2200)
    }
  }
}

// ── 互动 ─────────────────────────────────────────────
async function toggleLike() {
  try {
    if (liked.value) {
      await http.post(`/v1/content/${contentId.value}/unlike`, {})
    } else {
      await http.post(`/v1/content/${contentId.value}/like`, {})
    }
    liked.value = !liked.value
  } catch {/* ignore */}
}

async function toggleFavorite() {
  try {
    if (favorited.value) {
      await http.post(`/v1/content/${contentId.value}/unfavorite`, {})
    } else {
      await http.post(`/v1/content/${contentId.value}/favorite`, {})
    }
    favorited.value = !favorited.value
  } catch {/* ignore */}
}

function goComment() {
  uni.navigateTo({ url: `/pages/learning/content-detail?id=${contentId.value}&tab=comment` })
}

function handleShare() {
  uni.showToast({ title: '请点击右上角分享', icon: 'none' })
}

onShareAppMessage(() => ({
  title: content.value?.title || '推荐视频',
  path: `/pages/learning/video-player?content_id=${contentId.value}`,
}))

// ── 导航 ─────────────────────────────────────────────
function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}

function goQuiz() {
  showQuizModal.value = false
  uni.navigateTo({ url: `/pages/learning/quiz?content_id=${contentId.value}` })
}

// ── 工具 ─────────────────────────────────────────────
function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
</script>

<style scoped>
.vp-page { background: #000; min-height: 100vh; display: flex; flex-direction: column; }

/* 导航栏 */
.vp-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: rgba(0,0,0,0.6); position: relative; z-index: 10;
}
.vp-navbar__back {
  width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
.vp-navbar__arrow { font-size: 48rpx; color: #fff; font-weight: 300; }
.vp-navbar__title { font-size: 28rpx; color: #fff; font-weight: 600; max-width: 60%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vp-navbar__placeholder { width: 64rpx; }

/* 播放器 */
.vp-player { width: 100%; background: #000; }
.vp-video { width: 100%; height: 422rpx; }

/* 内容信息 */
.vp-info { padding: 28rpx 32rpx; background: var(--surface); }
.vp-info__title { font-size: 32rpx; font-weight: 700; color: var(--text-primary); display: block; line-height: 1.4; }
.vp-info__meta { display: flex; align-items: center; gap: 8rpx; margin-top: 12rpx; }
.vp-info__meta-item { font-size: 24rpx; color: var(--text-secondary); }
.vp-info__meta-sep { font-size: 24rpx; color: var(--text-tertiary); }
.vp-info__desc { font-size: 26rpx; color: var(--text-secondary); margin-top: 16rpx; display: block; line-height: 1.6; }

/* 互动栏 */
.vp-actions {
  display: flex; justify-content: space-around; align-items: center;
  padding: 24rpx 32rpx; background: var(--surface);
  border-top: 1px solid var(--border-light);
}
.vp-action { display: flex; flex-direction: column; align-items: center; gap: 6rpx; cursor: pointer; }
.vp-action:active { opacity: 0.7; }
.vp-action__icon { font-size: 40rpx; }
.vp-action__label { font-size: 22rpx; color: var(--text-secondary); }

/* 弹窗 */
.vp-modal-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
  z-index: 999;
}
.vp-modal {
  width: 560rpx; background: var(--surface); border-radius: var(--radius-xl);
  padding: 48rpx 40rpx 36rpx; display: flex; flex-direction: column; gap: 20rpx;
}
.vp-modal__title { font-size: 32rpx; font-weight: 700; color: var(--text-primary); text-align: center; }
.vp-modal__desc { font-size: 26rpx; color: var(--text-secondary); text-align: center; line-height: 1.5; }
.vp-modal__btns { display: flex; gap: 20rpx; margin-top: 12rpx; }
.vp-modal__btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
}
.vp-modal__btn:active { opacity: 0.8; }
.vp-modal__btn--primary { background: var(--bhp-primary-500); color: #fff; }
.vp-modal__btn--secondary { background: var(--bhp-gray-100); color: var(--text-secondary); }
</style>
