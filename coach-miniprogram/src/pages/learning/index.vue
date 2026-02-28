<template>
  <view class="lc-page">

    <view class="lc-navbar safe-area-top">
      <view class="lc-navbar__back" @tap="goBack"><text class="lc-navbar__arrow">‹</text></view>
      <text class="lc-navbar__title">学习中心</text>
      <view class="lc-navbar__placeholder"></view>
    </view>

    <!-- 学习统计 -->
    <view class="lc-stats">
      <view class="lc-stat">
        <text class="lc-stat__val">{{ learningStore.totalMinutes }}</text>
        <text class="lc-stat__lbl">总时长(分)</text>
      </view>
      <view class="lc-stat__divider"></view>
      <view class="lc-stat">
        <text class="lc-stat__val text-primary-color">{{ learningStore.currentStreak }}</text>
        <text class="lc-stat__lbl">连续天数</text>
      </view>
      <view class="lc-stat__divider"></view>
      <view class="lc-stat">
        <text class="lc-stat__val">{{ completedCount }}</text>
        <text class="lc-stat__lbl">完课数</text>
      </view>
    </view>

    <!-- 模块 Tab -->
    <view class="lc-module-tabs">
      <view
        v-for="tab in MODULE_TABS"
        :key="tab.key"
        class="lc-module-tab"
        :class="{ 'lc-module-tab--active': activeModule === tab.key }"
        @tap="activeModule = tab.key"
      >
        <text>{{ tab.label }}</text>
      </view>
    </view>

    <!-- 类型筛选 -->
    <view class="lc-type-tabs">
      <view
        v-for="t in TYPE_TABS"
        :key="t.key"
        class="lc-type-tab"
        :class="{ 'lc-type-tab--active': activeType === t.key }"
        @tap="switchType(t.key)"
      >
        <text>{{ t.label }}</text>
      </view>
    </view>

    <!-- 内容列表 -->
    <scroll-view scroll-y class="lc-body" @scrolltolower="loadMore">

      <template v-if="loading && !contentList.length">
        <view class="bhp-skeleton" v-for="i in 4" :key="i" style="height: 200rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <view v-else-if="contentList.length" class="lc-grid">
        <BHPCourseCard
          v-for="item in contentList"
          :key="item.id"
          :title="item.title"
          :cover="item.cover_url"
          :type="item.type || item.content_type"
          :duration="item.estimated_minutes ? item.estimated_minutes + '分钟' : ''"
          :points="item.points"
          class="lc-grid__item"
          @tap="goDetail(item.id, item.type || item.content_type)"
        />
      </view>

      <view v-else class="lc-empty">
        <text class="lc-empty__icon">📚</text>
        <text class="lc-empty__text">暂无内容</text>
      </view>

      <view class="lc-load-more" v-if="hasMore && contentList.length">
        <text class="text-sm text-secondary-color">{{ loading ? '加载中...' : '上拉加载更多' }}</text>
      </view>

    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'
import { useLearningStore } from '@/stores/learning'
import BHPCourseCard from '@/components/BHPCourseCard.vue'

const learningStore = useLearningStore()

const MODULE_TABS = [
  { key: 'all',    label: '全部' },
  { key: 'M1',     label: 'M1 基础' },
  { key: 'M2',     label: 'M2 进阶' },
  { key: 'M3',     label: 'M3 实践' },
  { key: 'M4',     label: 'M4 精通' },
]

const TYPE_TABS = [
  { key: 'all',     label: '全部' },
  { key: 'video',   label: '视频' },
  { key: 'article', label: '图文' },
  { key: 'audio',   label: '音频' },
]

const activeModule  = ref('all')
const activeType    = ref('all')
const contentList   = ref<any[]>([])
const loading       = ref(false)
const page          = ref(1)
const hasMore       = ref(true)
const completedCount = ref(0)

onMounted(async () => {
  learningStore.fetchStats()
  loadContent()
  loadCompletedCount()
})

async function loadContent(append = false) {
  if (loading.value) return
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: 10 }
    if (activeType.value !== 'all') params.content_type = activeType.value
    if (activeModule.value !== 'all') params.level = activeModule.value
    const res = await http.get<{ items: any[] }>('/v1/content/recommendations', params)
    const items = res.items || (Array.isArray(res) ? res : [])
    contentList.value = append ? [...contentList.value, ...items] : items
    hasMore.value = items.length >= 10
  } catch {
    if (!append) contentList.value = []
  } finally {
    loading.value = false
  }
}

async function loadCompletedCount() {
  try {
    const res = await http.get<any>('/v1/content/user/learning-history', { page_size: 1 })
    completedCount.value = res.total || 0
  } catch { /* ignore */ }
}

function switchType(key: string) {
  activeType.value = key
  page.value = 1
  loadContent()
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  page.value++
  loadContent(true)
}

function goDetail(id: number, type: string) {
  if (type === 'video') {
    uni.navigateTo({ url: `/pages/learning/video-player?id=${id}` })
  } else if (type === 'audio') {
    uni.navigateTo({ url: `/pages/learning/audio-player?id=${id}` })
  } else {
    uni.navigateTo({ url: `/pages/learning/content-detail?id=${id}` })
  }
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.lc-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.lc-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.lc-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.lc-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.lc-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.lc-navbar__placeholder { width: 64rpx; }

/* 学习统计 */
.lc-stats {
  display: flex; align-items: center; justify-content: center;
  background: var(--surface); padding: 24rpx 32rpx;
  border-bottom: 1px solid var(--border-light);
}
.lc-stat { display: flex; flex-direction: column; align-items: center; flex: 1; gap: 4rpx; }
.lc-stat__val { font-size: 40rpx; font-weight: 800; color: var(--text-primary); }
.lc-stat__lbl { font-size: 22rpx; color: var(--text-secondary); }
.lc-stat__divider { width: 1px; height: 56rpx; background: var(--border-light); }

/* 模块 Tab */
.lc-module-tabs {
  display: flex; background: var(--surface); padding: 12rpx 32rpx;
  gap: 12rpx; overflow-x: auto; white-space: nowrap;
  border-bottom: 1px solid var(--border-light);
}
.lc-module-tab {
  padding: 10rpx 24rpx; border-radius: var(--radius-full);
  font-size: 24rpx; font-weight: 600; color: var(--text-secondary);
  background: var(--surface-secondary); cursor: pointer; flex-shrink: 0;
}
.lc-module-tab--active { background: var(--bhp-primary-500); color: #fff; }

/* 类型筛选 */
.lc-type-tabs {
  display: flex; background: var(--surface); padding: 8rpx 32rpx 14rpx;
  gap: 24rpx;
}
.lc-type-tab {
  font-size: 24rpx; color: var(--text-tertiary); cursor: pointer;
  padding-bottom: 8rpx; border-bottom: 2px solid transparent;
}
.lc-type-tab--active { color: var(--bhp-primary-600); font-weight: 600; border-bottom-color: var(--bhp-primary-500); }

/* 内容列表 */
.lc-body { flex: 1; padding: 20rpx 32rpx 40rpx; }
.lc-grid { display: flex; flex-wrap: wrap; gap: 16rpx; }
.lc-grid__item { width: calc(50% - 8rpx); }

.lc-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.lc-empty__icon { font-size: 64rpx; }
.lc-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
.lc-load-more { text-align: center; padding: 24rpx; }
</style>
