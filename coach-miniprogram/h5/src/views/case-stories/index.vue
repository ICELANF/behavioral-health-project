<template>
  <view class="hj-page">
    <!-- Navbar -->
    <view class="hj-navbar">
      <view class="hj-nav-back" @tap="goBack">←</view>
      <text class="hj-nav-title">健康之路</text>
      <view class="hj-nav-pub" @tap="goPublish"><text>发布</text></view>
    </view>

    <!-- 领域筛选（picker dropdown）-->
    <view class="hj-filter-bar">
      <picker mode="selector" :range="domainOptions" range-key="label" :value="domainIdx" @change="onDomainChange">
        <view class="hj-domain-picker">
          <text class="hj-domain-picker-text">{{ domainOptions[domainIdx].label }}</text>
          <text class="hj-domain-picker-arrow">▾</text>
        </view>
      </picker>
    </view>

    <!-- 故事列表 -->
    <scroll-view
      scroll-y class="hj-scroll" :style="{ height: scrollH }"
      refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing"
    >
      <view v-if="loading" class="hj-center"><text class="hj-muted">加载中…</text></view>
      <view v-else-if="!stories.length" class="hj-center"><text class="hj-muted">暂无故事，成为第一个分享者吧 ✨</text></view>
      <template v-else>
        <view v-for="s in stories" :key="s.id" class="hj-card" @tap="viewStory(s)">
          <view class="hj-card-row1">
            <view class="hj-badge"><text>{{ s.domain_label || domainLabel(s.domain) }}</text></view>
            <text class="hj-card-author">{{ s.author_name || '成长者' }}</text>
            <text class="hj-card-date">{{ formatDate(s.created_at) }}</text>
          </view>
          <text class="hj-card-title">{{ s.title }}</text>
          <text class="hj-card-preview">{{ s.preview || (s.body || '').slice(0, 80) }}</text>
          <view class="hj-card-row2">
            <text class="hj-card-stat">👍 {{ s.like_count || 0 }}</text>
            <text class="hj-card-stat">❤️ {{ s.collect_count || 0 }}</text>
            <text class="hj-card-stat">👁 {{ s.view_count || 0 }}</text>
          </view>
        </view>
        <view v-if="hasMore" class="hj-load-more" @tap="loadMore">
          <text>{{ loadingMore ? '加载中…' : '加载更多' }}</text>
        </view>
      </template>
      <view style="height:120rpx;"></view>
    </scroll-view>

    <!-- 详情弹窗 -->
    <view class="hj-overlay" v-if="showDetail" @tap.self="showDetail = false">
      <view class="hj-sheet" @tap.stop>
        <view class="hj-sheet-head">
          <view class="hj-badge"><text>{{ selectedStory?.domain_label || domainLabel(selectedStory?.domain) }}</text></view>
          <view class="hj-sheet-actions">
            <view class="hj-share-btn" @tap="shareStory"><text>分享</text></view>
            <view @tap="showDetail = false"><text class="hj-close">✕</text></view>
          </view>
        </view>
        <text class="hj-sheet-title">{{ selectedStory?.title }}</text>
        <text class="hj-sheet-meta">{{ selectedStory?.author_name || '成长者' }} · {{ formatDate(selectedStory?.created_at) }}</text>
        <scroll-view scroll-y style="max-height: 50vh;">
          <view v-for="sec in detailSections" :key="sec.key">
            <text v-if="extractSection(selectedStory, sec.key)" class="hj-sec-label">{{ sec.label }}</text>
            <text v-if="extractSection(selectedStory, sec.key)" class="hj-sec-body">{{ extractSection(selectedStory, sec.key) }}</text>
          </view>
          <!-- 媒体 -->
          <view v-if="detailMediaList.length" class="hj-media-display">
            <view v-for="(url, i) in detailMediaList" :key="i">
              <image v-if="isImageUrl(url)" :src="serverUrl(url)" class="hj-media-img" mode="widthFix" @tap="previewImg(url)" />
              <video v-else-if="isVideoUrl(url)" :src="serverUrl(url)" class="hj-media-video" controls />
              <view v-else class="hj-media-audio" @tap="playAudio(url)"><text>🎙️ 语音 {{ i + 1 }}</text></view>
            </view>
          </view>
        </scroll-view>
        <view class="hj-like-row">
          <view class="hj-like-btn" @tap="toggleLike">
            <text>{{ selectedStory?.liked ? '❤️' : '🤍' }} {{ selectedStory?.like_count || 0 }}</text>
          </view>
          <view class="hj-helpful-btn" @tap="toggleHelpful">
            <text>{{ selectedStory?.helped ? '⭐' : '☆' }} 有帮助 {{ selectedStory?.collect_count || 0 }}</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const BASE_URL = 'http://localhost:8000'
const PAGE_SIZE = 10

