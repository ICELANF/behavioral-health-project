<template>
  <view class="msg-page">
    <!-- 顶部栏 -->
    <view class="msg-navbar">
      <view class="msg-back" @tap="goBack">←</view>
      <view class="msg-navbar-center">
        <text class="msg-title">发消息给教练</text>
        <text class="msg-subtitle" v-if="coachName">{{ coachName }}</text>
      </view>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="msg-scroll" :style="{ height: scrollH }" :scroll-into-view="scrollTarget">

      <!-- AI 起草区 -->
      <view class="msg-ai-card">
        <view class="msg-ai-header">
          <text class="msg-ai-title">🤖 AI 帮我起草</text>
          <text class="msg-ai-hint">基于你近期的健康 & 行为数据自动生成，可直接编辑</text>
        </view>
        <view class="msg-ai-btn" :class="{ 'msg-ai-btn--loading': drafting }" @tap="generateDraft">
          {{ drafting ? '分析中…' : '✨ 生成草稿' }}
        </view>
        <view v-if="draftContext.weight || draftContext.glucose || draftContext.steps" class="msg-ai-context">
          <text v-if="draftContext.weight"  class="msg-ai-ctx-item">⚖️ {{ draftContext.weight }}</text>
          <text v-if="draftContext.glucose" class="msg-ai-ctx-item">🩸 {{ draftContext.glucose }}</text>
          <text v-if="draftContext.steps"   class="msg-ai-ctx-item">👟 {{ draftContext.steps }}</text>
          <text v-if="draftContext.ttm_stage" class="msg-ai-ctx-item">🌱 行为阶段: {{ draftContext.ttm_stage }}</text>
        </view>
      </view>

      <!-- 正文输入（全页面，无闪退）-->
      <view class="msg-body-card" id="textarea-section">
        <text class="msg-body-label">消息正文</text>
        <textarea
          class="msg-textarea"
          v-model="content"
          placeholder="写下你想说的话，或使用上方 AI 草稿…"
          :auto-height="false"
          :show-confirm-bar="false"
          :adjust-position="true"
          maxlength="1000"
          @focus="onFocus"
        />
        <text class="msg-char-count">{{ content.length }} / 1000</text>
      </view>

      <!-- 附件区 -->
      <view class="msg-attach-card">
        <text class="msg-attach-title">附件（选填）</text>
        <view class="msg-attach-row">

          <!-- 拍照 / 相册 -->
          <view class="msg-attach-btn" @tap="pickImage">
            <text class="msg-attach-icon">📷</text>
            <text class="msg-attach-label">拍照/相册</text>
          </view>

          <!-- 语音输入 -->
          <view class="msg-attach-btn"
            :class="{ 'msg-attach-btn--recording': recording }"
            @touchstart="startRecord"
            @touchend="stopRecord"
            @touchcancel="cancelRecord">
            <text class="msg-attach-icon">{{ recording ? '🔴' : '🎤' }}</text>
            <text class="msg-attach-label">{{ recording ? '松开发送' : '按住说话' }}</text>
          </view>
        </view>

        <!-- 图片预览 -->
        <view v-if="images.length" class="msg-img-row">
          <view v-for="(img, i) in images" :key="i" class="msg-img-wrap">
            <image :src="img.path" class="msg-img-thumb" mode="aspectFill" />
            <view class="msg-img-del" @tap="removeImage(i)">×</view>
            <text v-if="img.desc" class="msg-img-desc">{{ img.desc }}</text>
          </view>
        </view>

        <!-- 语音记录 -->
        <view v-if="voiceList.length" class="msg-voice-row">
          <view v-for="(v, i) in voiceList" :key="i" class="msg-voice-item">
            <text class="msg-voice-icon">🎵</text>
            <text class="msg-voice-dur">{{ v.duration }}秒</text>
            <text v-if="v.text" class="msg-voice-text">「{{ v.text }}」</text>
            <view class="msg-voice-del" @tap="removeVoice(i)">×</view>
          </view>
        </view>
      </view>

      <view style="height:160rpx;"></view>
    </scroll-view>

    <!-- 底部发送栏 -->
    <view class="msg-footer">
      <view class="msg-send-btn"
        :class="{ 'msg-send-btn--disabled': !canSend, 'msg-send-btn--loading': sending }"
        @tap="send">
        {{ sending ? '发送中…' : '📤 发送给教练' }}
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const coachName = ref('')
const coachId = ref<number | null>(null)
const content = ref('')
const drafting = ref(false)
const draftContext = ref<any>({})
const images = ref<{ path: string; desc: string }[]>([])
const voiceList = ref<{ duration: number; text: string; filePath: string }[]>([])
const recording = ref(false)
const sending = ref(false)
const scrollTarget = ref('')
const scrollH = ref('60vh')

const canSend = computed(() => (content.value.trim().length > 0 || images.value.length > 0 || voiceList.value.length > 0) && !sending.value)

