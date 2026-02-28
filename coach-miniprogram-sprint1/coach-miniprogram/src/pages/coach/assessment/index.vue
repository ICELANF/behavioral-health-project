<template>
  <view class="assess-page">

    <!-- 状态 Tab -->
    <view class="assess-tabs px-4">
      <view class="assess-tabs__inner">
        <view
          v-for="tab in TABS"
          :key="tab.key"
          class="assess-tab"
          :class="{ 'assess-tab--active': activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text>{{ tab.label }}</text>
          <text class="assess-tab__count" v-if="tab.key === 'submitted' && pendingCount > 0">{{ pendingCount }}</text>
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <view class="assess-list px-4">

      <template v-if="loading">
        <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 130rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="items.length">
        <view
          v-for="item in items"
          :key="item.id"
          class="assess-item bhp-card bhp-card--flat"
          @tap="goReview(item)"
        >
          <!-- 头部：学员 + 状态 -->
          <view class="assess-item__header">
            <view class="assess-item__avatar">
              <text>{{ (item.student_name || '用')[0] }}</text>
            </view>
            <view class="assess-item__info">
              <text class="assess-item__student">{{ item.student_name || `学员${item.student_id}` }}</text>
              <view class="assess-item__role-tag" v-if="item.student_role">
                <text>{{ ROLE_LABEL[item.student_role] || item.student_role }}</text>
              </view>
            </view>
            <view class="assess-status" :class="`assess-status--${item.status}`">
              <text>{{ STATUS_LABEL[item.status] }}</text>
            </view>
          </view>

          <!-- 评估信息 -->
          <view class="assess-item__body">
            <text class="assess-item__title">{{ item.assessment_title }}</text>
            <view class="assess-item__meta">
              <view class="assess-type-badge">
                <text>{{ TYPE_LABEL[item.assessment_type] || item.assessment_type }}</text>
              </view>
              <text class="text-xs text-secondary-color" v-if="item.submitted_at">
                提交于 {{ formatDate(item.submitted_at) }}
              </text>
              <text class="text-xs text-secondary-color" v-if="item.score != null">
                · 得分 {{ item.score }}
              </text>
            </view>
          </view>

          <!-- 底部：操作提示 -->
          <view class="assess-item__footer">
            <text class="text-xs text-primary-color" v-if="item.status === 'submitted'">
              点击审核 →
            </text>
            <text class="text-xs text-secondary-color" v-else-if="item.status === 'reviewed'">
              已审核 {{ formatDate(item.reviewed_at || '') }}
            </text>
            <text class="text-xs text-tertiary-color" v-else>
              {{ item.status === 'assigned' ? '学员未开始' : '进行中' }}
            </text>
          </view>
        </view>

        <!-- 加载更多 -->
        <view class="assess-load-more" v-if="hasMore" @tap="loadMore">
          <text v-if="!loadingMore">加载更多</text>
          <text v-else>加载中...</text>
        </view>
        <view class="assess-load-more assess-load-more--end" v-else>
          <text>已显示全部</text>
        </view>
      </template>

      <view class="assess-empty" v-else-if="!loading">
        <text class="assess-empty__icon">📋</text>
        <text class="assess-empty__text">{{ activeTab === 'submitted' ? '暂无待审核评估' : '暂无记录' }}</text>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { assignmentApi, type AssessmentAssignment } from '@/api/coach'

type TabKey = 'submitted' | 'reviewed' | 'assigned'

const TABS: { key: TabKey; label: string }[] = [
  { key: 'submitted', label: '待审核' },
  { key: 'reviewed',  label: '已审核' },
  { key: 'assigned',  label: '已分配' },
]

const STATUS_LABEL: Record<string, string> = {
  assigned: '未开始', in_progress: '进行中', submitted: '待审核', reviewed: '已审核'
}
const TYPE_LABEL: Record<string, string> = {
  baps: 'BAPS评估', survey: '问卷调查', health_check: '健康检查', custom: '自定义'
}
const ROLE_LABEL: Record<string, string> = {
  observer: 'L0', grower: 'L1', sharer: 'L2',
  coach: 'L3', promoter: 'L4', supervisor: 'L4', master: 'L5'
}

const activeTab   = ref<TabKey>('submitted')
const items       = ref<AssessmentAssignment[]>([])
const loading     = ref(false)
const loadingMore = ref(false)
const page        = ref(1)
const hasMore     = ref(true)