const DOMAINS = [
  { key: '', label: '全部' },
  { key: 'blood_glucose', label: '血糖管理' },
  { key: 'weight', label: '体重控制' },
  { key: 'exercise', label: '运动康复' },
  { key: 'diet', label: '饮食调整' },
  { key: 'sleep', label: '睡眠改善' },
  { key: 'stress', label: '压力管理' },
  { key: 'medication', label: '合理用药' },
  { key: 'mental', label: '心态调整' },
  { key: 'general', label: '综合健康' },
]
const domainOptions = DOMAINS

const detailSections = [
  { key: 'challenge', label: '遇到的挑战' },
  { key: 'approach', label: '我的方法' },
  { key: 'outcome', label: '取得的成果' },
  { key: 'reflection', label: '深度感悟' },
]

function domainLabel(key?: string) {
  return DOMAINS.find(d => d.key === key)?.label || key || '综合健康'
}
function formatDate(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function isImageUrl(url: string) { return /\.(jpg|jpeg|png|webp|gif)(\?|$)/i.test(url) }
function isVideoUrl(url: string) { return /\.(mp4|mov|mpg)(\?|$)/i.test(url) }
function serverUrl(path: string) { return path.startsWith('http') ? path : BASE_URL + path }

function extractSection(s: any, key: string): string {
  if (!s) return ''
  const body: string = s.body || s.content || ''
  const markers: Record<string, string[]> = {
    challenge: ['**挑战：**', '**遇到的挑战：**'],
    approach: ['**方法：**', '**我的方法：**'],
    outcome: ['**成果：**', '**取得的成果：**'],
    reflection: ['**感悟：**', '**深度感悟：**', '**反思：**'],
  }
  for (const marker of (markers[key] || [])) {
    const idx = body.indexOf(marker)
    if (idx >= 0) {
      const after = body.slice(idx + marker.length).trimStart()
      const nextMatch = after.search(/\*\*[^*]+：\*\*/)
      return nextMatch > 0 ? after.slice(0, nextMatch).trim() : after.split('\n\n**')[0].trim()
    }
  }
  return ''
}

const detailMediaList = computed<string[]>(() => {
  if (!selectedStory.value) return []
  const body: string = selectedStory.value.body || selectedStory.value.content || ''
  const idx = body.indexOf('**媒体：**')
  if (idx < 0) return []
  return body.slice(idx + 6).trim().split('\n').filter(Boolean)
})

const scrollH = ref('65vh')
const refreshing = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const showDetail = ref(false)
const stories = ref<any[]>([])
const selectedStory = ref<any>(null)
const hasMore = ref(false)
const page = ref(1)
const domainIdx = ref(0)
let audioCtx: UniApp.InnerAudioContext | null = null

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/home/index' })
}
function onDomainChange(e: any) {
  domainIdx.value = Number(e.detail.value)
  loadStories(true)
}
function viewStory(s: any) { selectedStory.value = s; showDetail.value = true }
function goPublish() {
  uni.navigateTo({ url: '/case-stories/publish' })
}
function shareStory() {
  uni.showShareMenu({ withShareTicket: true, menus: ['shareAppMessage'] })
}
function previewImg(url: string) {
  const all = detailMediaList.value.filter(u => isImageUrl(u)).map(u => serverUrl(u))
  uni.previewImage({ urls: all, current: serverUrl(url) })
}
function playAudio(url: string) {
  if (audioCtx) { try { audioCtx.stop() } catch {} }
  audioCtx = uni.createInnerAudioContext()
  audioCtx.src = serverUrl(url)
  audioCtx.play()
}

async function toggleLike() {
  if (!selectedStory.value) return
  try {
    const res: any = await http(`/api/v1/health-journey/${selectedStory.value.id}/like`, { method: 'POST' })
    selectedStory.value.like_count = res.like_count
    selectedStory.value.liked = res.liked
    const s = stories.value.find((x: any) => x.id === selectedStory.value?.id)
    if (s) s.like_count = res.like_count
  } catch {}
}

async function toggleHelpful() {
  if (!selectedStory.value) return
  try {
    const res: any = await http(`/api/v1/health-journey/${selectedStory.value.id}/helpful`, { method: 'POST' })
    selectedStory.value.collect_count = res.helpful_count
    selectedStory.value.helped = res.marked
    const s = stories.value.find((x: any) => x.id === selectedStory.value?.id)
    if (s) s.collect_count = res.helpful_count
  } catch {}
}

async function loadStories(reset = false) {
  if (reset) { page.value = 1; stories.value = [] }
  reset ? (loading.value = true) : (loadingMore.value = true)
  try {
    const domain = domainOptions[domainIdx.value].key
    let url = `/api/v1/health-journey?page=${page.value}&page_size=${PAGE_SIZE}`
    if (domain) url += `&domain=${domain}`
    const res: any = await http<any>(url)
    const list: any[] = Array.isArray(res) ? res : (res?.items || [])
    stories.value = reset ? list : [...stories.value, ...list]
    hasMore.value = list.length === PAGE_SIZE
    page.value++
  } catch {} finally { loading.value = false; loadingMore.value = false }
}

