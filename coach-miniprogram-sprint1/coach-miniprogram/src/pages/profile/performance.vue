<template>
  <view class="perf-page">

    <!-- 刷新提示 -->
    <view class="perf-refresh px-4">
      <view class="perf-refresh__row">
        <text class="text-xs text-tertiary-color">数据实时更新</text>
        <view class="perf-refresh__btn" @tap="load">
          <text class="text-xs text-primary-color">↻ 刷新</text>
        </view>
      </view>
    </view>

    <!-- 骨架屏 -->
    <template v-if="loading">
      <view class="px-4">
        <view v-for="i in 4" :key="i" class="bhp-skeleton" style="height: 100rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </view>
    </template>

    <template v-else>
      <!-- 三维积分卡 -->
      <view class="perf-points px-4">
        <view class="perf-section-title">积分总览</view>
        <view class="perf-points__grid">
          <view class="perf-points__item" style="border-color: #52c41a20; background: #52c41a08;">
            <view class="perf-points__icon" style="background: #52c41a20;">
              <text style="color: #52c41a;">🌱</text>
            </view>
            <text class="perf-points__val" style="color: #52c41a;">{{ perf.growth_points }}</text>
            <text class="perf-points__label">成长积分</text>
          </view>
          <view class="perf-points__item" style="border-color: #1890ff20; background: #1890ff08;">
            <view class="perf-points__icon" style="background: #1890ff20;">
              <text style="color: #1890ff;">💧</text>
            </view>
            <text class="perf-points__val" style="color: #1890ff;">{{ perf.contribution_points }}</text>
            <text class="perf-points__label">贡献积分</text>
          </view>
          <view class="perf-points__item" style="border-color: #eb2f9620; background: #eb2f9608;">
            <view class="perf-points__icon" style="background: #eb2f9620;">
              <text style="color: #eb2f96;">✨</text>
            </view>
            <text class="perf-points__val" style="color: #eb2f96;">{{ perf.influence_points }}</text>
            <text class="perf-points__label">影响积分</text>
          </view>
        </view>
      </view>

      <!-- 学习数据 -->
      <view class="perf-stats px-4">
        <view class="perf-section-title">学习数据</view>
        <view class="perf-stats__grid">
          <view
            v-for="stat in statCards"
            :key="stat.label"
            class="perf-stats__card bhp-card bhp-card--flat"
          >
            <text class="perf-stats__icon">{{ stat.icon }}</text>
            <text class="perf-stats__val">{{ stat.value }}</text>
            <text class="perf-stats__label">{{ stat.label }}</text>
          </view>
        </view>
      </view>

      <!-- 连续打卡 -->
      <view class="perf-streak px-4">
        <view class="perf-streak__card bhp-card bhp-card--flat">
          <view class="perf-streak__left">
            <text class="perf-streak__fire">🔥</text>
            <view class="perf-streak__info">
              <text class="perf-streak__days">{{ perf.current_streak }}</text>
              <text class="perf-streak__unit">天连续打卡</text>
            </view>
          </view>
          <view class="perf-streak__right">
            <text class="perf-streak__hint text-xs text-secondary-color">
              历史最长 {{ perf.longest_streak }} 天
            </text>
            <view class="perf-streak__bar">
              <view
                v-for="i in 7"
                :key="i"
                class="perf-streak__dot"
                :class="{ 'perf-streak__dot--active': i <= perf.current_streak }"
              ></view>
            </view>
          </view>
        </view>
      </view>

      <!-- 本月 & 今日 -->
      <view class="perf-time px-4">
        <view class="perf-section-title">学习时长</view>
        <view class="perf-time__row">
          <view class="perf-time__card bhp-card bhp-card--flat">
            <text class="perf-time__val">{{ formatMinutes(perf.today_minutes) }}</text>
            <text class="perf-time__label">今日学习</text>
            <view class="perf-time__bar">
              <view
                class="perf-time__bar-fill"
                style="background: var(--bhp-primary-500);"
                :style="{ width: todayPct + '%' }"
              ></view>
            </view>
            <text class="text-xs text-tertiary-color">目标 30 分钟</text>
          </view>
          <view class="perf-time__card bhp-card bhp-card--flat">
            <text class="perf-time__val">{{ formatMinutes(perf.total_minutes) }}</text>
            <text class="perf-time__label">累计学习</text>
            <view class="perf-time__milestone-row">
              <view
                v-for="ms in milestones"
                :key="ms.hours"
                class="perf-time__milestone"
                :class="{ 'perf-time__milestone--done': perf.total_minutes >= ms.hours * 60 }"
              >
                <text class="text-xs">{{ ms.label }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 完成情况 -->
      <view class="perf-complete px-4">
        <view class="perf-complete__card bhp-card bhp-card--flat">
          <view class="perf-complete__item">
            <text class="perf-complete__val">{{ perf.completed_count }}</text>
            <text class="perf-complete__label">已完成内容</text>
          </view>
          <view class="perf-complete__divider"></view>
          <view class="perf-complete__item">
            <text class="perf-complete__val" style="color: var(--bhp-warn-600);">{{ avgLabel }}</text>
            <text class="perf-complete__label">日均学习</text>
          </view>
        </view>
      </view>
    </template>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { profileApi, type PerformanceSummary } from '@/api/profile'
import { learningApi } from '@/api/learning'

// 默认空数据
const EMPTY: PerformanceSummary = {
  total_minutes: 0, today_minutes: 0, current_streak: 0, longest_streak: 0,
  completed_count: 0, growth_points: 0, contribution_points: 0, influence_points: 0
}

const perf    = ref<PerformanceSummary>({ ...EMPTY })
const loading = ref(false)

const milestones = [
  { hours: 10, label: '10h' },
  { hours: 50, label: '50h' },
  { hours: 100, label: '100h' },
  { hours: 500, label: '500h' },
]

onMounted(load)

onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
})

