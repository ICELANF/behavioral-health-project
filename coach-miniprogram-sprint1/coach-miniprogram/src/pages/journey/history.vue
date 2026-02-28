<template>
  <view class="promo-history-page">

    <!-- 筛选 Tab -->
    <view class="ph-filter px-4">
      <view class="ph-filter__inner">
        <view
          v-for="tab in filterTabs"
          :key="tab.key"
          class="ph-filter__tab"
          :class="{ 'ph-filter__tab--active': activeFilter === tab.key }"
          @tap="setFilter(tab.key)"
        >
          <text>{{ tab.label }}</text>
          <text class="ph-filter__count" v-if="tabCount(tab.key) > 0">{{ tabCount(tab.key) }}</text>
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <view class="ph-list px-4">

      <!-- 骨架屏 -->
      <template v-if="loading">
        <view v-for="i in 4" :key="i" class="bhp-skeleton" style="height: 140rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else>
        <view
          v-for="item in filteredItems"
          :key="item.id"
          class="ph-item bhp-card bhp-card--flat"
        >
          <!-- 顶部：等级箭头 + 状态 -->
          <view class="ph-item__header">
            <view class="ph-item__levels">
              <view class="ph-item__level-tag" :style="{ background: getLevelColor(item.from_level) + '20', color: getLevelColor(item.from_level) }">
                <text>{{ item.from_level }}</text>
              </view>
              <text class="ph-item__arrow">→</text>
              <view class="ph-item__level-tag" :style="{ background: getLevelColor(item.to_level) + '20', color: getLevelColor(item.to_level) }">
                <text>{{ item.to_level }}</text>
              </view>
            </view>
            <view class="ph-item__status-badge" :class="`ph-status--${item.status}`">
              <text>{{ STATUS_LABEL[item.status] }}</text>
            </view>
          </view>

          <!-- 中间：日期信息 -->
          <view class="ph-item__meta">
            <text class="text-xs text-secondary-color">申请时间：{{ formatDate(item.submitted_at) }}</text>
            <text class="text-xs text-secondary-color" v-if="item.reviewed_at">
              审核时间：{{ formatDate(item.reviewed_at) }}
            </text>
          </view>

          <!-- 申请理由 -->
          <view class="ph-item__reason" v-if="item.reason">
            <text class="text-xs text-secondary-color line-clamp-2">{{ item.reason }}</text>
          </view>

          <!-- 审核意见 -->
          <view class="ph-item__review" v-if="item.reviewer_note">
            <view class="ph-item__review-card" :class="item.status === 'approved' ? 'ph-review--pass' : 'ph-review--reject'">
              <text class="ph-item__review-label">审核意见：</text>
              <text class="ph-item__review-text">{{ item.reviewer_note }}</text>
            </view>
          </view>

          <!-- 审核人 -->
          <view class="ph-item__footer" v-if="item.reviewer_name">
            <text class="text-xs text-tertiary-color">审核人：{{ item.reviewer_name }}</text>
          </view>

          <!-- 撤回按钮（仅待审核）-->
          <view class="ph-item__actions" v-if="item.status === 'pending'">
            <view class="ph-withdraw-btn" @tap="withdrawApplication(item)">
              <text>撤回申请</text>
            </view>
          </view>
        </view>

        <!-- 加载更多 -->
        <view class="ph-load-more" v-if="hasMore" @tap="loadMore">
          <text v-if="!loadingMore">加载更多</text>
          <text v-else>加载中...</text>
        </view>
        <view class="ph-load-more ph-load-more--end" v-else-if="items.length > 0">
          <text>已显示全部</text>
        </view>

        <!-- 空状态 -->
        <view class="ph-empty" v-if="!loading && !filteredItems.length">
          <text class="ph-empty__icon">📋</text>
          <text class="ph-empty__text">{{ emptyText }}</text>
          <view class="bhp-btn bhp-btn--primary mt-4" @tap="goPromotion" v-if="activeFilter === 'all'">
            <text>申请晋级</text>
          </view>
        </view>
      </template>
    </view>

    <!-- 底部浮动按钮：新申请 -->
    <view class="ph-fab" v-if="!loading && !hasPending" @tap="goPromotion">
      <text class="ph-fab__icon">+</text>
      <text class="ph-fab__label">申请晋级</text>
    </view>

    <view style="height: 100rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { promotionApi, LEVEL_META, type PromotionApplication } from '@/api/journey'

