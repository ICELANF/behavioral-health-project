<template>
  <view class="pending-page">

    <!-- 状态 Tab -->
    <view class="ap-tabs px-4">
      <view class="ap-tabs__inner">
        <view
          v-for="tab in TABS"
          :key="tab.key"
          class="ap-tab"
          :class="{ 'ap-tab--active': activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text>{{ tab.label }}</text>
          <text class="ap-tab__count" v-if="tab.key === 'pending' && pendingCount > 0">{{ pendingCount }}</text>
        </view>
      </view>
    </view>

    <!-- 说明卡（待完成时显示） -->
    <view class="ap-info px-4" v-if="activeTab === 'pending' && !loading && items.length">
      <view class="ap-info__card">
        <text class="ap-info__icon">📋</text>
        <text class="ap-info__text">您的教练已为您分配了评估任务，完成评估有助于制定个性化健康方案</text>
      </view>
    </view>

    <!-- 列表 -->
    <view class="ap-list px-4">

      <!-- 骨架屏 -->
      <template v-if="loading">
        <view v-for="i in 4" :key="i" class="bhp-skeleton" style="height: 140rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="items.length">
        <view
          v-for="item in items"
          :key="item.id"
          class="ap-item bhp-card bhp-card--flat"
          :class="{
            'ap-item--urgent': isUrgent(item),
            'ap-item--done':   item.status === 'reviewed'
          }"
          @tap="handleTap(item)"
        >
          <!-- 顶部：类型图标 + 标题 + 状态 -->
          <view class="ap-item__header">
            <view class="ap-item__type-icon" :style="{ background: typeColor(item.assessment_type) + '20' }">
              <text :style="{ color: typeColor(item.assessment_type) }">{{ TYPE_ICON[item.assessment_type] || '📋' }}</text>
            </view>
            <view class="ap-item__title-col">
              <text class="ap-item__title">{{ item.assessment_title }}</text>
              <view class="ap-type-badge" :style="{ background: typeColor(item.assessment_type) + '15', color: typeColor(item.assessment_type) }">
                <text>{{ TYPE_LABEL[item.assessment_type] || item.assessment_type }}</text>
              </view>
            </view>
            <view class="ap-status-badge" :class="`ap-status--${statusKey(item)}`">
              <text>{{ STATUS_LABEL[statusKey(item)] }}</text>
            </view>
          </view>

          <!-- 元信息 -->
          <view class="ap-item__meta">
            <text class="text-xs text-secondary-color">
              由 {{ item.assigned_by || '教练' }} 分配 · {{ formatDate(item.assigned_at) }}
            </text>
            <text class="text-xs" v-if="item.question_count">
              共 {{ item.question_count }} 题
              <text v-if="item.estimated_minutes"> · 约 {{ item.estimated_minutes }} 分钟</text>
            </text>
          </view>

          <!-- 截止日期警告 -->
          <view class="ap-item__due" v-if="item.due_date && item.status !== 'submitted' && item.status !== 'reviewed'">
            <text
              class="text-xs"
              :class="isUrgent(item) ? 'text-error-color' : 'text-tertiary-color'"
            >
              {{ isUrgent(item) ? '⚠️ ' : '📅 ' }}截止 {{ formatDate(item.due_date) }}
              {{ daysLeft(item.due_date) }}
            </text>
          </view>

          <!-- 底部行动提示 -->
          <view class="ap-item__action">
            <template v-if="item.status === 'assigned'">
              <view class="ap-action-btn ap-action-btn--start">
                <text>开始评估 →</text>
              </view>
            </template>
            <template v-else-if="item.status === 'in_progress'">
              <view class="ap-action-btn ap-action-btn--continue">
                <text>继续作答 →</text>
              </view>
            </template>
            <template v-else-if="item.status === 'submitted'">
              <text class="text-xs text-secondary-color">已提交，等待教练审核</text>
            </template>
            <template v-else-if="item.status === 'reviewed'">
              <view class="ap-action-btn ap-action-btn--result">
                <text>查看结果 →</text>
              </view>
            </template>
          </view>
        </view>

        <!-- 加载更多 -->
        <view class="ap-load-more" v-if="hasMore" @tap="loadMore">
          <text v-if="!loadingMore">加载更多</text>
          <text v-else>加载中...</text>
        </view>
        <view class="ap-load-more ap-load-more--end" v-else-if="items.length >= 5">
          <text>已显示全部</text>
        </view>
      </template>

      <!-- 空状态 -->
      <view class="ap-empty" v-else-if="!loading">
        <text class="ap-empty__icon">{{ activeTab === 'pending' ? '✅' : '📋' }}</text>
        <text class="ap-empty__title">
          {{ activeTab === 'pending' ? '暂无待完成评估' : '暂无已完成评估' }}
        </text>
        <text class="ap-empty__sub text-secondary-color" v-if="activeTab === 'pending'">
          教练会为您分配适合的评估任务
        </text>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { myAssessmentApi, type MyAssignment, type AssignmentStatus } from '@/api/assessment'

