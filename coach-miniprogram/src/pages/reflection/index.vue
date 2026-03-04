<template>
  <view class="rf-page">
    <!-- Navbar -->
    <view class="rf-navbar">
      <view class="rf-nav-back" @tap="goBack">←</view>
      <text class="rf-nav-title">成长感悟</text>
      <view class="rf-nav-right"></view>
    </view>

    <scroll-view scroll-y class="rf-scroll" :style="{ height: scrollH }" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 统计 -->
      <view class="rf-stats" v-if="stats">
        <text class="rf-stat-item">已写 <text class="rf-stat-num">{{ stats.total_entries || 0 }}</text> 篇</text>
        <text class="rf-stat-sep">·</text>
        <text class="rf-stat-item">平均深度 <text class="rf-stat-num">{{ depthLabel(stats.avg_depth) }}</text></text>
      </view>

      <!-- 今日提示 -->
      <view class="rf-card">
        <text class="rf-card-title">今日写作提示</text>
        <view v-if="loadingPrompt" class="rf-loading"><text>加载中…</text></view>
        <view v-else-if="todayPrompt" class="rf-prompt-box">
          <text class="rf-prompt-text">{{ todayPrompt.content || todayPrompt.prompt_text || todayPrompt }}</text>
        </view>
        <view v-else class="rf-prompt-empty"><text>今天就自由写吧 ✍️</text></view>
        <view class="rf-prompt-btns" v-if="!showEditor">
          <view class="rf-btn rf-btn-primary" @tap="openEditor(todayPrompt)"><text>开始写</text></view>
          <view class="rf-btn rf-btn-plain" @tap="openEditor(null)"><text>自由写作</text></view>
        </view>
      </view>

      <!-- 写作区 -->
      <view class="rf-card rf-editor-card" v-if="showEditor">
        <text class="rf-card-title">写日志</text>
        <view class="rf-field-row">
          <text class="rf-field-label">标题</text>
          <input class="rf-input" v-model="form.title" placeholder="可选，今天的主题" :maxlength="50" />
        </view>
        <view class="rf-type-row">
          <text class="rf-field-label">类型</text>
          <view class="rf-type-pills">
            <view class="rf-type-pill" :class="{ active: form.journal_type === 'freeform' }" @tap="form.journal_type = 'freeform'"><text>自由写作</text></view>
            <view class="rf-type-pill" :class="{ active: form.journal_type === 'guided' }" @tap="form.journal_type = 'guided'"><text>引导式</text></view>
          </view>
        </view>
        <textarea class="rf-textarea" v-model="form.content" placeholder="写下你今天的反思、感悟或观察…" :maxlength="2000" />
        <view class="rf-word-count"><text>{{ form.content.length }}/2000</text></view>

        <!-- 多模态工具栏 -->
        <view class="rf-media-toolbar">
          <view class="rf-media-btn" @tap="pickImages"><text>📷 图片</text></view>
          <view class="rf-media-btn" :class="{ recording: isRecording }" @tap="toggleRecording">
            <text>{{ isRecording ? '⏹ 停止' : '🎙️ 录音' }}</text>
          </view>
        </view>
        <!-- 媒体预览 -->
        <view class="rf-media-preview" v-if="mediaItems.length">
          <view v-for="(m, i) in mediaItems" :key="i" class="rf-media-thumb" @tap="removeMedia(i)">
            <image v-if="m.mediaType === 'image'" :src="m.localPath" class="rf-thumb-img" mode="aspectFill" />
            <view v-else class="rf-thumb-box"><text>🎙️</text></view>
            <view class="rf-thumb-del"><text>✕</text></view>
            <view v-if="m.uploading" class="rf-thumb-uploading"><text>上传中</text></view>
          </view>
        </view>

        <!-- 公开开关 -->
        <view class="rf-public-row">
          <text class="rf-public-label">{{ form.is_public ? '🌐 公开（教练可见）' : '🔒 仅自己可见' }}</text>
          <switch :checked="form.is_public" @change="(e:any) => form.is_public = e.detail.value" color="#722ed1" style="transform:scale(0.8)" />
        </view>
        <view class="rf-editor-btns">
          <view class="rf-btn rf-btn-plain" @tap="closeEditor"><text>取消</text></view>
          <view class="rf-btn rf-btn-primary" :class="{ disabled: !form.content.trim() }" @tap="submitEntry">
            <text>{{ submitting ? '提交中…' : '提交' }}</text>
          </view>
        </view>
      </view>

      <!-- Tab 切换 -->
      <view class="rf-tabs">
        <view class="rf-tab" :class="{ active: activeTab === 'my' }" @tap="activeTab = 'my'"><text>我的日志</text></view>
        <view class="rf-tab" :class="{ active: activeTab === 'public' }" @tap="switchPublicTab"><text>精华分享</text></view>
      </view>

      <!-- 我的日志列表 -->
      <view v-if="activeTab === 'my'">
        <view v-if="loadingEntries" class="rf-loading"><text>加载中…</text></view>
        <view v-else-if="!entries.length" class="rf-empty"><text>还没有日志，写下第一篇吧</text></view>
        <template v-else>
          <view v-for="e in entries" :key="e.id" class="rf-entry-card" @tap="viewEntry(e)">
            <view class="rf-entry-header">
              <text class="rf-entry-title">{{ e.title || '无标题' }}</text>
              <view class="rf-depth-tag" :style="{ background: depthBg(e.depth_level) }"><text>{{ depthLabel(e.depth_level) }}</text></view>
              <view v-if="e.is_public" class="rf-public-tag"><text>公开</text></view>
            </view>
            <text class="rf-entry-preview">{{ (e.content || '').slice(0, 60) }}{{ (e.content?.length || 0) > 60 ? '…' : '' }}</text>
            <text class="rf-entry-date">{{ formatDate(e.created_at) }}</text>
          </view>
          <view v-if="hasMore" class="rf-load-more" @tap="loadMore"><text>{{ loadingMore ? '加载中…' : '加载更多' }}</text></view>
        </template>
      </view>

      <!-- 精华分享列表 -->
      <view v-if="activeTab === 'public'">
        <view v-if="loadingPublic" class="rf-loading"><text>加载中…</text></view>
        <view v-else-if="!publicEntries.length" class="rf-empty"><text>暂无精华分享，成为第一个分享者吧</text></view>
        <template v-else>
          <view v-for="e in publicEntries" :key="e.id" class="rf-entry-card" @tap="viewEntry(e)">
            <view class="rf-entry-header">
              <text class="rf-entry-title">{{ e.title || '无标题' }}</text>
              <view class="rf-depth-tag" :style="{ background: depthBg(e.depth_level) }"><text>{{ depthLabel(e.depth_level) }}</text></view>
            </view>
            <text v-if="e.author_name" class="rf-entry-author">{{ e.author_name }}</text>
            <text class="rf-entry-preview">{{ (e.content || '').slice(0, 80) }}{{ (e.content?.length || 0) > 80 ? '…' : '' }}</text>
            <text class="rf-entry-date">{{ formatDate(e.created_at) }}</text>
          </view>
        </template>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>

    <!-- 详情弹窗 -->
    <view class="rf-overlay" v-if="showDetail" @tap.self="showDetail = false">
      <view class="rf-sheet" @tap.stop>
        <view class="rf-sheet-header">
          <view class="rf-depth-tag" :style="{ background: depthBg(selectedEntry?.depth_level) }"><text>{{ depthLabel(selectedEntry?.depth_level) }}</text></view>
          <view @tap="showDetail = false"><text class="rf-sheet-close">✕</text></view>
        </view>
        <text class="rf-sheet-title">{{ selectedEntry?.title || '无标题' }}</text>
        <text class="rf-sheet-date">{{ formatDate(selectedEntry?.created_at) }}</text>
        <scroll-view scroll-y style="max-height: 55vh;">
          <text class="rf-sheet-body">{{ entryTextContent(selectedEntry) }}</text>
          <!-- 媒体附件 -->
          <view v-if="entryMediaUrls(selectedEntry).length" class="rf-media-display">
            <view v-for="(url, i) in entryMediaUrls(selectedEntry)" :key="i">
              <image v-if="isImageUrl(url)" :src="serverUrl(url)" class="rf-media-img" mode="widthFix" @tap="previewEntryImg(selectedEntry, url)" />
              <view v-else class="rf-media-audio-btn" @tap="playAudio(url)"><text>🎙️ 语音 {{ i + 1 }}</text></view>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const BASE_URL = 'http://localhost:8000'
