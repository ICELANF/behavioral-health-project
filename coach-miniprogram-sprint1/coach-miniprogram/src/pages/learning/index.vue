<template>
  <view class="learn-page">

    <!-- 顶部搜索栏 -->
    <view class="learn-header">
      <view class="learn-search" @tap="focusSearch">
        <text class="learn-search__icon">🔍</text>
        <input
          class="learn-search__input"
          v-model="keyword"
          placeholder="搜索课程、视频、文章..."
          placeholder-class="search-placeholder"
          confirm-type="search"
          @confirm="doSearch"
        />
        <text class="learn-search__clear" v-if="keyword" @tap.stop="clearSearch">✕</text>
      </view>
    </view>

    <!-- 过滤 Tab（内容类型）-->
    <scroll-view scroll-x class="learn-tabs">
      <view class="learn-tabs__inner">
        <view
          v-for="tab in typeTabs"
          :key="tab.key"
          class="learn-tab"
          :class="{ 'learn-tab--active': activeType === tab.key }"
          @tap="setType(tab.key)"
        >
          <text>{{ tab.label }}</text>
        </view>
      </view>
    </scroll-view>

    <!-- 学习统计横条 -->
    <view class="learn-stats-bar px-4" v-if="!keyword">
      <view class="learn-stats-bar__item" @tap="goMyLearning">
        <text class="learn-stats-bar__value">{{ formatMinutes(stats?.today_minutes || 0) }}</text>
        <text class="learn-stats-bar__label">今日</text>
      </view>
      <view class="learn-stats-bar__divider"></view>
      <view class="learn-stats-bar__item" @tap="goMyLearning">
        <text class="learn-stats-bar__value">{{ stats?.current_streak || 0 }}天</text>
        <text class="learn-stats-bar__label">连续</text>
      </view>
      <view class="learn-stats-bar__divider"></view>
      <view class="learn-stats-bar__item" @tap="goCredits">
        <text class="learn-stats-bar__value">{{ credits?.total || 0 }}</text>
        <text class="learn-stats-bar__label">学分</text>
      </view>
      <view class="learn-stats-bar__divider"></view>
      <view class="learn-stats-bar__item" @tap="goCatalog">
        <text class="learn-stats-bar__value" style="color: var(--bhp-primary-500)">目录</text>
        <text class="learn-stats-bar__label">M1-M4</text>
      </view>
    </view>

    <!-- 内容列表 -->
    <view class="learn-list px-4">
      <!-- 骨架屏 -->
      <template v-if="loading && !items.length">
        <view v-for="i in 4" :key="i" class="bhp-skeleton learn-skeleton"></view>
      </template>

      <!-- 内容卡片 -->
      <template v-else>
        <view
          v-for="item in items"
          :key="item.id"
          class="learn-item bhp-card bhp-card--flat"
          @tap="goContent(item)"
        >
          <!-- 封面图 -->
          <view class="learn-item__cover" v-if="item.cover_url">
            <image class="learn-item__img" :src="item.cover_url" mode="aspectFill" lazy-load />
            <!-- 类型角标 -->
            <view class="learn-item__type-badge">
              <text>{{ TYPE_ICON[item.content_type] || '📄' }}</text>
              <text class="learn-item__type-text">{{ TYPE_LABEL[item.content_type] || '内容' }}</text>
            </view>
            <!-- 视频时长 -->
            <text class="learn-item__duration" v-if="item.duration">
              {{ formatDuration(item.duration) }}
            </text>
            <!-- 进度条 -->
            <view class="learn-item__progress-bar" v-if="(item.progress_percent || 0) > 0">
              <view class="learn-item__progress-fill" :style="{ width: item.progress_percent + '%' }"></view>
            </view>
          </view>

          <!-- 文字区 -->
          <view class="learn-item__body">
            <view class="learn-item__meta flex-start gap-2">
              <view class="bhp-badge bhp-badge--success" v-if="item.domain">
                <text>{{ DOMAIN_LABEL[item.domain] || item.domain }}</text>
              </view>
              <view class="bhp-badge bhp-badge--gray" v-if="item.level">
                <text>{{ item.level }}</text>
              </view>
              <view class="bhp-badge bhp-badge--primary" v-if="item.has_quiz">
                <text>含测验</text>
              </view>
            </view>
            <text class="learn-item__title line-clamp-2">{{ item.title }}</text>
            <view class="learn-item__footer flex-between">
              <text class="text-xs text-secondary-color">{{ item.author_name || '行健平台' }}</text>
              <text class="text-xs text-secondary-color">{{ item.view_count || 0 }} 阅读</text>
            </view>
          </view>
        </view>

        <!-- 空状态 -->
        <view class="learn-empty" v-if="!loading && !items.length">
          <text class="learn-empty__icon">📭</text>
          <text class="learn-empty__text">{{ keyword ? '没有找到相关内容' : '暂无内容' }}</text>
        </view>

        <!-- 加载更多 -->
        <view class="learn-load-more" v-if="hasMore" @tap="loadMore">
          <text v-if="!loadingMore">加载更多</text>
          <text v-else>加载中...</text>
        </view>
        <view class="learn-load-more learn-load-more--end" v-else-if="items.length > 0">
          <text>已显示全部</text>
        </view>
      </template>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useLearningStore } from '@/stores/learning'