const items        = ref<PromotionApplication[]>([])
const loading      = ref(false)
const loadingMore  = ref(false)
const page         = ref(1)
const hasMore      = ref(true)
const activeFilter = ref<'all' | 'pending' | 'approved' | 'rejected'>('all')
const withdrawingId= ref<number | null>(null)

const STATUS_LABEL: Record<string, string> = {
  pending:   '审核中',
  approved:  '已通过',
  rejected:  '未通过',
  withdrawn: '已撤回'
}

const filterTabs = [
  { key: 'all',      label: '全部' },
  { key: 'pending',  label: '审核中' },
  { key: 'approved', label: '已通过' },
  { key: 'rejected', label: '未通过' },
]

const filteredItems = computed(() => {
  if (activeFilter.value === 'all') return items.value
  return items.value.filter(i => i.status === activeFilter.value)
})

const hasPending = computed(() => items.value.some(i => i.status === 'pending'))

const emptyText = computed(() => {
  const map: Record<string, string> = {
    all: '暂无晋级申请记录', pending: '暂无待审核申请',
    approved: '暂无已通过申请', rejected: '暂无未通过申请'
  }
  return map[activeFilter.value] || '暂无记录'
})

function tabCount(key: string): number {
  if (key === 'all') return 0
  return items.value.filter(i => i.status === key).length
}

const LEVEL_COLORS: Record<string, string> = {
  L0: '#8c8c8c', L1: '#52c41a', L2: '#1890ff',
  L3: '#722ed1', L4: '#eb2f96', L5: '#faad14'
}
function getLevelColor(key: string): string {
  return LEVEL_COLORS[key] || '#8c8c8c'
}

onMounted(() => loadHistory(true))

onPullDownRefresh(async () => {
  await loadHistory(true)
  uni.stopPullDownRefresh()
})