async function load() {
  loading.value = true
  try {
    // 优先用 performance 接口，降级用 myStats
    try {
      const data = await profileApi.myPerformance()
      perf.value = { ...EMPTY, ...data }
    } catch {
      const data = await learningApi.myStats()
      perf.value = { ...EMPTY, ...data }
    }
  } catch { /* 静默 */ } finally {
    loading.value = false
  }
}

const statCards = computed(() => [
  { icon: '⏱️', value: formatMinutes(perf.value.today_minutes), label: '今日学习' },
  { icon: '📖', value: String(perf.value.completed_count), label: '完成内容' },
  { icon: '🔥', value: `${perf.value.current_streak}天`, label: '连续打卡' },
  { icon: '⏳', value: formatMinutes(perf.value.total_minutes), label: '累计学习' },
])

const todayPct = computed(() =>
  Math.min(Math.round((perf.value.today_minutes / 30) * 100), 100)
)

const avgLabel = computed(() => {
  const avg = perf.value.avg_daily_minutes
  if (avg) return formatMinutes(avg)
  // 简单估算：总分钟/30天
  return formatMinutes(Math.round(perf.value.total_minutes / 30))
})

function formatMinutes(minutes: number): string {
  if (!minutes) return '0分钟'
  if (minutes < 60) return `${minutes}分钟`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m ? `${h}h${m}m` : `${h}小时`
}
</script>

<style scoped>
.perf-page { background: var(--surface-secondary); min-height: 100vh; }

.perf-refresh { padding-top: 12rpx; padding-bottom: 4rpx; }
.perf-refresh__row { display: flex; justify-content: space-between; align-items: center; }
.perf-refresh__btn { cursor: pointer; padding: 4rpx 8rpx; }

.perf-section-title {
  font-size: 26rpx; font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12rpx;
  margin-top: 4rpx;
}

/* 三维积分 */
.perf-points { padding-top: 12rpx; }
.perf-points__grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; }
.perf-points__item {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 20rpx 12rpx;
  display: flex; flex-direction: column; align-items: center; gap: 10rpx;
  border: 1px solid transparent;
}
.perf-points__icon {
  width: 56rpx; height: 56rpx;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 26rpx;
}
.perf-points__val   { font-size: 34rpx; font-weight: 700; line-height: 1; }
.perf-points__label { font-size: 20rpx; color: var(--text-tertiary); }

/* 学习数据卡片 */
.perf-stats { padding-top: 20rpx; }
.perf-stats__grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12rpx; }
.perf-stats__card {
  padding: 20rpx;
  display: flex; flex-direction: column; align-items: center; gap: 8rpx;
}
.perf-stats__icon  { font-size: 40rpx; }
.perf-stats__val   { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }
.perf-stats__label { font-size: 22rpx; color: var(--text-tertiary); }

/* 连续打卡 */
.perf-streak { padding-top: 20rpx; }
.perf-streak__card {
  display: flex;
  align-items: center;
  padding: 20rpx 24rpx;
  gap: 24rpx;
}
.perf-streak__left { display: flex; align-items: center; gap: 16rpx; }
.perf-streak__fire { font-size: 48rpx; }
.perf-streak__info { display: flex; flex-direction: column; }
.perf-streak__days { font-size: 48rpx; font-weight: 700; color: var(--bhp-warn-500, #f59e0b); line-height: 1; }
.perf-streak__unit { font-size: 22rpx; color: var(--text-tertiary); }
.perf-streak__right { flex: 1; display: flex; flex-direction: column; align-items: flex-end; gap: 10rpx; }
.perf-streak__bar { display: flex; gap: 8rpx; }
.perf-streak__dot {
  width: 20rpx; height: 20rpx;
  border-radius: 50%;
  background: var(--bhp-gray-200);
}
.perf-streak__dot--active { background: var(--bhp-warn-400, #fbbf24); }

/* 时长 */
.perf-time { padding-top: 20rpx; }
.perf-time__row { display: grid; grid-template-columns: 1fr 1fr; gap: 12rpx; }
.perf-time__card {
  padding: 20rpx;
  display: flex; flex-direction: column; gap: 10rpx;
}
.perf-time__val   { font-size: 36rpx; font-weight: 700; color: var(--text-primary); }
.perf-time__label { font-size: 22rpx; color: var(--text-tertiary); }
.perf-time__bar {
  height: 8rpx; background: var(--bhp-gray-100);
  border-radius: var(--radius-full); overflow: hidden;
}
.perf-time__bar-fill {
  height: 100%; border-radius: var(--radius-full);
  transition: width 0.4s ease;
}
.perf-time__milestone-row { display: flex; flex-wrap: wrap; gap: 6rpx; }
.perf-time__milestone {
  font-size: 18rpx; color: var(--text-tertiary);
  background: var(--bhp-gray-100);
  padding: 2rpx 10rpx;
  border-radius: var(--radius-full);
}
.perf-time__milestone--done {
  color: var(--bhp-primary-600, #059669);
  background: var(--bhp-primary-50);
}

/* 完成情况 */
.perf-complete { padding-top: 20rpx; }
.perf-complete__card {
  display: flex; align-items: center;
  padding: 24rpx;
}
.perf-complete__item {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8rpx;
}
.perf-complete__val   { font-size: 40rpx; font-weight: 700; color: var(--text-primary); }
.perf-complete__label { font-size: 22rpx; color: var(--text-tertiary); }
.perf-complete__divider { width: 1px; height: 60rpx; background: var(--border-light); }
</style>
