<template>
  <view class="catalog-page">

    <!-- 模块切换 Tab -->
    <scroll-view scroll-x class="catalog-module-tabs">
      <view class="catalog-module-tabs__inner">
        <view
          v-for="m in modules"
          :key="m.key"
          class="catalog-module-tab"
          :class="{ 'catalog-module-tab--active': activeModule === m.key }"
          @tap="setModule(m.key)"
        >
          <text class="catalog-module-tab__icon">{{ m.icon }}</text>
          <text class="catalog-module-tab__label">{{ m.label }}</text>
        </view>
      </view>
    </scroll-view>

    <!-- 当前模块描述 -->
    <view class="catalog-module-desc px-4">
      <view class="catalog-module-desc__card bhp-card bhp-card--flat" v-if="currentModule">
        <view class="flex-start gap-3">
          <text class="catalog-module-desc__icon">{{ currentModule.icon }}</text>
          <view class="flex-1">
            <text class="catalog-module-desc__title">{{ currentModule.label }}</text>
            <text class="catalog-module-desc__sub">{{ currentModule.desc }}</text>
          </view>
          <view class="bhp-badge" :class="`bhp-badge--${currentModule.badgeColor}`">
            <text>{{ currentModule.creditLabel }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 内容列表 -->
    <view class="catalog-list px-4">
      <!-- 骨架屏 -->
      <template v-if="loading">
        <view v-for="i in 5" :key="i" class="bhp-skeleton catalog-skeleton"></view>
      </template>

      <template v-else>
        <view
          v-for="item in items"
          :key="item.id"
          class="catalog-item bhp-card bhp-card--flat"
          :class="{ 'catalog-item--locked': isLocked(item) }"
          @tap="goContent(item)"
        >
          <!-- 左侧：封面或类型图标 -->
          <view class="catalog-item__cover">
            <image
              v-if="item.cover_url"
              class="catalog-item__img"
              :src="item.cover_url"
              mode="aspectFill"
              lazy-load
            />
            <view v-else class="catalog-item__icon-wrap">
              <text class="catalog-item__type-icon">{{ TYPE_ICON[item.content_type] || '📄' }}</text>
            </view>
            <!-- 已完成遮罩 -->
            <view class="catalog-item__done-mask" v-if="(item.progress_percent || 0) >= 100">
              <text>✓</text>
            </view>
            <!-- 锁定遮罩 -->
            <view class="catalog-item__lock-mask" v-else-if="isLocked(item)">
              <text>🔒</text>
            </view>
          </view>

          <!-- 右侧：信息 -->
          <view class="catalog-item__body">
            <view class="flex-start gap-2 mb-1">
              <view class="bhp-badge bhp-badge--gray" v-if="item.level">
                <text>{{ item.level }}</text>
              </view>
              <view class="bhp-badge bhp-badge--success" v-if="item.has_quiz">
                <text>含测验</text>
              </view>
              <view class="bhp-badge bhp-badge--primary" v-if="item.duration">
                <text>{{ formatDuration(item.duration) }}</text>
              </view>
            </view>
            <text class="catalog-item__title line-clamp-2">{{ item.title }}</text>
            <view class="catalog-item__footer">
              <text class="text-xs text-tertiary-color">{{ TYPE_LABEL[item.content_type] || '内容' }}</text>
              <!-- 进度条 -->
              <view class="catalog-item__progress" v-if="(item.progress_percent || 0) > 0 && (item.progress_percent || 0) < 100">
                <view class="catalog-item__progress-fill" :style="{ width: (item.progress_percent || 0) + '%' }"></view>
              </view>
              <text class="catalog-item__done-text" v-if="(item.progress_percent || 0) >= 100">已完成 ✓</text>
            </view>
          </view>
        </view>

        <!-- 空状态 -->
        <view class="catalog-empty" v-if="!loading && !items.length">
          <text class="catalog-empty__icon">📭</text>
          <text class="catalog-empty__text">暂无内容</text>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { contentApi, type ContentItem } from '@/api/learning'

const userStore = useUserStore()

const activeModule = ref('m1')
const loading      = ref(false)
const loadingMore  = ref(false)
const items        = ref<ContentItem[]>([])
const page         = ref(1)
const hasMore      = ref(true)

const LEVEL_GATE: Record<string, number> = {
  L0: 0, L1: 1, L2: 2, L3: 3, L4: 4, L5: 5
}

const TYPE_LABEL: Record<string, string> = {
  article: '图文', video: '视频', course: '课程',
  audio: '音频', card: '练习卡', case_share: '案例'
}
const TYPE_ICON: Record<string, string> = {
  article: '📖', video: '▶️', course: '📚',
  audio: '🎵', card: '🃏', case_share: '💬'
}

const modules = [
  {
    key: 'm1',
    label: 'M1 认知基础',
    icon: '🧠',
    desc: '行为健康基础理论 · 6大健康领域入门',
    creditLabel: '必修 8学分',
    badgeColor: 'primary'
  },
  {
    key: 'm2',
    label: 'M2 评估技能',
    icon: '📊',
    desc: 'BAPS评估 · 数据解读 · 风险识别',
    creditLabel: '必修 10学分',
    badgeColor: 'success'
  },
  {
    key: 'm3',
    label: 'M3 干预方法',
    icon: '🛠️',
    desc: '处方制定 · 行为激励 · 习惯养成',
    creditLabel: '必修 12学分',
    badgeColor: 'warn'
  },
  {
    key: 'm4',
    label: 'M4 高阶带教',
    icon: '🎓',
    desc: '督导技能 · 团队管理 · 案例复盘',
    creditLabel: '选修 6学分',
    badgeColor: 'gray'
  },
]

const currentModule = computed(() => modules.find(m => m.key === activeModule.value))

function isLocked(item: ContentItem): boolean {
  if (!item.level) return false
  const required = LEVEL_GATE[item.level] ?? 0
  return userStore.roleLevel < required
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
    const data = await contentApi.list({
      page: page.value,
      page_size: 20,
      module: activeModule.value,
      status: 'published'
    })
    const newItems = data.items || []
    items.value = reset ? newItems : [...items.value, ...newItems]
    hasMore.value = newItems.length === 20
    page.value++
  } catch { /* 静默 */ } finally {
    loading.value = false
    loadingMore.value = false
  }
}

