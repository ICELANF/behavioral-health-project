<template>
  <view class="pub-page">
    <!-- 导航栏 -->
    <view class="pub-navbar">
      <view class="pub-back" @tap="goBack">←</view>
      <text class="pub-nav-title">分享健康之路</text>
      <view class="pub-nav-submit" :class="{ disabled: !canSubmit || submitting }" @tap="submitStory">
        <text>{{ submitting ? '发布中…' : '发布' }}</text>
      </view>
    </view>

    <scroll-view scroll-y class="pub-scroll" :style="{ height: scrollH }">
      <!-- 标题 -->
      <view class="pub-field">
        <text class="pub-label">故事标题 <text class="pub-required">*</text></text>
        <input
          class="pub-input"
          v-model="form.title"
          placeholder="用一句话概括你的故事"
          :maxlength="60"
          confirm-type="next"
        />
      </view>

      <!-- 领域 -->
      <view class="pub-field">
        <text class="pub-label">健康领域</text>
        <picker mode="selector" :range="domainOpts" range-key="label" :value="domainIdx" @change="onDomainChange">
          <view class="pub-picker">
            <text class="pub-picker-text">{{ domainOpts[domainIdx].label }}</text>
            <text class="pub-picker-arrow">▾</text>
          </view>
        </picker>
      </view>

      <!-- 挑战 -->
      <view class="pub-field">
        <text class="pub-label">遇到的挑战 <text class="pub-required">*</text></text>
        <text class="pub-hint">你面对的困难或起点是什么？</text>
        <textarea
          class="pub-ta"
          v-model="form.challenge"
          placeholder="描述你面对的困难或挑战…"
          :maxlength="500"
          :show-confirm-bar="false"
          auto-height
        />
        <text class="pub-count">{{ form.challenge.length }}/500</text>
      </view>

      <!-- 方法 -->
      <view class="pub-field">
        <text class="pub-label">我的方法 <text class="pub-required">*</text></text>
        <text class="pub-hint">你是怎么做的？有哪些具体行动？</text>
        <textarea
          class="pub-ta"
          v-model="form.approach"
          placeholder="你是如何应对的？"
          :maxlength="500"
          :show-confirm-bar="false"
          auto-height
        />
        <text class="pub-count">{{ form.approach.length }}/500</text>
      </view>

      <!-- 成果 -->
      <view class="pub-field">
        <text class="pub-label">取得的成果 <text class="pub-required">*</text></text>
        <text class="pub-hint">有哪些具体改变？数据或体感都可以。</text>
        <textarea
          class="pub-ta"
          v-model="form.outcome"
          placeholder="有哪些具体的改变？"
          :maxlength="500"
          :show-confirm-bar="false"
          auto-height
        />
        <text class="pub-count">{{ form.outcome.length }}/500</text>
      </view>

      <!-- 感悟（选填） -->
      <view class="pub-field">
        <text class="pub-label">深度感悟 <text class="pub-optional">（选填）</text></text>
        <textarea
          class="pub-ta"
          v-model="form.reflection"
          placeholder="这段经历带给你什么认识或领悟？"
          :maxlength="300"
          :show-confirm-bar="false"
          auto-height
        />
      </view>

      <!-- 图片 -->
      <view class="pub-field">
        <text class="pub-label">配图 <text class="pub-optional">（最多3张）</text></text>
        <view class="pub-img-row">
          <view v-for="(m, i) in imgItems" :key="i" class="pub-img-thumb" @tap="removeImg(i)">
            <image :src="m.localPath" class="pub-thumb-img" mode="aspectFill" />
            <view class="pub-thumb-del"><text>✕</text></view>
            <view v-if="m.uploading" class="pub-thumb-ld"><text>上传中</text></view>
          </view>
          <view v-if="imgItems.length < 3" class="pub-img-add" @tap="pickImages">
            <text class="pub-img-add-icon">📷</text>
            <text class="pub-img-add-text">添加图片</text>
          </view>
        </view>
      </view>

      <!-- 语音 -->
      <view class="pub-field">
        <text class="pub-label">语音说明 <text class="pub-optional">（选填）</text></text>
        <view v-if="audioItem" class="pub-audio-item">
          <view class="pub-audio-play" @tap="playPreview"><text>{{ isPlaying ? '⏸' : '▶' }} 试听</text></view>
          <text class="pub-audio-dur">{{ audioDuration }}</text>
          <view v-if="audioItem.uploading" class="pub-audio-ld"><text>上传中…</text></view>
          <view class="pub-audio-del" @tap="removeAudio"><text>✕</text></view>
        </view>
        <view v-else class="pub-rec-btn" :class="{ recording: isRecording }" @tap="toggleRecording">
          <text>{{ isRecording ? '⏹ 停止录音' : '🎙️ 开始录音（最长60秒）' }}</text>
        </view>
      </view>

      <!-- 匿名开关 -->
      <view class="pub-anon-row">
        <text class="pub-anon-label">{{ form.is_anonymous ? '匿名发布' : '实名发布' }}</text>
        <switch
          :checked="form.is_anonymous"
          @change="(e: any) => form.is_anonymous = e.detail.value"
          color="#6d28d9"
          style="transform: scale(0.85)"
        />
      </view>

      <!-- 底部提交（备用，导航栏也有） -->
      <view
        class="pub-submit-btn"
        :class="{ disabled: !canSubmit || submitting }"
        @tap="submitStory"
      >
        <text>{{ submitting ? '发布中…' : '发布故事' }}</text>
      </view>
      <text class="pub-submit-tip">发布后将等待审核，通常1个工作日内完成</text>

      <view style="height: 80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const BASE_URL = 'http://localhost:8000'