onMounted(async () => {
  try {
    const info = uni.getSystemInfoSync()
    const r = info.windowWidth / 750
    scrollH.value = Math.max(300, info.windowHeight - (88 + 24 + 40) * r - info.statusBarHeight - 80) + 'px'
  } catch { scrollH.value = '70vh' }
  // 读取路由参数（教练名/ID 可由 companions/index 传入）
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  const opts = page?.options || {}
  coachName.value = decodeURIComponent(opts.coach_name || '')
  coachId.value = opts.coach_id ? Number(opts.coach_id) : null

  // 若无参数，从接口补全
  if (!coachName.value) {
    try {
      const res = await http<any>('/api/v1/companions/my-coach')
      if (res?.coach) {
        coachName.value = res.coach.name || ''
        coachId.value = res.coach.id
      }
    } catch { /* silent */ }
  }
})

// ── AI 草稿 ─────────────────────────────────────────────
async function generateDraft() {
  if (drafting.value) return
  drafting.value = true
  try {
    const res = await http<any>('/api/v1/companions/ai-draft-message', { method: 'POST' })
    content.value = res.draft || ''
    draftContext.value = res.context || {}
    uni.showToast({ title: 'AI草稿已生成，可直接编辑', icon: 'none', duration: 2000 })
  } catch {
    uni.showToast({ title: '生成失败，请手动填写', icon: 'none' })
  } finally {
    drafting.value = false
  }
}

// ── 图片 ─────────────────────────────────────────────────
function pickImage() {
  uni.chooseImage({
    count: 3 - images.value.length,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success(res) {
      ;(res.tempFilePaths as string[]).forEach(path => {
        images.value.push({ path, desc: '' })
      })
      // 简单 OCR 描述：提示用户可以补充说明（无服务端 OCR 时降级）
      uni.showModal({
        title: '图片说明（选填）',
        editable: true,
        placeholderText: '简要描述图片内容，方便教练理解…',
        success(r) {
          if (r.confirm && r.content) {
            const last = images.value[images.value.length - 1]
            if (last) last.desc = r.content
          }
        },
      })
    },
  })
}

function removeImage(i: number) { images.value.splice(i, 1) }

// ── 语音 ─────────────────────────────────────────────────
let recManager: UniApp.RecorderManager | null = null
let recStartTime = 0

function getRecManager(): UniApp.RecorderManager {
  if (!recManager) {
    recManager = uni.getRecorderManager()
    recManager.onStop((res: any) => {
      recording.value = false
      const dur = Math.round((Date.now() - recStartTime) / 1000)
      if (dur < 1) { uni.showToast({ title: '录音太短', icon: 'none' }); return }
      voiceList.value.push({ duration: dur, text: '', filePath: res.tempFilePath })
      uni.showModal({
        title: '语音转文字（选填）',
        editable: true,
        placeholderText: '输入语音对应文字，方便教练阅读…',
        success(r) {
          if (r.confirm && r.content) {
            voiceList.value[voiceList.value.length - 1].text = r.content
          }
        },
      })
    })
    recManager.onError(() => { recording.value = false; uni.showToast({ title: '录音出错', icon: 'none' }) })
  }
  return recManager
}

function startRecord() {
  if (images.value.length + voiceList.value.length >= 5) {
    uni.showToast({ title: '附件已达上限', icon: 'none' }); return
  }
  const mgr = getRecManager()
  mgr.start({ duration: 60000, format: 'mp3', sampleRate: 16000, numberOfChannels: 1, encodeBitRate: 48000 })
  recording.value = true
  recStartTime = Date.now()
}

function stopRecord() {
  if (!recording.value) return
  getRecManager().stop()
}

function cancelRecord() {
  if (!recording.value) return
  getRecManager().stop()
  // 丢弃最后一条（onStop 会触发，所以延迟移除）
  setTimeout(() => { if (voiceList.value.length) voiceList.value.pop() }, 300)
}

function removeVoice(i: number) { voiceList.value.splice(i, 1) }

// ── 发送 ─────────────────────────────────────────────────
async function send() {
  if (!canSend.value) return
  const text_content = content.value.trim()
  const image_desc = images.value.map(img => img.desc || '图片').join('；') || undefined
  const voice_text = voiceList.value.filter(v => v.text).map(v => v.text).join('；') || undefined

  if (!text_content && !image_desc && !voice_text) {
    uni.showToast({ title: '请填写消息内容', icon: 'none' }); return
  }

  sending.value = true
  try {
    await http('/api/v1/companions/message-to-coach', {
      method: 'POST',
      data: {
        content: text_content || (image_desc ? `[图片消息] ${image_desc}` : '[语音消息]'),
        image_desc,
        voice_text,
      },
    })
    uni.showToast({ title: '消息已发送给教练 ✓', icon: 'success' })
    setTimeout(() => goBack(), 1500)
  } catch {
    uni.showToast({ title: '发送失败，请重试', icon: 'none' })
  } finally {
    sending.value = false
  }
}