const PAGE_SIZE = 10

const refreshing = ref(false)
const loadingPrompt = ref(false)
const loadingEntries = ref(false)
const loadingMore = ref(false)
const loadingPublic = ref(false)
const submitting = ref(false)
const showEditor = ref(false)
const showDetail = ref(false)
const activeTab = ref<'my' | 'public'>('my')

const todayPrompt = ref<any>(null)
const stats = ref<any>(null)
const entries = ref<any[]>([])
const publicEntries = ref<any[]>([])
const selectedEntry = ref<any>(null)
const hasMore = ref(false)
const offsetPage = ref(0)
const scrollH = ref('60vh')

interface MediaItem { mediaType: 'image' | 'audio'; localPath: string; remoteUrl?: string; uploading: boolean }
const mediaItems = ref<MediaItem[]>([])
const isRecording = ref(false)
let recorder: UniApp.RecorderManager | null = null
let audioCtx: UniApp.InnerAudioContext | null = null

const form = reactive({
  title: '',
  content: '',
  journal_type: 'freeform' as 'freeform' | 'guided',
  prompt_used: null as string | null,
  is_public: false,
})

function depthLabel(d?: string) {
  return ({ surface: '表层', pattern: '规律', insight: '洞见', identity: '身份' })[d || ''] || '表层'
}
function depthBg(d?: string) {
  return ({ surface: '#e5e7eb', pattern: '#bfdbfe', insight: '#bbf7d0', identity: '#e9d5ff' })[d || ''] || '#e5e7eb'
}
function formatDate(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function isImageUrl(url: string) { return /\.(jpg|jpeg|png|webp|gif)(\?|$)/i.test(url) }
function serverUrl(path: string) { return path.startsWith('http') ? path : BASE_URL + path }

function entryTextContent(e: any): string {
  if (!e) return ''
  const content: string = e.content || ''
  const mediaIdx = content.indexOf('\n\n[媒体附件]')
  return mediaIdx >= 0 ? content.slice(0, mediaIdx).trim() : content
}
function entryMediaUrls(e: any): string[] {
  if (!e) return []
  const content: string = e.content || ''
  const idx = content.indexOf('\n\n[媒体附件]\n')
  if (idx < 0) return []
  return content.slice(idx + '\n\n[媒体附件]\n'.length).split('\n').filter(Boolean)
}
function previewEntryImg(e: any, url: string) {
  const all = entryMediaUrls(e).filter(u => isImageUrl(u)).map(u => serverUrl(u))
  uni.previewImage({ urls: all, current: serverUrl(url) })
}
function playAudio(url: string) {
  if (audioCtx) { try { audioCtx.stop() } catch {} }
  audioCtx = uni.createInnerAudioContext()
  audioCtx.src = serverUrl(url)
  audioCtx.play()
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

function openEditor(prompt: any) {
  form.title = ''
  form.content = prompt?.content || prompt?.prompt_text || ''
  form.journal_type = prompt ? 'guided' : 'freeform'
  form.prompt_used = (prompt?.content || prompt?.prompt_text || null)
  form.is_public = false
  mediaItems.value = []
  showEditor.value = true
}

function closeEditor() {
  showEditor.value = false
  mediaItems.value = []
}

function viewEntry(e: any) { selectedEntry.value = e; showDetail.value = true }

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
    count: 3, sizeType: ['compressed'], sourceType: ['album', 'camera'],
    success: async (res) => {
      for (const path of (res.tempFilePaths as string[])) {
        const item: MediaItem = { mediaType: 'image', localPath: path, uploading: true }
        mediaItems.value.push(item)
        const idx = mediaItems.value.length - 1
        try { mediaItems.value[idx].remoteUrl = await uploadFile(path) }
        catch { uni.showToast({ title: '图片上传失败', icon: 'none' }) }
        finally { mediaItems.value[idx].uploading = false }
      }
    },
  })
}

