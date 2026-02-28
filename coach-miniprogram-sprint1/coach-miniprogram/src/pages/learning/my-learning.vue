<template>
  <view class="ml-page">

    <!-- 统计卡 -->
    <view class="ml-stats px-4">
      <view class="ml-stats__card bhp-card bhp-card--flat" v-if="stats">

        <!-- 三维积分 -->
        <view class="ml-stats__points-row">
          <view class="ml-stats__point-item">
            <text class="ml-stats__point-value">{{ stats.total_minutes }}</text>
            <text class="ml-stats__point-label">总学习分钟</text>
          </view>
          <view class="ml-stats__divider"></view>
          <view class="ml-stats__point-item">
            <text class="ml-stats__point-value">{{ stats.completed_count }}</text>
            <text class="ml-stats__point-label">已完成</text>
          </view>
          <view class="ml-stats__divider"></view>
          <view class="ml-stats__point-item">
            <text class="ml-stats__point-value">{{ stats.in_progress_count }}</text>
            <text class="ml-stats__point-label">进行中</text>
          </view>
        </view>

        <!-- 连续打卡 -->
        <view class="ml-streak-row">
          <view class="ml-streak__item">
            <text class="ml-streak__label">今日</text>
            <text class="ml-streak__value">{{ formatMinutes(stats.today_minutes) }}</text>
          </view>
          <view class="ml-streak__item ml-streak__item--highlight">
            <text class="ml-streak__label">🔥 连续打卡</text>
            <text class="ml-streak__value">{{ stats.current_streak }}天</text>
          </view>
          <view class="ml-streak__item">
            <text class="ml-streak__label">最长连续</text>
            <text class="ml-streak__value">{{ stats.longest_streak }}天</text>
          </view>
        </view>

        <!-- 激励文案 -->
        <view class="ml-streak-msg">
          <text class="text-xs text-secondary-color">{{ streakMsg }}</text>
        </view>
      </view>

      <!-- 骨架屏 -->
      <view v-else class="bhp-skeleton" style="height: 200rpx; border-radius: var(--radius-xl, 16px);"></view>
    </view>

    <!-- 积分明细 -->
    <view class="ml-section px-4">
      <text class="ml-section-title">积分记录</text>
      <template v-if="loadingPoints">
        <view v-for="i in 3" :key="i" class="bhp-skeleton" style="height: 80rpx; margin-bottom: 10rpx; border-radius: var(--radius-lg);"></view>
      </template>
      <template v-else-if="pointsRecords.length">
        <view
          v-for="record in pointsRecords"
          :key="record.id"
          class="ml-record bhp-card bhp-card--flat"
        >
          <view class="ml-record__icon">
            <text>{{ SOURCE_ICON[record.source] || '⭐' }}</text>
          </view>
          <view class="ml-record__body">
            <text class="ml-record__desc">{{ record.description || SOURCE_LABEL[record.source] || record.source }}</text>
            <text class="ml-record__time text-xs text-secondary-color">{{ formatDate(record.created_at) }}</text>
          </view>
          <text class="ml-record__points" :class="record.points > 0 ? 'text-success' : 'text-error'">
            {{ record.points > 0 ? '+' : '' }}{{ record.points }}
          </text>
        </view>

        <view class="ml-load-more" v-if="pointsHasMore" @tap="loadMorePoints">
          <text v-if="!loadingMorePoints">加载更多</text>
          <text v-else>加载中...</text>
        </view>
        <view class="ml-load-more ml-load-more--end" v-else>
          <text>已显示全部</text>
        </view>
      </template>
      <view class="ml-empty" v-else>
        <text class="text-secondary-color text-sm">暂无积分记录</text>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { learningApi, type LearningStats, type PointsRecord } from '@/api/learning'
import { formatMinutes, getStreakMessage } from '@/utils/level'

const stats             = ref<LearningStats | null>(null)
const loadingStats      = ref(false)
const pointsRecords     = ref<PointsRecord[]>([])
const loadingPoints     = ref(false)
const loadingMorePoints = ref(false)
const pointsPage        = ref(1)
const pointsHasMore     = ref(true)

