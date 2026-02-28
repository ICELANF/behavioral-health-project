<template>
  <view class="history-page">

    <!-- 统计摘要 -->
    <view class="history-summary px-4" v-if="summary.total > 0">
      <view class="history-summary__card bhp-card bhp-card--flat">
        <view class="history-summary__item">
          <text class="history-summary__val">{{ summary.total }}</text>
          <text class="history-summary__lbl">总考次</text>
        </view>
        <view class="history-summary__divider"></view>
        <view class="history-summary__item">
          <text class="history-summary__val" style="color: var(--bhp-success-500);">{{ summary.passed }}</text>
          <text class="history-summary__lbl">通过</text>
        </view>
        <view class="history-summary__divider"></view>
        <view class="history-summary__item">
          <text class="history-summary__val">{{ summary.bestScore }}</text>
          <text class="history-summary__lbl">最高分</text>
        </view>
        <view class="history-summary__divider"></view>
        <view class="history-summary__item">
          <text class="history-summary__val">{{ summary.avgScore }}</text>
          <text class="history-summary__lbl">平均分</text>
        </view>
      </view>
    </view>

    <!-- 筛选 Tab -->
    <view class="history-filter px-4">
      <view class="history-filter__inner">
        <view
          v-for="tab in filterTabs"
          :key="tab.key"
          class="history-filter__tab"
          :class="{ 'history-filter__tab--active': activeFilter === tab.key }"
          @tap="setFilter(tab.key)"
        >
          <text>{{ tab.label }}</text>
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <view class="history-list px-4">

      <!-- 骨架屏 -->
      <template v-if="loading">
        <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 100rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else>
        <view
          v-for="item in filteredItems"
          :key="item.id"
          class="history-item bhp-card bhp-card--flat"
          @tap="goDetail(item)"
        >
          <!-- 左：通过/失败标识 -->
          <view class="history-item__status-dot" :class="item.pass ? 'history-item__status-dot--pass' : 'history-item__status-dot--fail'">
            <text>{{ item.pass ? '✓' : '✗' }}</text>
          </view>

          <!-- 中：信息 -->
          <view class="history-item__body">
            <text class="history-item__title">{{ item.exam_title || '认证考试' }}</text>
            <view class="history-item__meta flex-start gap-3 mt-1">
              <text class="text-xs text-secondary-color">{{ formatDate(item.completed_at) }}</text>
              <text class="text-xs text-secondary-color" v-if="item.time_spent_seconds">
                用时 {{ formatDuration(item.time_spent_seconds) }}
              </text>
              <text
                class="text-xs font-semibold"
                :class="item.pass ? 'text-success-color' : 'text-fail-color'"
              >
                {{ item.pass ? '通过' : `差${(item.pass_score || 60) - item.score}分` }}
              </text>
            </view>
          </view>

          <!-- 右：分数 -->
          <view class="history-item__score-wrap">
            <text
              class="history-item__score"
              :class="item.pass ? 'history-item__score--pass' : 'history-item__score--fail'"
            >
              {{ item.score }}
            </text>
            <text class="history-item__score-unit">分</text>
          </view>
        </view>

        <!-- 加载更多 -->
        <view class="history-load-more" v-if="hasMore" @tap="loadMore">
          <text v-if="!loadingMore">加载更多</text>
          <text v-else>加载中...</text>
        </view>
        <view class="history-load-more history-load-more--end" v-else-if="items.length > 0">
          <text>已显示全部</text>
        </view>

        <!-- 空状态 -->
        <view class="history-empty" v-if="!loading && !filteredItems.length">
          <text class="history-empty__icon">📋</text>
          <text class="history-empty__text">
            {{ activeFilter === 'all' ? '暂无考试记录' : activeFilter === 'pass' ? '暂无通过记录' : '暂无未通过记录' }}
          </text>
          <view class="bhp-btn bhp-btn--primary mt-4" @tap="goExamHome">
            <text>去参加考试</text>
          </view>
        </view>
      </template>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { certExamApi, type ExamHistoryItem } from '@/api/exam'