function toggleRecording() {
  if (isRecording.value) {
    recorder?.stop()
    isRecording.value = false
    return
  }
  if (!recorder) {
    recorder = uni.getRecorderManager()
    recorder.onStop(async (res) => {
      const item: MediaItem = { mediaType: 'audio', localPath: res.tempFilePath, uploading: true }
      mediaItems.value.push(item)
      const idx = mediaItems.value.length - 1
      try { mediaItems.value[idx].remoteUrl = await uploadFile(res.tempFilePath) }
      catch { uni.showToast({ title: '语音上传失败', icon: 'none' }) }
      finally { mediaItems.value[idx].uploading = false }
    })
  }
  recorder.start({ duration: 60000, format: 'mp3' })
  isRecording.value = true
}

function removeMedia(i: number) { mediaItems.value.splice(i, 1) }

async function switchPublicTab() {
  activeTab.value = 'public'
  if (publicEntries.value.length) return
  loadingPublic.value = true
  try {
    const res: any = await http<any>('/api/v1/reflection/entries?is_public=true&limit=20')
    publicEntries.value = Array.isArray(res) ? res : (res?.entries || res?.items || [])
  } catch { publicEntries.value = [] } finally { loadingPublic.value = false }
}

async function loadData() {
  loadingPrompt.value = true
  try {
    const res: any = await http<any>('/api/v1/reflection/prompts')
    const list = Array.isArray(res) ? res : (res?.items || res?.prompts || [])
    todayPrompt.value = list.length ? list[Math.floor(Math.random() * list.length)] : null
  } catch { todayPrompt.value = null } finally { loadingPrompt.value = false }
  try { stats.value = await http<any>('/api/v1/reflection/stats') } catch { stats.value = null }
  await loadEntries(true)
}