const SOURCE_LABEL: Record<string, string> = {
  quiz:                   '测验通过',
  complete:               '完成学习',
  share:                  '分享内容',
  comment:                '发表评论',
  login:                  '每日登录',
  streak:                 '连续打卡',
  coach_mentor:           '带教学员',
  knowledge_contribution: '知识投稿'
}
const SOURCE_ICON: Record<string, string> = {
  quiz:    '📝', complete: '✅', share: '📤', comment: '💬',
  login:   '🔑', streak:   '🔥', coach_mentor: '🎓', knowledge_contribution: '📚'
}

const streakMsg = computed(() => getStreakMessage(stats.value?.current_streak || 0))

onMounted(async () => {
  await Promise.all([loadStats(), loadPoints(true)])
})

onPullDownRefresh(async () => {
  await Promise.all([loadStats(), loadPoints(true)])
  uni.stopPullDownRefresh()
})

async function loadStats() {
  loadingStats.value = true
  try {
    stats.value = await learningApi.myStats()
  } catch { /* 静默 */ } finally {
    loadingStats.value = false
  }
}

async function loadPoints(reset = false) {
  if (reset) { pointsPage.value = 1; pointsRecords.value = []; pointsHasMore.value = true }
  if (!pointsHasMore.value) return
  reset ? (loadingPoints.value = true) : (loadingMorePoints.value = true)
  try {
    const data = await learningApi.pointsHistory(pointsPage.value, 20)
    const newItems = data.items || []
    pointsRecords.value = reset ? newItems : [...pointsRecords.value, ...newItems]
    pointsHasMore.value = newItems.length === 20
    pointsPage.value++
  } catch { /* 静默 */ } finally {
    loadingPoints.value = false
    loadingMorePoints.value = false
  }
}

function loadMorePoints() { loadPoints(false) }

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    const m = d.getMonth() + 1
    const day = d.getDate()
    const h = d.getHours()
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${m}月${day}日 ${h}:${min}`
  } catch { return dateStr }
}
</script>

<style scoped>
.ml-page { background: var(--surface-secondary); min-height: 100vh; }

/* 统计卡 */
.ml-stats { padding-top: 16rpx; }
.ml-stats__points-row {
  display: flex;
  align-items: center;
  padding-bottom: 20rpx;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 20rpx;
}
.ml-stats__point-item { flex: 1; text-align: center; }
.ml-stats__point-value { display: block; font-size: 40rpx; font-weight: 700; color: var(--text-primary); }
.ml-stats__point-label { display: block; font-size: 20rpx; color: var(--text-secondary); margin-top: 4rpx; }
.ml-stats__divider { width: 1px; height: 50rpx; background: var(--border-light); }

.ml-streak-row {
  display: flex;
  align-items: center;
  gap: 0;
  justify-content: space-between;
}
.ml-streak__item { text-align: center; flex: 1; }
.ml-streak__item--highlight {
  background: var(--bhp-warn-50, #fffbeb);
  border-radius: var(--radius-lg);
  padding: 12rpx;
}
.ml-streak__label { display: block; font-size: 20rpx; color: var(--text-secondary); }
.ml-streak__value { display: block; font-size: 32rpx; font-weight: 700; color: var(--text-primary); }

.ml-streak-msg { margin-top: 16rpx; text-align: center; }

/* 区块 */
.ml-section { padding-top: 24rpx; }
.ml-section-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16rpx;
}

/* 记录条目 */
.ml-record {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 20rpx;
  margin-bottom: 10rpx;
}
.ml-record__icon { font-size: 36rpx; }
.ml-record__body { flex: 1; overflow: hidden; }
.ml-record__desc { display: block; font-size: 26rpx; color: var(--text-primary); }
.ml-record__time { display: block; margin-top: 4rpx; }
.ml-record__points { font-size: 28rpx; font-weight: 700; }
.text-success { color: var(--bhp-success-500, #22c55e); }
.text-error   { color: var(--bhp-error-500, #ef4444); }

.ml-load-more {
  text-align: center;
  padding: 20rpx;
  font-size: 26rpx;
  color: var(--bhp-primary-500);
  cursor: pointer;
}
.ml-load-more--end { color: var(--text-tertiary); }

.ml-empty { padding: 40rpx 0; text-align: center; }
</style>