type TabKey = 'pending' | 'done'

const TABS: { key: TabKey; label: string }[] = [
  { key: 'pending', label: '待完成' },
  { key: 'done',    label: '已完成' },
]

const TYPE_LABEL: Record<string, string> = {
  baps: 'BAPS行为评估', survey: '问卷调查', health_check: '健康检查',
  phq9: 'PHQ-9抑郁筛查', gad7: 'GAD-7焦虑筛查', custom: '自定义评估'
}
const TYPE_ICON: Record<string, string> = {
  baps: '🧠', survey: '📝', health_check: '🏥',
  phq9: '💭', gad7: '😰', custom: '📋'
}
const TYPE_COLORS: Record<string, string> = {
  baps: '#722ed1', survey: '#1890ff', health_check: '#52c41a',
  phq9: '#eb2f96', gad7: '#fa8c16', custom: '#8c8c8c'
}
const STATUS_LABEL: Record<string, string> = {
  assigned:    '待开始',
  in_progress: '进行中',
  submitted:   '待审核',
  reviewed:    '已审核',
}

const activeTab   = ref<TabKey>('pending')
const items       = ref<MyAssignment[]>([])
const loading     = ref(false)
const loadingMore = ref(false)
const page        = ref(1)
const hasMore     = ref(true)

const pendingCount = computed(() =>
  items.value.filter(i => i.status === 'assigned' || i.status === 'in_progress').length
)

onMounted(() => loadData(true))

onPullDownRefresh(async () => {
  await loadData(true)
  uni.stopPullDownRefresh()
})

async function switchTab(key: TabKey) {
  if (key === activeTab.value) return
  activeTab.value = key
  await loadData(true)
}