async function loadEntries(reset = false) {
  if (reset) { offsetPage.value = 0; entries.value = [] }
  reset ? (loadingEntries.value = true) : (loadingMore.value = true)
  try {
    const res: any = await http<any>(`/api/v1/reflection/entries?offset=${offsetPage.value * PAGE_SIZE}&limit=${PAGE_SIZE}`)
    const list = Array.isArray(res) ? res : (res?.entries || res?.items || [])
    entries.value = reset ? list : [...entries.value, ...list]
    hasMore.value = list.length === PAGE_SIZE
    offsetPage.value++
  } catch {} finally { loadingEntries.value = false; loadingMore.value = false }
}

function loadMore() { loadEntries(false) }

async function submitEntry() {
  if (!form.content.trim() || submitting.value) return
  if (mediaItems.value.some(m => m.uploading)) {
    uni.showToast({ title: '媒体上传中，请稍候', icon: 'none' }); return
  }
  submitting.value = true
  try {
    // append media URLs to content
    const remoteUrls = mediaItems.value.filter(m => m.remoteUrl).map(m => m.remoteUrl as string)
    let content = form.content.trim()
    if (remoteUrls.length) content += '\n\n[媒体附件]\n' + remoteUrls.join('\n')

    await http('/api/v1/reflection/entries', {
      method: 'POST',
      data: {
        title: form.title || undefined,
        content,
        journal_type: form.journal_type,
        prompt_used: form.prompt_used || undefined,
        is_public: form.is_public,
      }
    })
    uni.showToast({ title: '日志已保存', icon: 'success' })
    closeEditor()
    await Promise.allSettled([
      loadEntries(true),
      (async () => { try { stats.value = await http<any>('/api/v1/reflection/stats') } catch {} })()
    ])
  } catch { uni.showToast({ title: '保存失败', icon: 'none' }) } finally { submitting.value = false }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

onMounted(() => {
  try {
    const info = uni.getSystemInfoSync()
    const r = info.windowWidth / 750
    const headerPx = (88 + 24) * r + info.statusBarHeight
    scrollH.value = Math.max(300, info.windowHeight - headerPx) + 'px'
  } catch { scrollH.value = '60vh' }
  loadData()
})
</script>

<style scoped>
.rf-page { min-height: 100vh; background: #F5F6FA; }
.rf-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #6d28d9 0%, #7c3aed 100%); color: #fff; }
.rf-nav-back { font-size: 40rpx; padding: 16rpx; }
.rf-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.rf-nav-right { width: 72rpx; }

.rf-stats { display: flex; align-items: center; gap: 12rpx; padding: 16rpx 24rpx; background: #f9f0ff; }
.rf-stat-item { font-size: 24rpx; color: #555; }
.rf-stat-num { color: #6d28d9; font-weight: 700; }
.rf-stat-sep { color: #ddd; }

.rf-card { margin: 16rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.rf-card-title { display: block; font-size: 30rpx; font-weight: 700; color: #2C3E50; margin-bottom: 16rpx; }
.rf-prompt-box { background: #fafafa; border-left: 6rpx solid #6d28d9; padding: 20rpx; border-radius: 8rpx; margin-bottom: 16rpx; }
.rf-prompt-text { font-size: 28rpx; color: #333; line-height: 1.6; }
.rf-prompt-empty { font-size: 26rpx; color: #999; margin-bottom: 16rpx; }
.rf-prompt-btns { display: flex; gap: 16rpx; }
.rf-loading { padding: 32rpx; text-align: center; font-size: 26rpx; color: #999; }
.rf-empty { text-align: center; padding: 60rpx; font-size: 26rpx; color: #BDC3C7; }

.rf-btn { padding: 16rpx 32rpx; border-radius: 40rpx; font-size: 26rpx; font-weight: 600; text-align: center; }
.rf-btn-primary { background: #6d28d9; color: #fff; }
.rf-btn-plain { background: #f3f4f6; color: #555; }
.rf-btn.disabled { opacity: 0.4; }

.rf-field-row { display: flex; align-items: center; gap: 16rpx; margin-bottom: 16rpx; border-bottom: 1rpx solid #f0f0f0; padding-bottom: 16rpx; }
.rf-field-label { font-size: 26rpx; color: #646566; min-width: 60rpx; }
.rf-input { flex: 1; font-size: 28rpx; color: #333; }
.rf-type-row { display: flex; align-items: center; gap: 16rpx; margin-bottom: 16rpx; }
.rf-type-pills { display: flex; gap: 12rpx; }
.rf-type-pill { padding: 8rpx 24rpx; border-radius: 20rpx; background: #f3f4f6; font-size: 24rpx; color: #666; }
.rf-type-pill.active { background: #6d28d9; color: #fff; }
.rf-textarea { width: 100%; height: 200rpx; background: #fafafa; border-radius: 12rpx; padding: 16rpx; font-size: 28rpx; color: #333; box-sizing: border-box; }
.rf-word-count { text-align: right; font-size: 22rpx; color: #bbb; margin-top: 4rpx; margin-bottom: 8rpx; }

/* Multimodal toolbar */
.rf-media-toolbar { display: flex; gap: 16rpx; padding: 16rpx 0; border-top: 1rpx solid #f0f0f0; border-bottom: 1rpx solid #f0f0f0; margin-bottom: 12rpx; }
.rf-media-btn { flex: 1; text-align: center; background: #f3f4f6; padding: 14rpx; border-radius: 8rpx; font-size: 24rpx; color: #555; }
.rf-media-btn.recording { background: #fee2e2; color: #dc2626; }

.rf-media-preview { display: flex; flex-wrap: wrap; gap: 12rpx; margin-bottom: 12rpx; }
.rf-media-thumb { position: relative; width: 120rpx; height: 120rpx; border-radius: 8rpx; overflow: hidden; }
.rf-thumb-img { width: 120rpx; height: 120rpx; }
.rf-thumb-box { width: 120rpx; height: 120rpx; display: flex; align-items: center; justify-content: center; background: #e5e7eb; }
.rf-thumb-box text { font-size: 40rpx; }
.rf-thumb-del { position: absolute; top: 2rpx; right: 2rpx; background: rgba(0,0,0,0.5); border-radius: 50%; width: 32rpx; height: 32rpx; display: flex; align-items: center; justify-content: center; }
.rf-thumb-del text { font-size: 18rpx; color: #fff; }
.rf-thumb-uploading { position: absolute; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; }
.rf-thumb-uploading text { font-size: 18rpx; color: #fff; }

.rf-public-row { display: flex; align-items: center; justify-content: space-between; padding: 16rpx 0; border-top: 1rpx solid #f0f0f0; margin-top: 8rpx; }
.rf-public-label { font-size: 26rpx; color: #555; }
.rf-editor-btns { display: flex; gap: 16rpx; justify-content: flex-end; margin-top: 16rpx; }

.rf-tabs { display: flex; margin: 16rpx 24rpx 0; background: #fff; border-radius: 12rpx 12rpx 0 0; overflow: hidden; }
.rf-tab { flex: 1; text-align: center; padding: 20rpx; font-size: 26rpx; color: #999; border-bottom: 4rpx solid transparent; }
.rf-tab.active { color: #6d28d9; border-bottom-color: #6d28d9; font-weight: 700; }

.rf-entry-card { margin: 0 24rpx; background: #fff; padding: 20rpx 24rpx; border-bottom: 1rpx solid #f5f5f5; }
.rf-entry-card:last-child { border-bottom: none; margin-bottom: 12rpx; border-radius: 0 0 16rpx 16rpx; }
.rf-entry-header { display: flex; align-items: center; gap: 12rpx; margin-bottom: 8rpx; }
.rf-entry-title { flex: 1; font-size: 28rpx; font-weight: 600; color: #2C3E50; overflow: hidden; }
.rf-depth-tag { padding: 4rpx 12rpx; border-radius: 8rpx; font-size: 20rpx; color: #333; }
.rf-public-tag { background: #f9f0ff; padding: 4rpx 12rpx; border-radius: 8rpx; font-size: 20rpx; color: #6d28d9; }
.rf-entry-author { display: block; font-size: 22rpx; color: #6d28d9; margin-bottom: 4rpx; }
.rf-entry-preview { display: block; font-size: 26rpx; color: #777; line-height: 1.5; margin-bottom: 6rpx; }
.rf-entry-date { display: block; font-size: 22rpx; color: #bbb; }
.rf-load-more { text-align: center; padding: 24rpx; font-size: 26rpx; color: #6d28d9; }

.rf-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 999; display: flex; align-items: flex-end; }
.rf-sheet { background: #fff; border-radius: 24rpx 24rpx 0 0; width: 100%; padding: 24rpx 24rpx 48rpx; box-sizing: border-box; }
.rf-sheet-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16rpx; }
.rf-sheet-close { font-size: 36rpx; color: #bbb; padding: 8rpx; }
.rf-sheet-title { display: block; font-size: 34rpx; font-weight: 700; color: #111; margin-bottom: 8rpx; }
.rf-sheet-date { display: block; font-size: 22rpx; color: #bbb; margin-bottom: 24rpx; }
.rf-sheet-body { display: block; font-size: 28rpx; color: #333; line-height: 1.8; white-space: pre-wrap; }
.rf-media-display { margin-top: 16rpx; }
.rf-media-img { width: 100%; margin-bottom: 12rpx; border-radius: 8rpx; }
.rf-media-audio-btn { background: #f9f0ff; padding: 16rpx; border-radius: 8rpx; margin-bottom: 8rpx; }
.rf-media-audio-btn text { font-size: 26rpx; color: #6d28d9; }
</style>