const DOMAINS = [
  { key: 'blood_glucose', label: '血糖管理' },
  { key: 'weight',        label: '体重控制' },
  { key: 'exercise',      label: '运动康复' },
  { key: 'diet',          label: '饮食调整' },
  { key: 'sleep',         label: '睡眠改善' },
  { key: 'stress',        label: '压力管理' },
  { key: 'medication',    label: '合理用药' },
  { key: 'mental',        label: '心态调整' },
  { key: 'general',       label: '综合健康' },
]
const domainOpts = DOMAINS
const domainIdx = ref(3)   // 默认"饮食调整"

const scrollH = ref('80vh')
const submitting = ref(false)
const isRecording = ref(false)
const isPlaying = ref(false)
const audioDuration = ref('')

interface MediaItem {
  localPath: string
  remoteUrl?: string
  uploading: boolean
}

const imgItems = ref<MediaItem[]>([])
const audioItem = ref<MediaItem | null>(null)
let recorder: UniApp.RecorderManager | null = null
let audioCtx: UniApp.InnerAudioContext | null = null
let recStartMs = 0

const form = reactive({
  title: '',
  domain: DOMAINS[3].key,
  challenge: '',
  approach: '',
  outcome: '',
  reflection: '',
  is_anonymous: false,
})

const canSubmit = computed(() =>
  form.title.trim().length >= 2 &&
  form.challenge.trim().length >= 5 &&
  form.approach.trim().length >= 5 &&
  form.outcome.trim().length >= 5 &&
  !imgItems.value.some(m => m.uploading) &&
  !(audioItem.value?.uploading)
)

function onDomainChange(e: any) {
  domainIdx.value = Number(e.detail.value)
  form.domain = domainOpts[domainIdx.value].key
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/home/index' })
}

