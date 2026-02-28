<template>
  <view class="ml-page">

    <view class="ml-navbar safe-area-top">
      <view class="ml-navbar__back" @tap="goBack"><text class="ml-navbar__arrow">‹</text></view>
      <text class="ml-navbar__title">我的学习</text>
      <view class="ml-navbar__placeholder"></view>
    </view>

    <!-- 统计 -->
    <view class="ml-stats">
      <view class="ml-stat">
        <text class="ml-stat__val">{{ stats.total_minutes || 0 }}</text>
        <text class="ml-stat__lbl">总时长(分)</text>
      </view>
      <view class="ml-stat__divider"></view>
      <view class="ml-stat">
        <text class="ml-stat__val text-primary-color">{{ stats.completed_count || 0 }}</text>
        <text class="ml-stat__lbl">完课数</text>
      </view>
      <view class="ml-stat__divider"></view>
      <view class="ml-stat">
        <text class="ml-stat__val">{{ stats.quiz_pass_rate || 0 }}%</text>
        <text class="ml-stat__lbl">测验通过率</text>
      </view>
    </view>

    <!-- Tab -->
    <view class="ml-tabs">
      <view
        v-for="tab in TABS"
        :key="tab.key"
        class="ml-tab"
        :class="{ 'ml-tab--active': activeTab === tab.key }"
        @tap="switchTab(tab.key)"
      >
        <text>{{ tab.label }}</text>
      </view>
    </view>

    <!-- 学习记录列表 -->
    <scroll-view scroll-y class="ml-body" @scrolltolower="loadMore">

      <template v-if="loading && !records.length">
        <view class="bhp-skeleton" v-for="i in 4" :key="i" style="height: 120rpx; border-radius: var(--radius-lg); margin-bottom: 12rpx;"></view>
      </template>

      <view v-else-if="records.length" class="ml-list">
        <view v-for="item in records" :key="item.id || item.content_id" class="ml-record">
          <view class="ml-record__left">
            <view class="ml-record__type-badge" :class="`ml-record__type-badge--${item.content_type || item.type}`">
              <text>{{ TYPE_ICON[item.content_type || item.type] || '📄' }}</text>
            </view>
          </view>
          <view class="ml-record__center">
            <text class="ml-record__title">{{ item.title || item.content_title }}</text>
            <view class="ml-record__meta">
              <text>{{ TYPE_LABEL[item.content_type || item.type] || '其他' }}</text>
              <text v-if="item.time_spent_minutes">· {{ item.time_spent_minutes }}分钟</text>
              <text v-if="item.completed_at">· {{ formatDate(item.completed_at) }}</text>
            </view>
            <!-- 进度条 -->
            <view class="ml-record__progress-bar">
              <view class="ml-record__progress-fill" :style="{ width: (item.progress_pct || 0) + '%' }"></view>
            </view>
          </view>
          <text class="ml-record__pct">{{ item.progress_pct || 0 }}%</text>
        </view>
      </view>

      <view v-else class="ml-empty">
        <text class="ml-empty__icon">📚</text>
        <text class="ml-empty__text">暂无学习记录</text>
      </view>

      <view class="ml-load-more" v-if="hasMore && records.length">
        <text class="text-sm text-secondary-color">{{ loading ? '加载中...' : '上拉加载更多' }}</text>
      </view>

    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import http from '@/api/request'

const TABS = [
  { key: 'all', label: '全部' },
  { key: 'video', label: '视频' },
  { key: 'article', label: '图文' },
  { key: 'audio', label: '音频' },
  { key: 'course', label: '课程' },
]
const TYPE_LABEL: Record<string, string> = { video: '视频', article: '图文', audio: '音频', course: '课程' }
const TYPE_ICON: Record<string, string> = { video: '🎬', article: '📄', audio: '🎧', course: '📘' }

const activeTab = ref('all')
const records   = ref<any[]>([])
const stats     = reactive({ total_minutes: 0, completed_count: 0, quiz_pass_rate: 0 })
const loading   = ref(false)
const page      = ref(1)
const hasMore   = ref(true)

onMounted(() => { loadRecords(); loadStats() })

async function loadRecords(append = false) {
  if (loading.value) return
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: 20 }
    if (activeTab.value !== 'all') params.content_type = activeTab.value
    const res = await http.get<any>('/v1/content/user/learning-history', params)
    const items = res.items || res.records || (Array.isArray(res) ? res : [])
    records.value = append ? [...records.value, ...items] : items
    hasMore.value = items.length >= 20
  } catch {
    if (!append) records.value = []
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const res = await http.get<any>('/v1/content/user/learning-history', { page_size: 1 })
    stats.total_minutes = res.total_minutes || 0
    stats.completed_count = res.total || 0
    stats.quiz_pass_rate = res.quiz_pass_rate || 0
  } catch { /* ignore */ }
}

function switchTab(key: string) {
  activeTab.value = key
  page.value = 1
  loadRecords()
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  page.value++
  loadRecords(true)
}

function formatDate(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.ml-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.ml-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.ml-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ml-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.ml-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.ml-navbar__placeholder { width: 64rpx; }

.ml-stats {
  display: flex; align-items: center; background: var(--surface); padding: 24rpx 32rpx;
  border-bottom: 1px solid var(--border-light);
}
.ml-stat { display: flex; flex-direction: column; align-items: center; flex: 1; gap: 4rpx; }
.ml-stat__val { font-size: 40rpx; font-weight: 800; color: var(--text-primary); }
.ml-stat__lbl { font-size: 22rpx; color: var(--text-secondary); }
.ml-stat__divider { width: 1px; height: 56rpx; background: var(--border-light); }

.ml-tabs {
  display: flex; background: var(--surface); padding: 12rpx 32rpx 16rpx;
  gap: 16rpx; border-bottom: 1px solid var(--border-light); overflow-x: auto;
}
.ml-tab {
  padding: 10rpx 24rpx; border-radius: var(--radius-full);
  font-size: 24rpx; font-weight: 600; color: var(--text-secondary);
  background: var(--surface-secondary); cursor: pointer; flex-shrink: 0;
}
.ml-tab--active { background: var(--bhp-primary-500); color: #fff; }

.ml-body { flex: 1; padding: 20rpx 32rpx 40rpx; }
.ml-list { display: flex; flex-direction: column; gap: 12rpx; }

.ml-record {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx; border: 1px solid var(--border-light);
}
.ml-record__left { flex-shrink: 0; }
.ml-record__type-badge {
  width: 64rpx; height: 64rpx; border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center; font-size: 28rpx;
  background: var(--surface-secondary);
}
.ml-record__type-badge--video { background: #eff6ff; }
.ml-record__type-badge--article { background: #f0fdf4; }
.ml-record__type-badge--audio { background: #fefce8; }
.ml-record__type-badge--course { background: #faf5ff; }
.ml-record__center { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
.ml-record__title { font-size: 26rpx; font-weight: 600; color: var(--text-primary); display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
.ml-record__meta { font-size: 20rpx; color: var(--text-tertiary); display: flex; gap: 4rpx; }
.ml-record__progress-bar { height: 8rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.ml-record__progress-fill { height: 100%; background: var(--bhp-primary-500); border-radius: var(--radius-full); transition: width 0.3s; }
.ml-record__pct { font-size: 22rpx; font-weight: 700; color: var(--bhp-primary-600); flex-shrink: 0; width: 64rpx; text-align: right; }

.ml-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.ml-empty__icon { font-size: 64rpx; }
.ml-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
.ml-load-more { text-align: center; padding: 24rpx; }
</style>
