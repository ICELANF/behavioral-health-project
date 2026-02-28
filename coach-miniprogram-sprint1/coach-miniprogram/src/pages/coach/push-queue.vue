<template>
  <view class="pq-page">

    <!-- 状态 Tab -->
    <view class="pq-tabs px-4">
      <view class="pq-tabs__inner">
        <view
          v-for="tab in TABS"
          :key="tab.key"
          class="pq-tab"
          :class="{ 'pq-tab--active': activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text>{{ tab.label }}</text>
          <text class="pq-tab__count" v-if="tab.key === 'pending' && pendingTotal > 0">{{ pendingTotal }}</text>
        </view>
      </view>
    </view>

    <!-- 批量操作（待审批时显示） -->
    <view class="pq-batch px-4" v-if="activeTab === 'pending' && items.length > 1">
      <view class="pq-batch__bar">
        <text class="text-xs text-secondary-color">共 {{ pendingTotal }} 条待审批</text>
        <view class="pq-batch__btn" @tap="approveAll">
          <text class="text-xs">全部审批通过</text>
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <view class="pq-list px-4">

      <template v-if="loading">
        <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 160rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="items.length">
        <view
          v-for="item in items"
          :key="item.id"
          class="pq-item bhp-card bhp-card--flat"
          :class="{ 'pq-item--processing': processingId === item.id }"
        >
          <!-- 头部：目标用户 + 类型 + 时间 -->
          <view class="pq-item__header">
            <view class="pq-item__user-row">
              <view class="pq-item__avatar">
                <text>{{ (item.target_user?.full_name || item.target_user?.username || '用')[0] }}</text>
              </view>
              <view class="pq-item__user-info">
                <text class="pq-item__user-name">{{ item.target_user?.full_name || item.target_user?.username }}</text>
                <view class="pq-type-badge" :class="`pq-type--${item.content_type}`">
                  <text>{{ CONTENT_TYPE_LABEL[item.content_type] || item.content_type }}</text>
                </view>
              </view>
              <view class="pq-item__status-badge" :class="`pq-status--${item.status}`">
                <text>{{ STATUS_LABEL[item.status] || item.status }}</text>
              </view>
            </view>
            <text class="pq-item__time text-xs text-tertiary-color">{{ formatDate(item.created_at) }}</text>
          </view>

          <!-- 内容 -->
          <view class="pq-item__content">
            <view class="pq-source-tag">
              <text class="text-xs text-tertiary-color">来源：{{ SOURCE_LABEL[item.source_type] || item.source_type }}</text>
            </view>
            <text class="pq-item__text">{{ item.content }}</text>
          </view>

          <!-- 操作（仅待审批） -->
          <view class="pq-item__actions" v-if="activeTab === 'pending' && item.status === 'pending'">
            <view class="pq-reject-btn" @tap="openRejectDialog(item)">
              <text>拒绝</text>
            </view>
            <view class="pq-approve-btn" @tap="approve(item.id)">
              <text v-if="processingId !== item.id">审批通过</text>
              <text v-else>处理中...</text>
            </view>
          </view>

          <!-- 已审批结果 -->
          <view class="pq-item__result" v-else-if="(item as any).reject_reason">
            <text class="text-xs text-secondary-color">拒绝原因：{{ (item as any).reject_reason }}</text>
          </view>
        </view>

        <!-- 加载更多 -->
        <view class="pq-load-more" v-if="hasMore" @tap="loadMore">
          <text v-if="!loadingMore">加载更多</text>
          <text v-else>加载中...</text>
        </view>
        <view class="pq-load-more pq-load-more--end" v-else-if="items.length > 0">
          <text>已显示全部</text>
        </view>
      </template>

      <view class="pq-empty" v-else-if="!loading">
        <text class="pq-empty__icon">📤</text>
        <text class="pq-empty__text">{{ activeTab === 'pending' ? '暂无待审批推送' : '暂无历史记录' }}</text>
      </view>
    </view>

    <!-- 拒绝原因弹窗 -->
    <view class="pq-overlay" v-if="rejectDialog.show" @tap.self="rejectDialog.show = false">
      <view class="pq-dialog">
        <text class="pq-dialog__title">拒绝原因</text>
        <textarea
          class="pq-dialog__input"
          v-model="rejectDialog.reason"
          placeholder="请输入拒绝原因（可选）"
          placeholder-class="pq-input-placeholder"
          :maxlength="200"
          auto-height
        />
        <view class="pq-dialog__actions">
          <view class="pq-dialog__cancel" @tap="rejectDialog.show = false">
            <text>取消</text>
          </view>
          <view class="pq-dialog__confirm" @tap="confirmReject">
            <text v-if="!processingReject">确认拒绝</text>
            <text v-else>处理中...</text>
          </view>
        </view>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { pushQueueApi, type PushHistoryItem } from '@/api/coach'
import type { PushQueueItem } from '@/stores/coach'
import { useCoachStore } from '@/stores/coach'

const coachStore = useCoachStore()

type TabKey = 'pending' | 'history'