async function loadHistory(reset = false) {
  if (reset) { page.value = 1; items.value = []; hasMore.value = true }
  if (!hasMore.value) return
  reset ? (loading.value = true) : (loadingMore.value = true)
  try {
    const data = await promotionApi.myHistory(page.value)
    const newItems = data.items || []
    items.value = reset ? newItems : [...items.value, ...newItems]
    hasMore.value = newItems.length === 20
    page.value++
  } catch { /* 静默 */ } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() { loadHistory(false) }
function setFilter(key: 'all' | 'pending' | 'approved' | 'rejected') { activeFilter.value = key }

async function withdrawApplication(item: PromotionApplication) {
  uni.showModal({
    title: '确认撤回',
    content: '撤回后申请将取消，如需晋级请重新提交。确认撤回吗？',
    confirmText: '确认撤回',
    confirmColor: '#ef4444',
    success: async (res) => {
      if (!res.confirm) return
      withdrawingId.value = item.id
      try {
        await promotionApi.withdraw(item.id)
        // 本地更新状态
        const idx = items.value.findIndex(i => i.id === item.id)
        if (idx >= 0) items.value[idx].status = 'withdrawn'
        uni.showToast({ title: '已撤回', icon: 'none' })
      } catch {
        uni.showToast({ title: '撤回失败', icon: 'none' })
      } finally {
        withdrawingId.value = null
      }
    }
  })
}

function goPromotion() {
  uni.navigateTo({ url: '/pages/journey/promotion' })
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch { return dateStr }
}
</script>

<style scoped>
.promo-history-page { background: var(--surface-secondary); min-height: 100vh; }

/* 筛选 */
.ph-filter { padding-top: 16rpx; padding-bottom: 8rpx; }
.ph-filter__inner {
  display: flex;
  background: var(--surface);
  border-radius: var(--radius-full);
  padding: 6rpx;
  border: 1px solid var(--border-light);
  gap: 4rpx;
}
.ph-filter__tab {
  flex: 1;
  text-align: center;
  padding: 10rpx 8rpx;
  border-radius: var(--radius-full);
  font-size: 24rpx;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
}
.ph-filter__tab--active { background: var(--bhp-primary-500); color: #fff; font-weight: 600; }
.ph-filter__count {
  background: rgba(255,255,255,0.3);
  border-radius: var(--radius-full);
  font-size: 18rpx;
  padding: 2rpx 8rpx;
  min-width: 24rpx;
  text-align: center;
}
.ph-filter__tab:not(.ph-filter__tab--active) .ph-filter__count {
  background: var(--bhp-primary-100, #d1fae5);
  color: var(--bhp-primary-600, #059669);
}

/* 列表 */
.ph-list { padding-top: 12rpx; }

.ph-item {
  padding: 20rpx 24rpx;
  margin-bottom: 12rpx;
}

.ph-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}
.ph-item__levels { display: flex; align-items: center; gap: 12rpx; }
.ph-item__level-tag {
  padding: 4rpx 16rpx;
  border-radius: var(--radius-full);
  font-size: 22rpx;
  font-weight: 700;
}
.ph-item__arrow { font-size: 28rpx; color: var(--text-tertiary); }

.ph-item__status-badge {
  font-size: 22rpx;
  font-weight: 600;
  padding: 4rpx 16rpx;
  border-radius: var(--radius-full);
}
.ph-status--pending   { background: var(--bhp-warn-100, #fef3c7);   color: var(--bhp-warn-700, #b45309); }
.ph-status--approved  { background: var(--bhp-success-100, #dcfce7); color: var(--bhp-success-700, #15803d); }
.ph-status--rejected  { background: var(--bhp-error-100, #fee2e2);   color: var(--bhp-error-700, #b91c1c); }
.ph-status--withdrawn { background: var(--bhp-gray-100); color: var(--text-tertiary); }

.ph-item__meta { display: flex; flex-direction: column; gap: 4rpx; margin-bottom: 8rpx; }
.ph-item__reason { margin-bottom: 8rpx; }

.ph-item__review { margin-bottom: 8rpx; }
.ph-item__review-card {
  border-radius: var(--radius-md);
  padding: 12rpx 16rpx;
}
.ph-review--pass   { background: var(--bhp-success-50, #f0fdf4); }
.ph-review--reject { background: var(--bhp-error-50, #fef2f2); }
.ph-item__review-label { font-size: 22rpx; color: var(--text-tertiary); }
.ph-item__review-text  { font-size: 24rpx; color: var(--text-secondary); line-height: 1.5; }

.ph-item__footer { margin-top: 4rpx; }

.ph-item__actions { margin-top: 12rpx; display: flex; justify-content: flex-end; }
.ph-withdraw-btn {
  font-size: 22rpx;
  color: var(--bhp-error-500, #ef4444);
  padding: 8rpx 20rpx;
  border: 1px solid var(--bhp-error-200, #fecaca);
  border-radius: var(--radius-full);
  cursor: pointer;
}
.ph-withdraw-btn:active { opacity: 0.7; }

/* 加载更多 */
.ph-load-more {
  text-align: center;
  padding: 20rpx;
  font-size: 26rpx;
  color: var(--bhp-primary-500);
  cursor: pointer;
}
.ph-load-more--end { color: var(--text-tertiary); }

/* 空状态 */
.ph-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
  gap: 16rpx;
}
.ph-empty__icon { font-size: 80rpx; }
.ph-empty__text { font-size: 28rpx; color: var(--text-tertiary); }

/* FAB */
.ph-fab {
  position: fixed;
  bottom: 40rpx;
  right: 40rpx;
  background: var(--bhp-primary-500);
  border-radius: var(--radius-full);
  padding: 16rpx 28rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
  box-shadow: 0 4px 16px rgba(16,185,129,0.4);
  cursor: pointer;
  z-index: 50;
}
.ph-fab:active { opacity: 0.8; transform: scale(0.95); }
.ph-fab__icon  { font-size: 32rpx; color: #fff; font-weight: 700; }
.ph-fab__label { font-size: 26rpx; color: #fff; font-weight: 600; }
</style>