import { contentApi, learningApi, creditsApi, type ContentItem } from '@/api/learning'
import { formatMinutes } from '@/utils/level'

const learningStore = useLearningStore()

const keyword    = ref('')
const activeType = ref('all')
const loading    = ref(false)
const loadingMore= ref(false)
const items      = ref<ContentItem[]>([])
const page       = ref(1)
const hasMore    = ref(true)
const stats      = ref<any>(null)
const credits    = ref<any>(null)

const typeTabs = [
  { key: 'all',        label: '全部' },
  { key: 'article',    label: '图文' },
  { key: 'video',      label: '视频' },
  { key: 'audio',      label: '音频' },
  { key: 'course',     label: '课程' },
  { key: 'card',       label: '练习卡' },
]

const TYPE_LABEL: Record<string, string> = {
  article: '图文', video: '视频', course: '课程',
  audio: '音频', card: '练习卡', case_share: '案例'
}
const TYPE_ICON: Record<string, string> = {
  article: '📖', video: '▶️', course: '📚',
  audio: '🎵', card: '🃏', case_share: '💬'
}
const DOMAIN_LABEL: Record<string, string> = {
  nutrition: '营养', exercise: '运动', sleep: '睡眠',
  emotion: '情绪', tcm: '中医', metabolic: '代谢', behavior: '行为'
}

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

async function loadItems(reset = false) {
  if (reset) { page.value = 1; items.value = []; hasMore.value = true }
  if (!hasMore.value) return
  reset ? (loading.value = true) : (loadingMore.value = true)
  try {
    const params: any = {
      page: page.value, page_size: 12, status: 'published'
    }
    if (activeType.value !== 'all') params.content_type = activeType.value
    if (keyword.value.trim()) params.search = keyword.value.trim()

    const data = await contentApi.list(params)
    const newItems = data.items || []
    if (reset) {
      items.value = newItems
    } else {
      items.value = [...items.value, ...newItems]
    }
    hasMore.value = newItems.length === 12
    page.value++
  } catch { /* 静默 */ } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function loadStats() {
  try {
    const [s, c] = await Promise.all([
      learningApi.myStats(),
      creditsApi.mySummary()
    ])
    stats.value = s
    credits.value = c
  } catch { /* 静默 */ }
}

onMounted(async () => {
  await Promise.all([loadItems(true), loadStats()])
})

onPullDownRefresh(async () => {
  await Promise.all([loadItems(true), loadStats()])
  uni.stopPullDownRefresh()
})

watch(activeType, () => loadItems(true))

function setType(key: string) { activeType.value = key }

let searchTimer: any = null
function doSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadItems(true), 300)
}

function clearSearch() {
  keyword.value = ''
  loadItems(true)
}

function focusSearch() { /* 输入框自动聚焦 */ }
function loadMore() { loadItems(false) }

// ─── 导航 ─────────────────────────────────────────────────────
function goContent(item: ContentItem) {
  const typePageMap: Record<string, string> = {
    video:      '/pages/learning/video-player',
    audio:      '/pages/learning/audio-player',
    course:     '/pages/learning/course-detail',
    article:    '/pages/learning/content-detail',
    card:       '/pages/learning/content-detail',
    case_share: '/pages/learning/content-detail',
  }
  const page = typePageMap[item.content_type] || '/pages/learning/content-detail'
  uni.navigateTo({ url: `${page}?id=${item.id}` })
}

function goCatalog()    { uni.navigateTo({ url: '/pages/learning/catalog' }) }
function goMyLearning() { uni.navigateTo({ url: '/pages/learning/my-learning' }) }
function goCredits()    { uni.navigateTo({ url: '/pages/learning/credits' }) }
</script>