const TABS: { key: TabKey; label: string }[] = [
  { key: 'pending', label: '待审批' },
  { key: 'history', label: '历史记录' },
]

const CONTENT_TYPE_LABEL: Record<string, string> = {
  advice: '建议', encouragement: '鼓励', reminder: '提醒', warning: '警示',
  article: '文章', video: '视频', message: '消息'
}
const SOURCE_LABEL: Record<string, string> = {
  ai_recommendation: 'AI推荐', coach_manual: '教练手动', system: '系统'
}
const STATUS_LABEL: Record<string, string> = {
  pending: '待审批', approved: '已批准', rejected: '已拒绝', delivered: '已推送'
}

const activeTab    = ref<TabKey>('pending')
const items        = ref<(PushQueueItem | PushHistoryItem)[]>([])
const loading      = ref(false)
const loadingMore  = ref(false)
const page         = ref(1)
const hasMore      = ref(true)
const pendingTotal = ref(0)
const processingId = ref<number | null>(null)

const rejectDialog = reactive({ show: false, id: 0, reason: '' })
const processingReject = ref(false)

onMounted(() => loadData(true))

async function switchTab(key: TabKey) {
  if (key === activeTab.value) return
  activeTab.value = key
  await loadData(true)
}

async function loadData(reset = false) {
  if (reset) { page.value = 1; items.value = []; hasMore.value = true }
  if (!hasMore.value) return
  reset ? (loading.value = true) : (loadingMore.value = true)
  try {
    if (activeTab.value === 'pending') {
      const resp = await pushQueueApi.pending({ page: page.value })
      const newItems = resp.items || []
      items.value = reset ? newItems : [...items.value, ...newItems]
      pendingTotal.value = resp.total || 0
      hasMore.value = newItems.length === 20
    } else {
      const resp = await pushQueueApi.history({ page: page.value })
      const newItems = resp.items || []
      items.value = reset ? newItems : [...items.value, ...newItems]
      hasMore.value = newItems.length === 20
    }
    page.value++
  } catch { if (reset) items.value = [] } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() { loadData(false) }

async function approve(id: number) {
  if (processingId.value) return
  processingId.value = id
  try {
    await coachStore.approvePush(id)
    items.value = items.value.filter(i => i.id !== id)
    pendingTotal.value = Math.max(0, pendingTotal.value - 1)
    uni.showToast({ title: '已审批通过', icon: 'success' })
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    processingId.value = null
  }
}

function openRejectDialog(item: PushQueueItem) {
  rejectDialog.id = item.id
  rejectDialog.reason = ''
  rejectDialog.show = true
}

async function confirmReject() {
  if (processingReject.value) return
  processingReject.value = true
  try {
    await coachStore.rejectPush(rejectDialog.id, rejectDialog.reason)
    items.value = items.value.filter(i => i.id !== rejectDialog.id)
    pendingTotal.value = Math.max(0, pendingTotal.value - 1)
    rejectDialog.show = false
    uni.showToast({ title: '已拒绝', icon: 'none' })
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    processingReject.value = false
  }
}

async function approveAll() {
  uni.showModal({
    title: '批量审批',
    content: `确认通过全部 ${items.value.length} 条待审批推送？`,
    confirmText: '全部通过',
    success: async (res) => {
      if (!res.confirm) return
      const pending = items.value.filter(i => i.status === 'pending')
      for (const item of pending) {
        try { await coachStore.approvePush(item.id) } catch { }
      }
      items.value = []
      pendingTotal.value = 0
      uni.showToast({ title: '批量审批完成', icon: 'success' })
    }
  })
}

function formatDate(s: string): string {
  if (!s) return ''
  try {
    const d = new Date(s)
    return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch { return s }
}
</script>

<style scoped>
.pq-page { background: var(--surface-secondary); min-height: 100vh; }

/* Tab */
.pq-tabs { padding-top: 16rpx; }
.pq-tabs__inner {
  display: flex; background: var(--surface);
  border-radius: var(--radius-full); padding: 6rpx;
  border: 1px solid var(--border-light); gap: 4rpx;
}
.pq-tab {
  flex: 1; text-align: center; padding: 10rpx 8rpx;
  border-radius: var(--radius-full);
  font-size: 26rpx; color: var(--text-secondary); cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8rpx;
}
.pq-tab--active { background: var(--bhp-primary-500); color: #fff; font-weight: 600; }
.pq-tab__count {
  background: #ff4d4f; color: #fff;
  font-size: 18rpx; padding: 0 8rpx;
  border-radius: var(--radius-full); min-width: 28rpx; text-align: center;
}

/* 批量 */
.pq-batch { padding-top: 8rpx; }
.pq-batch__bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12rpx 16rpx;
  background: var(--bhp-warn-50, #fffbeb);
  border-radius: var(--radius-lg);
  border: 1px solid var(--bhp-warn-200, #fde68a);
}
.pq-batch__btn {
  background: var(--bhp-success-500, #22c55e); color: #fff;
  padding: 6rpx 20rpx; border-radius: var(--radius-full);
  font-size: 22rpx; font-weight: 600; cursor: pointer;
}
.pq-batch__btn:active { opacity: 0.8; }

/* 列表 */
.pq-list { padding-top: 12rpx; }
.pq-item {
  padding: 20rpx 24rpx; margin-bottom: 12rpx;
  transition: opacity 0.2s;
}
.pq-item--processing { opacity: 0.6; }

.pq-item__header { margin-bottom: 14rpx; }
.pq-item__user-row { display: flex; align-items: center; gap: 14rpx; margin-bottom: 6rpx; }
.pq-item__avatar {
  width: 56rpx; height: 56rpx; border-radius: 50%;
  background: var(--bhp-primary-100, #d1fae5);
  display: flex; align-items: center; justify-content: center;
  font-size: 24rpx; color: var(--bhp-primary-700, #047857); font-weight: 700;
  flex-shrink: 0;
}
.pq-item__user-info { flex: 1; }
.pq-item__user-name { display: block; font-size: 26rpx; font-weight: 600; color: var(--text-primary); margin-bottom: 4rpx; }
.pq-type-badge {
  display: inline-block; font-size: 18rpx; font-weight: 600;
  padding: 2rpx 10rpx; border-radius: var(--radius-full);
}
.pq-type--advice        { background: var(--bhp-primary-50); color: var(--bhp-primary-600); }
.pq-type--encouragement { background: #fff7e6; color: #d97706; }
.pq-type--reminder      { background: var(--bhp-gray-100); color: var(--text-secondary); }
.pq-type--warning       { background: #fff1f0; color: #cf1322; }
.pq-type--article, .pq-type--video { background: #e6f7ff; color: #096dd9; }
.pq-item__status-badge {
  font-size: 20rpx; font-weight: 600;
  padding: 4rpx 14rpx; border-radius: var(--radius-full);
}
.pq-status--pending  { background: var(--bhp-warn-50); color: var(--bhp-warn-700, #b45309); }
.pq-status--approved { background: var(--bhp-success-50); color: var(--bhp-success-700, #15803d); }
.pq-status--rejected { background: var(--bhp-error-50, #fef2f2); color: var(--bhp-error-700, #b91c1c); }
.pq-status--delivered { background: var(--bhp-primary-50); color: var(--bhp-primary-600); }

.pq-item__content { margin-bottom: 16rpx; }
.pq-source-tag { margin-bottom: 8rpx; }
.pq-item__text { font-size: 26rpx; color: var(--text-primary); line-height: 1.5; }

.pq-item__actions { display: flex; gap: 12rpx; justify-content: flex-end; }
.pq-reject-btn {
  padding: 12rpx 28rpx; border-radius: var(--radius-full);
  background: var(--bhp-gray-100); color: var(--text-secondary);
  font-size: 24rpx; font-weight: 600; cursor: pointer;
}
.pq-reject-btn:active { opacity: 0.8; }
.pq-approve-btn {
  padding: 12rpx 28rpx; border-radius: var(--radius-full);
  background: var(--bhp-success-500, #22c55e); color: #fff;
  font-size: 24rpx; font-weight: 600; cursor: pointer;
}
.pq-approve-btn:active { opacity: 0.8; }

.pq-item__result { padding-top: 10rpx; border-top: 1px solid var(--border-light); }

/* 加载更多 */
.pq-load-more { text-align: center; padding: 20rpx; font-size: 26rpx; color: var(--bhp-primary-500); cursor: pointer; }
.pq-load-more--end { color: var(--text-tertiary); }

/* 空状态 */
.pq-empty { display: flex; flex-direction: column; align-items: center; padding: 80rpx 0; gap: 16rpx; }
.pq-empty__icon { font-size: 80rpx; }
.pq-empty__text { font-size: 28rpx; color: var(--text-tertiary); }

/* 弹窗 */
.pq-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 0 48rpx;
}
.pq-dialog {
  background: var(--surface); border-radius: var(--radius-xl, 24rpx);
  padding: 40rpx 32rpx; width: 100%;
}
.pq-dialog__title {
  display: block; font-size: 32rpx; font-weight: 700;
  color: var(--text-primary); text-align: center; margin-bottom: 24rpx;
}
.pq-dialog__input {
  width: 100%; min-height: 120rpx;
  background: var(--bhp-gray-50, #f9fafb);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 16rpx 20rpx; font-size: 26rpx; color: var(--text-primary);
  box-sizing: border-box; line-height: 1.6; margin-bottom: 24rpx;
}
.pq-input-placeholder { color: var(--text-tertiary); font-size: 26rpx; }
.pq-dialog__actions { display: flex; gap: 16rpx; }
.pq-dialog__cancel, .pq-dialog__confirm {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
}
.pq-dialog__cancel  { background: var(--bhp-gray-100); color: var(--text-secondary); }
.pq-dialog__confirm { background: var(--bhp-error-500, #ef4444); color: #fff; }
.pq-dialog__confirm:active { opacity: 0.8; }
</style>