const items        = ref<ExamHistoryItem[]>([])
const loading      = ref(false)
const loadingMore  = ref(false)
const page         = ref(1)
const hasMore      = ref(true)
const activeFilter = ref<'all' | 'pass' | 'fail'>('all')

const filterTabs = [
  { key: 'all',  label: '全部' },
  { key: 'pass', label: '已通过' },
  { key: 'fail', label: '未通过' },
]

const filteredItems = computed(() => {
  if (activeFilter.value === 'all')  return items.value
  if (activeFilter.value === 'pass') return items.value.filter(i => i.pass)
  return items.value.filter(i => !i.pass)
})

const summary = computed(() => {
  const total     = items.value.length
  const passed    = items.value.filter(i => i.pass).length
  const scores    = items.value.map(i => i.score)
  const bestScore = scores.length ? Math.max(...scores) : 0
  const avgScore  = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0
  return { total, passed, bestScore, avgScore }
})

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
    const data = await certExamApi.history(page.value, 20)
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
function setFilter(key: 'all' | 'pass' | 'fail') { activeFilter.value = key }

function goDetail(item: ExamHistoryItem) {
  if (!item.id) return
  uni.navigateTo({ url: `/pages/exam/result?session_id=${item.id}&score=${item.score}&pass=${item.pass ? 1 : 0}&pass_score=${item.pass_score || 60}&correct_count=0&total_count=0` })
}

function goExamHome() {
  uni.navigateBack()
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch { return dateStr }
}

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}分${s}秒`
}
</script>

<style scoped>
.history-page { background: var(--surface-secondary); min-height: 100vh; }

/* 统计摘要 */
.history-summary { padding-top: 16rpx; }
.history-summary__card {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
}
.history-summary__item { flex: 1; text-align: center; }
.history-summary__val { display: block; font-size: 36rpx; font-weight: 700; color: var(--text-primary); }
.history-summary__lbl { display: block; font-size: 20rpx; color: var(--text-secondary); margin-top: 4rpx; }
.history-summary__divider { width: 1px; height: 48rpx; background: var(--border-light); }

/* 筛选 Tab */
.history-filter { padding-top: 16rpx; }
.history-filter__inner {
  display: flex;
  background: var(--surface);
  border-radius: var(--radius-full);
  padding: 6rpx;
  border: 1px solid var(--border-light);
}
.history-filter__tab {
  flex: 1;
  text-align: center;
  padding: 12rpx;
  border-radius: var(--radius-full);
  font-size: 26rpx;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.history-filter__tab--active {
  background: var(--bhp-primary-500);
  color: #fff;
  font-weight: 600;
}

/* 列表 */
.history-list { padding-top: 16rpx; }
.history-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 20rpx;
  margin-bottom: 10rpx;
  cursor: pointer;
}
.history-item:active { opacity: 0.8; }

.history-item__status-dot {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 700;
  flex-shrink: 0;
}
.history-item__status-dot--pass { background: var(--bhp-success-100, #dcfce7); color: var(--bhp-success-600, #16a34a); }
.history-item__status-dot--fail { background: var(--bhp-error-100, #fee2e2);   color: var(--bhp-error-500, #ef4444); }

.history-item__body { flex: 1; overflow: hidden; }
.history-item__title { display: block; font-size: 28rpx; font-weight: 500; color: var(--text-primary); }

.text-success-color { color: var(--bhp-success-500, #22c55e); }
.text-fail-color    { color: var(--bhp-error-500, #ef4444); }

.history-item__score-wrap { text-align: right; }
.history-item__score {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1;
}
.history-item__score--pass { color: var(--bhp-success-500, #22c55e); }
.history-item__score--fail { color: var(--bhp-error-500, #ef4444); }
.history-item__score-unit  { font-size: 20rpx; color: var(--text-tertiary); }

/* 加载更多 */
.history-load-more {
  text-align: center;
  padding: 20rpx;
  font-size: 26rpx;
  color: var(--bhp-primary-500);
  cursor: pointer;
}
.history-load-more--end { color: var(--text-tertiary); }

/* 空状态 */
.history-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
  gap: 16rpx;
}
.history-empty__icon { font-size: 80rpx; }
.history-empty__text { font-size: 28rpx; color: var(--text-tertiary); }
</style>