async function loadData(reset = false) {
  if (reset) { page.value = 1; items.value = []; hasMore.value = true }
  if (!hasMore.value) return
  reset ? (loading.value = true) : (loadingMore.value = true)

  // 根据 tab 确定 status 过滤
  const statusFilter: AssignmentStatus[] =
    activeTab.value === 'pending'
      ? ['assigned', 'in_progress', 'submitted']
      : ['reviewed']

  try {
    // 分别请求每个状态（如果后端支持多状态过滤可合并）
    if (activeTab.value === 'pending') {
      const resp = await myAssessmentApi.myList({ page: page.value, page_size: 20 })
      const all = resp.items || []
      const filtered = all.filter(i => statusFilter.includes(i.status))
      items.value = reset ? filtered : [...items.value, ...filtered]
      hasMore.value = (resp.items || []).length === 20
    } else {
      const resp = await myAssessmentApi.myList({
        status: 'reviewed', page: page.value, page_size: 20
      })
      const newItems = resp.items || []
      items.value = reset ? newItems : [...items.value, ...newItems]
      hasMore.value = newItems.length === 20
    }
    page.value++
  } catch {
    if (reset) items.value = []
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() { loadData(false) }

function statusKey(item: MyAssignment): string {
  return item.status
}

function typeColor(type: string): string {
  return TYPE_COLORS[type] || '#8c8c8c'
}

function isUrgent(item: MyAssignment): boolean {
  if (!item.due_date || item.status === 'submitted' || item.status === 'reviewed') return false
  const diff = new Date(item.due_date).getTime() - Date.now()
  return diff > 0 && diff < 86400000 * 2  // 2天内截止
}

function daysLeft(dueDateStr: string): string {
  try {
    const diff = new Date(dueDateStr).getTime() - Date.now()
    if (diff < 0) return '（已超时）'
    const days = Math.ceil(diff / 86400000)
    if (days === 0) return '（今天截止）'
    if (days === 1) return '（明天截止）'
    return `（还剩${days}天）`
  } catch { return '' }
}

function formatDate(s: string): string {
  if (!s) return ''
  try {
    const d = new Date(s)
    return `${d.getMonth() + 1}/${d.getDate()}`
  } catch { return s }
}

function handleTap(item: MyAssignment) {
  if (item.status === 'reviewed') {
    uni.navigateTo({ url: `/pages/assessment/result?id=${item.id}` })
  } else {
    uni.navigateTo({ url: `/pages/assessment/do?id=${item.id}` })
  }
}
</script>

<style scoped>
.pending-page { background: var(--surface-secondary); min-height: 100vh; }

/* Tabs */
.ap-tabs { padding-top: 16rpx; }
.ap-tabs__inner {
  display: flex; background: var(--surface);
  border-radius: var(--radius-full); padding: 6rpx;
  border: 1px solid var(--border-light); gap: 4rpx;
}
.ap-tab {
  flex: 1; text-align: center; padding: 10rpx 8rpx;
  border-radius: var(--radius-full);
  font-size: 26rpx; color: var(--text-secondary); cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8rpx;
}
.ap-tab--active { background: var(--bhp-primary-500); color: #fff; font-weight: 600; }
.ap-tab__count {
  background: #ff4d4f; color: #fff;
  font-size: 18rpx; padding: 0 8rpx;
  border-radius: var(--radius-full); min-width: 28rpx; text-align: center;
}

/* 说明卡 */
.ap-info { padding-top: 12rpx; }
.ap-info__card {
  display: flex; align-items: flex-start; gap: 12rpx;
  background: var(--bhp-primary-50);
  border-radius: var(--radius-lg); padding: 16rpx 20rpx;
}
.ap-info__icon { font-size: 28rpx; flex-shrink: 0; }
.ap-info__text { font-size: 22rpx; color: var(--bhp-primary-600, #059669); line-height: 1.5; }

/* 列表 */
.ap-list { padding-top: 12rpx; }
.ap-item {
  padding: 20rpx 24rpx; margin-bottom: 12rpx; cursor: pointer;
  border-left: 4rpx solid transparent;
  transition: opacity 0.2s;
}
.ap-item:active { opacity: 0.8; }
.ap-item--urgent { border-left-color: #ff4d4f; }
.ap-item--done   { opacity: 0.85; }

/* 头部 */
.ap-item__header { display: flex; align-items: flex-start; gap: 14rpx; margin-bottom: 12rpx; }
.ap-item__type-icon {
  width: 72rpx; height: 72rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 32rpx; flex-shrink: 0;
}
.ap-item__title-col { flex: 1; display: flex; flex-direction: column; gap: 8rpx; }
.ap-item__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); line-height: 1.4; }
.ap-type-badge {
  display: inline-block; font-size: 18rpx; font-weight: 600;
  padding: 2rpx 10rpx; border-radius: var(--radius-full);
  align-self: flex-start;
}
.ap-status-badge {
  font-size: 20rpx; font-weight: 600; flex-shrink: 0;
  padding: 4rpx 14rpx; border-radius: var(--radius-full);
}
.ap-status--assigned    { background: var(--bhp-gray-100); color: var(--text-secondary); }
.ap-status--in_progress { background: #e6f7ff; color: #096dd9; }
.ap-status--submitted   { background: var(--bhp-warn-50, #fffbeb); color: var(--bhp-warn-700, #b45309); }
.ap-status--reviewed    { background: var(--bhp-success-50); color: var(--bhp-success-700, #15803d); }

/* 元信息 */
.ap-item__meta { display: flex; flex-direction: column; gap: 4rpx; margin-bottom: 8rpx; }
.ap-item__due  { margin-bottom: 12rpx; }

/* 行动按钮 */
.ap-item__action { display: flex; justify-content: flex-end; padding-top: 10rpx; border-top: 1px solid var(--border-light); }
.ap-action-btn {
  font-size: 24rpx; font-weight: 600;
  padding: 8rpx 24rpx; border-radius: var(--radius-full);
}
.ap-action-btn--start    { background: var(--bhp-primary-500); color: #fff; }
.ap-action-btn--continue { background: #1890ff; color: #fff; }
.ap-action-btn--result   { background: var(--bhp-success-500, #22c55e); color: #fff; }

/* 加载更多 */
.ap-load-more { text-align: center; padding: 20rpx; font-size: 26rpx; color: var(--bhp-primary-500); cursor: pointer; }
.ap-load-more--end { color: var(--text-tertiary); }

/* 空状态 */
.ap-empty { display: flex; flex-direction: column; align-items: center; padding: 80rpx 0; gap: 16rpx; }
.ap-empty__icon  { font-size: 80rpx; }
.ap-empty__title { font-size: 28rpx; color: var(--text-tertiary); }
.ap-empty__sub   { font-size: 24rpx; text-align: center; padding: 0 48rpx; line-height: 1.6; }

/* 工具类 */
.text-error-color { color: var(--bhp-error-500, #ef4444); }
</style>