function onFocus() { scrollTarget.value = 'textarea-section' }

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}
</script>

<style scoped>
.msg-page { min-height: 100vh; background: #F5F6FA; display: flex; flex-direction: column; }

.msg-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff;
}
.msg-back { font-size: 40rpx; padding: 16rpx; }
.msg-navbar-center { flex: 1; text-align: center; }
.msg-title { display: block; font-size: 32rpx; font-weight: 700; }
.msg-subtitle { display: block; font-size: 22rpx; opacity: 0.85; margin-top: 2rpx; }

.msg-scroll { flex: 1; min-height: 200rpx; }

/* AI 草稿卡 */
.msg-ai-card {
  margin: 24rpx; background: #fff; border-radius: 20rpx; padding: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(45,142,105,0.08);
}
.msg-ai-header { margin-bottom: 16rpx; }
.msg-ai-title { display: block; font-size: 28rpx; font-weight: 700; color: #2C3E50; }
.msg-ai-hint  { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.msg-ai-btn {
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  color: #fff; padding: 16rpx 32rpx; border-radius: 12rpx;
  font-size: 26rpx; font-weight: 600; text-align: center;
}
.msg-ai-btn--loading { opacity: 0.6; }
.msg-ai-context { margin-top: 16rpx; display: flex; flex-wrap: wrap; gap: 8rpx; }
.msg-ai-ctx-item {
  font-size: 20rpx; color: #2D8E69; background: #E8F8F0;
  padding: 4rpx 12rpx; border-radius: 8rpx;
}

/* 正文 */
.msg-body-card {
  margin: 0 24rpx 16rpx; background: #fff; border-radius: 20rpx; padding: 24rpx;
}
.msg-body-label { display: block; font-size: 24rpx; color: #8E99A4; margin-bottom: 12rpx; }
.msg-textarea {
  width: 100%; height: 240rpx; background: #F8FAFC; border-radius: 14rpx;
  padding: 20rpx; font-size: 28rpx; color: #2C3E50; box-sizing: border-box;
  border: 1rpx solid #E8EDF2; line-height: 1.6;
}
.msg-char-count { display: block; font-size: 20rpx; color: #BDC3C7; text-align: right; margin-top: 8rpx; }

/* 附件 */
.msg-attach-card {
  margin: 0 24rpx 16rpx; background: #fff; border-radius: 20rpx; padding: 24rpx;
}
.msg-attach-title { display: block; font-size: 24rpx; color: #8E99A4; margin-bottom: 16rpx; }
.msg-attach-row { display: flex; gap: 16rpx; }
.msg-attach-btn {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8rpx;
  background: #F5F6FA; border-radius: 16rpx; padding: 24rpx 16rpx;
}
.msg-attach-btn--recording { background: #FFF0F0; border: 2rpx solid #E74C3C; }
.msg-attach-icon { font-size: 48rpx; }
.msg-attach-label { font-size: 22rpx; color: #5B6B7F; }

.msg-img-row { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 20rpx; }
.msg-img-wrap { position: relative; }
.msg-img-thumb { width: 160rpx; height: 160rpx; border-radius: 12rpx; }
.msg-img-del {
  position: absolute; top: -8rpx; right: -8rpx;
  width: 36rpx; height: 36rpx; background: #E74C3C; color: #fff;
  border-radius: 50%; font-size: 24rpx; line-height: 36rpx; text-align: center;
}
.msg-img-desc { display: block; font-size: 18rpx; color: #8E99A4; max-width: 160rpx; margin-top: 4rpx; overflow: hidden; text-overflow: ellipsis; }

.msg-voice-row { margin-top: 16rpx; }
.msg-voice-item {
  display: flex; align-items: center; gap: 12rpx;
  background: #F0FFF8; border-radius: 12rpx; padding: 12rpx 16rpx; margin-bottom: 8rpx;
}
.msg-voice-icon { font-size: 28rpx; }
.msg-voice-dur { font-size: 24rpx; color: #2D8E69; font-weight: 600; white-space: nowrap; }
.msg-voice-text { flex: 1; font-size: 22rpx; color: #5B6B7F; }
.msg-voice-del { font-size: 28rpx; color: #E74C3C; padding: 0 4rpx; }

/* 底部发送栏 */
.msg-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  padding: 16rpx 24rpx; padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: #fff; border-top: 1rpx solid #F0F0F0;
}
.msg-send-btn {
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  color: #fff; text-align: center; padding: 24rpx; border-radius: 16rpx;
  font-size: 30rpx; font-weight: 700;
}
.msg-send-btn--disabled { opacity: 0.4; }
.msg-send-btn--loading { opacity: 0.7; }
</style>