onMounted(() => loadItems(true))
watch(activeModule, () => loadItems(true))

function setModule(key: string) { activeModule.value = key }
function loadMore() { loadItems(false) }

function goContent(item: ContentItem) {
  if (isLocked(item)) {
    uni.showToast({ title: `需达到${item.level}等级解锁`, icon: 'none' })
    return
  }
  const typePageMap: Record<string, string> = {
    video:      '/pages/learning/video-player',
    audio:      '/pages/learning/audio-player',
    course:     '/pages/learning/course-detail',
    article:    '/pages/learning/content-detail',
    card:       '/pages/learning/content-detail',
    case_share: '/pages/learning/content-detail',
  }
  const p = typePageMap[item.content_type] || '/pages/learning/content-detail'
  uni.navigateTo({ url: `${p}?id=${item.id}` })
}
</script>

<style scoped>
.catalog-page { background: var(--surface-secondary); min-height: 100vh; }

/* 模块 Tab */
.catalog-module-tabs {
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
  white-space: nowrap;
}
.catalog-module-tabs__inner { display: flex; padding: 12rpx 16rpx; gap: 12rpx; }
.catalog-module-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12rpx 20rpx;
  border-radius: var(--radius-lg);
  gap: 4rpx;
  cursor: pointer;
  background: var(--bhp-gray-100);
  white-space: nowrap;
}
.catalog-module-tab--active {
  background: var(--bhp-primary-50);
}
.catalog-module-tab__icon { font-size: 32rpx; }
.catalog-module-tab__label { font-size: 22rpx; color: var(--text-secondary); }
.catalog-module-tab--active .catalog-module-tab__label {
  color: var(--bhp-primary-500);
  font-weight: 600;
}

/* 模块描述 */
.catalog-module-desc { padding-top: 16rpx; }
.catalog-module-desc__icon { font-size: 40rpx; }
.catalog-module-desc__title { font-size: 28rpx; font-weight: 700; color: var(--text-primary); display: block; }
.catalog-module-desc__sub { font-size: 24rpx; color: var(--text-secondary); display: block; margin-top: 4rpx; }

/* 列表 */
.catalog-list { padding-top: 16rpx; }
.catalog-skeleton { height: 120rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg); }

/* 条目 */
.catalog-item {
  display: flex;
  margin-bottom: 12rpx;
  padding: 0;
  overflow: hidden;
  cursor: pointer;
}
.catalog-item--locked { opacity: 0.6; }
.catalog-item:active { opacity: 0.8; }

.catalog-item__cover {
  width: 160rpx;
  flex-shrink: 0;
  position: relative;
  background: var(--bhp-gray-100);
  min-height: 120rpx;
}
.catalog-item__img { width: 100%; height: 100%; }
.catalog-item__icon-wrap {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120rpx;
}
.catalog-item__type-icon { font-size: 48rpx; }
.catalog-item__done-mask,
.catalog-item__lock-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
}
.catalog-item__done-mask {
  background: rgba(16,185,129,0.3);
  color: #fff;
  font-weight: 700;
  font-size: 40rpx;
}
.catalog-item__lock-mask { background: rgba(0,0,0,0.35); }

.catalog-item__body {
  flex: 1;
  padding: 16rpx 20rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.catalog-item__title {
  font-size: 26rpx;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  flex: 1;
  margin: 8rpx 0;
}
.catalog-item__footer { display: flex; align-items: center; justify-content: space-between; }
.catalog-item__done-text { font-size: 20rpx; color: var(--bhp-success-500); }
.catalog-item__progress {
  flex: 1;
  height: 6rpx;
  background: var(--bhp-gray-200);
  border-radius: 9999px;
  margin-left: 16rpx;
  overflow: hidden;
}
.catalog-item__progress-fill {
  height: 100%;
  background: var(--bhp-primary-500);
  border-radius: 9999px;
}

/* 空状态 */
.catalog-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
  gap: 16rpx;
}
.catalog-empty__icon { font-size: 80rpx; }
.catalog-empty__text { font-size: 28rpx; color: var(--text-tertiary); }

/* 加载更多（复用 learn 样式名）*/
.learn-load-more {
  text-align: center;
  padding: 24rpx;
  font-size: 26rpx;
  color: var(--bhp-primary-500);
  cursor: pointer;
}
.learn-load-more--end { color: var(--text-tertiary); }
</style>