function loadMore() { loadStories(false) }
async function onRefresh() { refreshing.value = true; await loadStories(true); refreshing.value = false }

onMounted(() => {
  try {
    const info = uni.getSystemInfoSync()
    const r = info.windowWidth / 750
    const top = (88 + 44) * r + info.statusBarHeight
    scrollH.value = Math.max(300, info.windowHeight - top) + 'px'
  } catch { scrollH.value = '65vh' }
  loadStories(true)
})
</script>

<style scoped>
.hj-page { min-height: 100vh; background: #F5F6FA; }
.hj-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #6d28d9 0%, #7c3aed 100%); color: #fff;
}
.hj-nav-back { font-size: 40rpx; padding: 16rpx; }
.hj-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.hj-nav-pub { background: rgba(255,255,255,0.2); padding: 8rpx 20rpx; border-radius: 8rpx; font-size: 26rpx; }

.hj-filter-bar {
  display: flex; align-items: center;
  background: #fff; padding: 12rpx 24rpx; border-bottom: 1rpx solid #f0f0f0;
}
.hj-domain-picker {
  display: inline-flex; align-items: center; gap: 8rpx;
  background: #f9f0ff; padding: 10rpx 24rpx; border-radius: 32rpx;
}
.hj-domain-picker-text { font-size: 26rpx; color: #6d28d9; font-weight: 600; }
.hj-domain-picker-arrow { font-size: 20rpx; color: #6d28d9; }

.hj-center { text-align: center; padding: 80rpx 32rpx; }
.hj-muted { font-size: 26rpx; color: #BDC3C7; }

.hj-card {
  background: #fff; margin: 16rpx 24rpx 0; padding: 24rpx;
  border-radius: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04);
}
.hj-card-row1 { display: flex; align-items: center; gap: 12rpx; margin-bottom: 10rpx; }
.hj-badge { background: #f9f0ff; padding: 4rpx 16rpx; border-radius: 8rpx; }
.hj-badge text { font-size: 22rpx; color: #6d28d9; font-weight: 600; }
.hj-card-author { font-size: 22rpx; color: #9ca3af; flex: 1; }
.hj-card-date { font-size: 20rpx; color: #bbb; }
.hj-card-title { display: block; font-size: 30rpx; font-weight: 700; color: #111; margin-bottom: 8rpx; }
.hj-card-preview { display: block; font-size: 26rpx; color: #666; line-height: 1.5; margin-bottom: 10rpx; }
.hj-card-row2 { display: flex; gap: 24rpx; }
.hj-card-stat { font-size: 22rpx; color: #9ca3af; }
.hj-load-more { text-align: center; padding: 24rpx; font-size: 26rpx; color: #6d28d9; }

/* Overlay & Sheet */
.hj-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 999; display: flex; align-items: flex-end; }
.hj-sheet { background: #fff; border-radius: 24rpx 24rpx 0 0; width: 100%; padding: 24rpx; box-sizing: border-box; }
.hj-publish-sheet { max-height: 92vh; }
.hj-sheet-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16rpx; }
.hj-sheet-actions { display: flex; align-items: center; gap: 16rpx; }
.hj-share-btn { background: #f3f4f6; padding: 8rpx 20rpx; border-radius: 8rpx; font-size: 24rpx; color: #555; }
.hj-close { font-size: 36rpx; color: #bbb; padding: 8rpx; }
.hj-pub-title { font-size: 32rpx; font-weight: 700; color: #111; }
.hj-sheet-title { display: block; font-size: 32rpx; font-weight: 700; color: #111; margin-bottom: 6rpx; }
.hj-sheet-meta { display: block; font-size: 22rpx; color: #bbb; margin-bottom: 20rpx; }
.hj-sec-label { display: block; font-size: 22rpx; font-weight: 700; color: #6d28d9; margin: 16rpx 0 6rpx; }
.hj-sec-body { display: block; font-size: 28rpx; color: #333; line-height: 1.7; white-space: pre-wrap; margin-bottom: 8rpx; }
.hj-media-display { margin-top: 16rpx; }
.hj-media-img { width: 100%; margin-bottom: 12rpx; border-radius: 8rpx; }
.hj-media-video { width: 100%; height: 320rpx; margin-bottom: 12rpx; border-radius: 8rpx; }
.hj-media-audio { background: #f9f0ff; padding: 16rpx; border-radius: 8rpx; margin-bottom: 8rpx; }
.hj-media-audio text { font-size: 26rpx; color: #6d28d9; }
.hj-like-row { display: flex; gap: 16rpx; margin-top: 16rpx; padding-top: 16rpx; border-top: 1rpx solid #f0f0f0; }
.hj-like-btn, .hj-helpful-btn { flex: 1; text-align: center; background: #f9f0ff; padding: 16rpx; border-radius: 12rpx; font-size: 26rpx; color: #6d28d9; }

</style>