<style scoped>
.learn-page { background: var(--surface-secondary); min-height: 100vh; }

/* 头部搜索 */
.learn-header {
  background: var(--surface);
  padding: 60rpx 24rpx 20rpx;
  position: sticky;
  top: 0;
  z-index: 10;
}
.learn-search {
  display: flex;
  align-items: center;
  background: var(--bhp-gray-100);
  border-radius: var(--radius-full);
  padding: 16rpx 24rpx;
  gap: 12rpx;
}
.learn-search__icon  { font-size: 28rpx; color: var(--text-tertiary); }
.learn-search__input {
  flex: 1;
  font-size: 28rpx;
  color: var(--text-primary);
  background: transparent;
}
.learn-search__clear { font-size: 24rpx; color: var(--text-tertiary); padding: 0 4rpx; }
.search-placeholder  { color: var(--text-tertiary); font-size: 28rpx; }

/* 类型 Tab */
.learn-tabs {
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
  white-space: nowrap;
}
.learn-tabs__inner { display: flex; gap: 0; padding: 0 16rpx; }
.learn-tab {
  padding: 20rpx 24rpx;
  font-size: 26rpx;
  color: var(--text-secondary);
  position: relative;
  white-space: nowrap;
  cursor: pointer;
}
.learn-tab--active {
  color: var(--bhp-primary-500);
  font-weight: 600;
}
.learn-tab--active::after {
  content: '';
  position: absolute;
  bottom: 0; left: 12rpx; right: 12rpx;
  height: 3rpx;
  background: var(--bhp-primary-500);
  border-radius: 9999px;
}

/* 统计横条 */
.learn-stats-bar {
  display: flex;
  align-items: center;
  background: var(--surface);
  margin: 16rpx 24rpx;
  border-radius: var(--radius-lg);
  padding: 20rpx 0;
  box-shadow: var(--shadow-card);
}
.learn-stats-bar__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  cursor: pointer;
}
.learn-stats-bar__item:active { opacity: 0.7; }
.learn-stats-bar__value { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.learn-stats-bar__label { font-size: 20rpx; color: var(--text-secondary); }
.learn-stats-bar__divider {
  width: 1px; height: 40rpx;
  background: var(--border-light);
}

/* 内容列表 */
.learn-list { padding-top: 16rpx; }
.learn-skeleton { height: 200rpx; margin-bottom: 16rpx; border-radius: var(--radius-lg); }

/* 内容卡片 */
.learn-item {
  display: flex;
  margin-bottom: 16rpx;
  overflow: hidden;
  padding: 0;
  cursor: pointer;
}
.learn-item:active { opacity: 0.85; }
.learn-item__cover {
  width: 200rpx;
  flex-shrink: 0;
  position: relative;
  background: var(--bhp-gray-100);
  min-height: 140rpx;
}
.learn-item__img { width: 100%; height: 100%; }
.learn-item__type-badge {
  position: absolute;
  top: 6px; left: 6px;
  background: rgba(0,0,0,0.55);
  border-radius: 6px;
  padding: 2px 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.learn-item__type-text { font-size: 18rpx; color: #fff; }
.learn-item__duration {
  position: absolute;
  bottom: 6px; right: 6px;
  background: rgba(0,0,0,0.55);
  color: #fff;
  font-size: 18rpx;
  padding: 2px 6px;
  border-radius: 4px;
}
.learn-item__progress-bar {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 4px;
  background: rgba(255,255,255,0.3);
}
.learn-item__progress-fill {
  height: 100%;
  background: var(--bhp-primary-500);
}

.learn-item__body {
  flex: 1;
  padding: 16rpx 20rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.learn-item__meta { margin-bottom: 8rpx; flex-wrap: wrap; gap: 6px; }
.learn-item__title {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  flex: 1;
  margin-bottom: 8rpx;
}
.learn-item__footer { }

/* 空状态 */
.learn-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
  gap: 16rpx;
}
.learn-empty__icon { font-size: 80rpx; }
.learn-empty__text { font-size: 28rpx; color: var(--text-tertiary); }

/* 加载更多 */
.learn-load-more {
  text-align: center;
  padding: 24rpx;
  font-size: 26rpx;
  color: var(--bhp-primary-500);
  cursor: pointer;
}
.learn-load-more--end { color: var(--text-tertiary); }
</style>