async function uploadFile(path: string): Promise<string> {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${BASE_URL}/api/v1/upload/media`,
      filePath: path,
      name: 'file',
      header: { Authorization: `Bearer ${uni.getStorageSync('access_token')}` },
      success(res) {
        try { resolve(JSON.parse(res.data).url) } catch { reject(new Error('parse')) }
      },
      fail: reject,
    })
  })
}

async function pickImages() {
  uni.chooseImage({
    count: 3 - imgItems.value.length,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: async (res) => {
      for (const path of (res.tempFilePaths as string[])) {
        const item: MediaItem = { localPath: path, uploading: true }
        imgItems.value.push(item)
        const idx = imgItems.value.length - 1
        try { imgItems.value[idx].remoteUrl = await uploadFile(path) }
        catch { uni.showToast({ title: '图片上传失败', icon: 'none' }) }
        finally { imgItems.value[idx].uploading = false }
      }
    },
  })
}

function removeImg(i: number) { imgItems.value.splice(i, 1) }

function toggleRecording() {
  if (isRecording.value) {
    recorder?.stop()
    isRecording.value = false
    const elapsed = Math.round((Date.now() - recStartMs) / 1000)
    audioDuration.value = `${elapsed}″`
    return
  }
  if (!recorder) {
    recorder = uni.getRecorderManager()
    recorder.onStop(async (res) => {
      const item: MediaItem = { localPath: res.tempFilePath, uploading: true }
      audioItem.value = item
      try { item.remoteUrl = await uploadFile(res.tempFilePath) }
      catch { uni.showToast({ title: '语音上传失败', icon: 'none' }) }
      finally { item.uploading = false }
    })
    recorder.onError(() => {
      isRecording.value = false
      uni.showToast({ title: '录音失败，请检查权限', icon: 'none' })
    })
  }
  recorder.start({ duration: 60000, format: 'mp3' })
  recStartMs = Date.now()
  isRecording.value = true
}

function removeAudio() {
  if (audioCtx) { try { audioCtx.stop() } catch {} audioCtx = null }
  audioItem.value = null
  audioDuration.value = ''
  isPlaying.value = false
}

function playPreview() {
  if (!audioItem.value) return
  if (isPlaying.value) {
    audioCtx?.pause()
    isPlaying.value = false
    return
  }
  if (!audioCtx) audioCtx = uni.createInnerAudioContext()
  audioCtx.src = audioItem.value.localPath
  audioCtx.onEnded(() => { isPlaying.value = false })
  audioCtx.play()
  isPlaying.value = true
}

async function submitStory() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  try {
    const media_urls: string[] = [
      ...imgItems.value.filter(m => m.remoteUrl).map(m => m.remoteUrl as string),
      ...(audioItem.value?.remoteUrl ? [audioItem.value.remoteUrl] : []),
    ]
    await http('/api/v1/health-journey', {
      method: 'POST',
      data: {
        title: form.title.trim(),
        domain: form.domain,
        challenge: form.challenge.trim(),
        approach: form.approach.trim(),
        outcome: form.outcome.trim(),
        reflection: form.reflection.trim() || undefined,
        is_anonymous: form.is_anonymous,
        media_urls,
      },
    })
    uni.showToast({ title: '发布成功，等待审核', icon: 'success' })
    // 通知列表页刷新
    const pages = getCurrentPages()
    const prev = pages[pages.length - 2] as any
    if (prev && typeof prev.$vm?.loadStories === 'function') {
      prev.$vm.loadStories(true)
    }
    setTimeout(() => goBack(), 1200)
  } catch {
    uni.showToast({ title: '发布失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  try {
    const info = uni.getSystemInfoSync()
    const navH = 88 * (info.windowWidth / 750) + info.statusBarHeight
    scrollH.value = Math.max(400, info.windowHeight - navH) + 'px'
  } catch { scrollH.value = '80vh' }
})
</script>

<style scoped>
.pub-page { min-height: 100vh; background: #F5F6FA; }
.pub-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #6d28d9, #7c3aed); color: #fff;
}
.pub-back { font-size: 40rpx; padding: 16rpx; }
.pub-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.pub-nav-submit {
  background: rgba(255,255,255,0.2); padding: 10rpx 24rpx;
  border-radius: 20rpx; font-size: 28rpx; font-weight: 600;
}
.pub-nav-submit.disabled { opacity: 0.4; }

.pub-field {
  background: #fff; margin: 16rpx 24rpx 0; padding: 24rpx;
  border-radius: 16rpx; box-shadow: 0 2rpx 6rpx rgba(0,0,0,0.04);
}
.pub-label { display: block; font-size: 26rpx; font-weight: 700; color: #333; margin-bottom: 8rpx; }
.pub-required { color: #e74c3c; }
.pub-optional { font-size: 22rpx; font-weight: 400; color: #9ca3af; }
.pub-hint { display: block; font-size: 22rpx; color: #9ca3af; margin-bottom: 10rpx; }
.pub-count { display: block; text-align: right; font-size: 20rpx; color: #bbb; margin-top: 4rpx; }

.pub-input {
  width: 100%; font-size: 28rpx; color: #333; padding: 8rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}
.pub-ta {
  width: 100%; min-height: 120rpx; background: #fafafa; border-radius: 10rpx;
  padding: 16rpx; box-sizing: border-box; font-size: 28rpx; color: #333; line-height: 1.6;
}
.pub-picker { display: inline-flex; align-items: center; gap: 8rpx; background: #f9f0ff; padding: 10rpx 24rpx; border-radius: 24rpx; }
.pub-picker-text { font-size: 26rpx; color: #6d28d9; font-weight: 600; }
.pub-picker-arrow { font-size: 20rpx; color: #6d28d9; }

/* 图片 */
.pub-img-row { display: flex; flex-wrap: wrap; gap: 16rpx; margin-top: 12rpx; }
.pub-img-thumb { position: relative; width: 140rpx; height: 140rpx; border-radius: 8rpx; overflow: hidden; }
.pub-thumb-img { width: 140rpx; height: 140rpx; }
.pub-thumb-del {
  position: absolute; top: 4rpx; right: 4rpx;
  background: rgba(0,0,0,0.5); border-radius: 50%;
  width: 36rpx; height: 36rpx; display: flex; align-items: center; justify-content: center;
}
.pub-thumb-del text { font-size: 20rpx; color: #fff; }
.pub-thumb-ld {
  position: absolute; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
}
.pub-thumb-ld text { font-size: 20rpx; color: #fff; }
.pub-img-add {
  width: 140rpx; height: 140rpx; border-radius: 8rpx; border: 2rpx dashed #d1d5db;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8rpx;
}
.pub-img-add-icon { font-size: 40rpx; }
.pub-img-add-text { font-size: 20rpx; color: #9ca3af; }

/* 语音 */
.pub-audio-item {
  display: flex; align-items: center; gap: 16rpx; margin-top: 12rpx;
  background: #f9f0ff; padding: 16rpx; border-radius: 10rpx;
}
.pub-audio-play { background: #6d28d9; color: #fff; padding: 8rpx 20rpx; border-radius: 20rpx; font-size: 26rpx; }
.pub-audio-dur { font-size: 26rpx; color: #6d28d9; flex: 1; }
.pub-audio-ld { font-size: 22rpx; color: #9ca3af; }
.pub-audio-del { font-size: 30rpx; color: #bbb; padding: 8rpx; }
.pub-rec-btn {
  display: flex; align-items: center; justify-content: center;
  margin-top: 12rpx; padding: 24rpx; border-radius: 10rpx;
  background: #f3f4f6; font-size: 28rpx; color: #555;
}
.pub-rec-btn.recording { background: #fee2e2; color: #dc2626; }

/* 匿名 */
.pub-anon-row {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; margin: 16rpx 24rpx 0; padding: 24rpx;
  border-radius: 16rpx;
}
.pub-anon-label { font-size: 28rpx; color: #555; }

/* 提交 */
.pub-submit-btn {
  margin: 24rpx 24rpx 0; background: #6d28d9; color: #fff;
  text-align: center; padding: 28rpx; border-radius: 16rpx;
  font-size: 30rpx; font-weight: 700;
}
.pub-submit-btn.disabled { opacity: 0.4; }
.pub-submit-tip { display: block; text-align: center; font-size: 22rpx; color: #9ca3af; margin-top: 12rpx; }
</style>