const pendingCount = computed(() =>
  activeTab.value === 'submitted' ? items.value.length : 0
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
  try {
    const resp = await assignmentApi.list({
      status: activeTab.value,
      page: page.value,
      page_size: 20
    })
    const newItems = resp.items || []
    items.value = reset ? newItems : [...items.value, ...newItems]
    hasMore.value = newItems.length === 20
    page.value++
  } catch { if (reset) items.value = [] } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() { loadData(false) }

function goReview(item: AssessmentAssignment) {
  uni.navigateTo({
    url: `/pages/coach/assessment/review?id=${item.id}&status=${item.status}`
  })
}

function formatDate(s: string): string {
  if (!s) return ''
  try {
    const d = new Date(s)
    return `${d.getMonth() + 1}/${d.getDate()}`
  } catch { return s }
}
</script>

<style scoped>
.assess-page { background: var(--surface-secondary); min-height: 100vh; }

/* Tab */
.assess-tabs { padding-top: 16rpx; }
.assess-tabs__inner {
  display: flex; background: var(--surface);
  border-radius: var(--radius-full); padding: 6rpx;
  border: 1px solid var(--border-light); gap: 4rpx;
}
.assess-tab {
  flex: 1; text-align: center; padding: 10rpx 8rpx;
  border-radius: var(--radius-full);
  font-size: 26rpx; color: var(--text-secondary); cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8rpx;
}
.assess-tab--active { background: var(--bhp-primary-500); color: #fff; font-weight: 600; }
.assess-tab__count {
  background: #ff4d4f; color: #fff;
  font-size: 18rpx; padding: 0 8rpx;
  border-radius: var(--radius-full); min-width: 28rpx; text-align: center;
}

/* 列表 */
.assess-list { padding-top: 12rpx; }
.assess-item {
  padding: 20rpx 24rpx; margin-bottom: 12rpx; cursor: pointer;
}
.assess-item:active { opacity: 0.8; }

.assess-item__header { display: flex; align-items: center; gap: 14rpx; margin-bottom: 14rpx; }
.assess-item__avatar {
  width: 60rpx; height: 60rpx; border-radius: 50%;
  background: var(--bhp-primary-100, #d1fae5);
  display: flex; align-items: center; justify-content: center;
  font-size: 26rpx; color: var(--bhp-primary-700, #047857); font-weight: 700;
  flex-shrink: 0;
}
.assess-item__info { flex: 1; }
.assess-item__student { display: block; font-size: 26rpx; font-weight: 600; color: var(--text-primary); margin-bottom: 4rpx; }
.assess-item__role-tag {
  display: inline-block; font-size: 18rpx;
  background: var(--bhp-gray-100); color: var(--text-tertiary);
  padding: 2rpx 10rpx; border-radius: var(--radius-full);
}

.assess-status {
  font-size: 20rpx; font-weight: 600;
  padding: 4rpx 14rpx; border-radius: var(--radius-full);
}
.assess-status--submitted  { background: var(--bhp-warn-50); color: var(--bhp-warn-700, #b45309); }
.assess-status--reviewed   { background: var(--bhp-success-50); color: var(--bhp-success-700, #15803d); }
.assess-status--assigned   { background: var(--bhp-gray-100); color: var(--text-tertiary); }
.assess-status--in_progress { background: #e6f7ff; color: #096dd9; }

.assess-item__body { margin-bottom: 12rpx; }
.assess-item__title { display: block; font-size: 28rpx; font-weight: 600; color: var(--text-primary); margin-bottom: 8rpx; }
.assess-item__meta { display: flex; align-items: center; gap: 10rpx; flex-wrap: wrap; }
.assess-type-badge {
  display: inline-block; font-size: 18rpx;
  background: var(--bhp-primary-50); color: var(--bhp-primary-600, #059669);
  padding: 2rpx 10rpx; border-radius: var(--radius-full);
}

.assess-item__footer { padding-top: 10rpx; border-top: 1px solid var(--border-light); }

/* 加载更多 */
.assess-load-more { text-align: center; padding: 20rpx; font-size: 26rpx; color: var(--bhp-primary-500); cursor: pointer; }
.assess-load-more--end { color: var(--text-tertiary); }

/* 空状态 */
.assess-empty { display: flex; flex-direction: column; align-items: center; padding: 80rpx 0; gap: 16rpx; }
.assess-empty__icon { font-size: 80rpx; }
.assess-empty__text { font-size: 28rpx; color: var(--text-tertiary); }
</style>
