<template>
  <view class="analytics-page">

    <!-- 刷新 -->
    <view class="an-toolbar px-4">
      <text class="text-xs text-tertiary-color">教练数据看板</text>
      <view class="an-refresh" @tap="load">
        <text class="text-xs text-primary-color">↻ 刷新</text>
      </view>
    </view>

    <!-- 骨架屏 -->
    <template v-if="loading">
      <view class="px-4">
        <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 110rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </view>
    </template>

    <template v-else>
      <!-- 学员总览 -->
      <view class="an-overview px-4">
        <text class="an-section-title">学员总览</text>
        <view class="an-overview__grid">
          <view class="an-card an-card--total">
            <text class="an-card__val">{{ data.total_students }}</text>
            <text class="an-card__label">总学员数</text>
          </view>
          <view class="an-card an-card--active">
            <text class="an-card__val" style="color: #52c41a;">{{ data.active_students_7d }}</text>
            <text class="an-card__label">7日活跃</text>
          </view>
        </view>
      </view>

      <!-- 风险分布 -->
      <view class="an-risk px-4">
        <text class="an-section-title">风险分布</text>
        <view class="an-risk__card bhp-card bhp-card--flat">
          <view
            v-for="item in riskDistribution"
            :key="item.key"
            class="an-risk__row"
          >
            <view class="an-risk__label-col">
              <view class="an-risk__dot" :style="{ background: item.color }"></view>
              <text class="an-risk__label">{{ item.label }}</text>
            </view>
            <view class="an-risk__bar-col">
              <view class="an-risk__bar">
                <view
                  class="an-risk__bar-fill"
                  :style="{ width: barWidth(item.count) + '%', background: item.color }"
                ></view>
              </view>
            </view>
            <text class="an-risk__count">{{ item.count }}</text>
          </view>

          <!-- 改善率 -->
          <view class="an-risk__improve" v-if="data.improvement_rate">
            <text class="text-xs text-secondary-color">风险改善率</text>
            <text class="an-risk__improve-val" style="color: #52c41a;">
              ↑ {{ (data.improvement_rate * 100).toFixed(1) }}%
            </text>
          </view>
        </view>
      </view>

      <!-- 工作量统计 -->
      <view class="an-workload px-4">
        <text class="an-section-title">近30天工作量</text>
        <view class="an-workload__grid">
          <view class="an-workload__item bhp-card bhp-card--flat">
            <text class="an-workload__icon">📤</text>
            <text class="an-workload__val">{{ data.messages_sent_30d }}</text>
            <text class="an-workload__label">发送消息</text>
          </view>
          <view class="an-workload__item bhp-card bhp-card--flat">
            <text class="an-workload__icon">📋</text>
            <text class="an-workload__val">{{ data.assessments_reviewed_30d }}</text>
            <text class="an-workload__label">审核评估</text>
          </view>
          <view class="an-workload__item bhp-card bhp-card--flat" v-if="data.avg_response_time_hours != null">
            <text class="an-workload__icon">⚡</text>
            <text class="an-workload__val">{{ data.avg_response_time_hours?.toFixed(1) }}h</text>
            <text class="an-workload__label">平均响应</text>
          </view>
        </view>
      </view>

      <!-- 效能指标 -->
      <view class="an-kpi px-4">
        <text class="an-section-title">效能指标</text>
        <view class="an-kpi__card bhp-card bhp-card--flat">

          <view class="an-kpi__row">
            <text class="an-kpi__label">学员活跃率（7日）</text>
            <view class="an-kpi__bar-wrap">
              <view class="an-kpi__bar">
                <view class="an-kpi__bar-fill" :style="{ width: activeRate + '%', background: '#52c41a' }"></view>
              </view>
              <text class="an-kpi__pct">{{ activeRate }}%</text>
            </view>
          </view>

          <view class="an-kpi__row">
            <text class="an-kpi__label">高风险占比</text>
            <view class="an-kpi__bar-wrap">
              <view class="an-kpi__bar">
                <view class="an-kpi__bar-fill" :style="{ width: highRiskRate + '%', background: '#ff4d4f' }"></view>
              </view>
              <text class="an-kpi__pct" :style="{ color: highRiskRate > 30 ? '#ff4d4f' : 'inherit' }">{{ highRiskRate }}%</text>
            </view>
          </view>

          <view class="an-kpi__row" v-if="data.improvement_rate">
            <text class="an-kpi__label">风险改善率</text>
            <view class="an-kpi__bar-wrap">
              <view class="an-kpi__bar">
                <view class="an-kpi__bar-fill" :style="{ width: (data.improvement_rate * 100).toFixed(0) + '%', background: '#722ed1' }"></view>
              </view>
              <text class="an-kpi__pct" style="color: #722ed1;">{{ (data.improvement_rate * 100).toFixed(1) }}%</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 提示 -->
      <view class="an-tip px-4">
        <view class="an-tip__card">
          <text class="an-tip__text">
            💡 持续关注高风险学员，提升活跃率有助于改善学员健康结局
          </text>
        </view>
      </view>
    </template>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { coachApi, type CoachAnalytics } from '@/api/coach'
import { useCoachStore } from '@/stores/coach'

const coachStore = useCoachStore()

const EMPTY: CoachAnalytics = {
  total_students: 0, active_students_7d: 0,
  high_risk_count: 0, medium_risk_count: 0, low_risk_count: 0,
  improvement_rate: 0, messages_sent_30d: 0, assessments_reviewed_30d: 0
}

const data    = ref<CoachAnalytics>({ ...EMPTY })
const loading = ref(false)

onMounted(load)

onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
})

async function load() {
  loading.value = true
  try {
    // 优先调用专用 analytics 接口，降级使用 store dashboardStats
    try {
      data.value = await coachApi.analytics()
    } catch {
      const dash = coachStore.dashboardStats
      if (dash) {
        data.value = {
          ...EMPTY,
          total_students: dash.total_students,
          active_students_7d: dash.active_students_7d,
          high_risk_count: dash.high_risk_count,
          medium_risk_count: dash.medium_risk_count,
          improvement_rate: dash.improvement_rate,
        }
      }
    }
  } catch { /* 静默 */ } finally {
    loading.value = false
  }
}

const riskDistribution = computed(() => [
  { key: 'high',     label: '高风险', count: data.value.high_risk_count,   color: '#ff4d4f' },
  { key: 'moderate', label: '中风险', count: data.value.medium_risk_count, color: '#fa8c16' },
  { key: 'low',      label: '低风险', count: data.value.low_risk_count,    color: '#52c41a' },
])

const maxCount = computed(() =>
  Math.max(...riskDistribution.value.map(r => r.count), 1)
)

function barWidth(count: number): number {
  return Math.round((count / maxCount.value) * 100)
}

const activeRate = computed(() => {
  if (!data.value.total_students) return 0
  return Math.round((data.value.active_students_7d / data.value.total_students) * 100)
})

const highRiskRate = computed(() => {
  if (!data.value.total_students) return 0
  return Math.round((data.value.high_risk_count / data.value.total_students) * 100)
})
</script>

<style scoped>
.analytics-page { background: var(--surface-secondary); min-height: 100vh; }

.an-toolbar { display: flex; justify-content: space-between; align-items: center; padding-top: 12rpx; padding-bottom: 4rpx; }
.an-refresh { cursor: pointer; padding: 4rpx 8rpx; }
.an-section-title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 12rpx; }

/* 总览 */
.an-overview { padding-top: 12rpx; }
.an-overview__grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12rpx; }
.an-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  padding: 24rpx;
  display: flex; flex-direction: column; align-items: center; gap: 8rpx;
}
.an-card__val   { font-size: 52rpx; font-weight: 700; color: var(--text-primary); line-height: 1; }
.an-card__label { font-size: 22rpx; color: var(--text-tertiary); }

/* 风险分布 */
.an-risk { padding-top: 20rpx; }
.an-risk__card { padding: 20rpx 24rpx; }
.an-risk__row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 16rpx; }
.an-risk__label-col { width: 100rpx; display: flex; align-items: center; gap: 8rpx; }
.an-risk__dot { width: 14rpx; height: 14rpx; border-radius: 50%; flex-shrink: 0; }
.an-risk__label { font-size: 24rpx; color: var(--text-secondary); }
.an-risk__bar-col { flex: 1; }
.an-risk__bar { height: 16rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.an-risk__bar-fill { height: 100%; border-radius: var(--radius-full); transition: width 0.4s ease; }
.an-risk__count { width: 40rpx; font-size: 26rpx; font-weight: 700; color: var(--text-primary); text-align: right; }
.an-risk__improve { display: flex; align-items: center; justify-content: space-between; padding-top: 12rpx; border-top: 1px solid var(--border-light); }
.an-risk__improve-val { font-size: 28rpx; font-weight: 700; }

/* 工作量 */
.an-workload { padding-top: 20rpx; }
.an-workload__grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10rpx; }
.an-workload__item { padding: 20rpx 8rpx; display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.an-workload__icon { font-size: 36rpx; }
.an-workload__val  { font-size: 36rpx; font-weight: 700; color: var(--text-primary); }
.an-workload__label { font-size: 20rpx; color: var(--text-tertiary); text-align: center; }

/* KPI */
.an-kpi { padding-top: 20rpx; }
.an-kpi__card { padding: 20rpx 24rpx; }
.an-kpi__row { display: flex; align-items: center; gap: 16rpx; margin-bottom: 20rpx; }
.an-kpi__row:last-child { margin-bottom: 0; }
.an-kpi__label { width: 160rpx; font-size: 24rpx; color: var(--text-secondary); flex-shrink: 0; }
.an-kpi__bar-wrap { flex: 1; display: flex; align-items: center; gap: 12rpx; }
.an-kpi__bar { flex: 1; height: 14rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.an-kpi__bar-fill { height: 100%; border-radius: var(--radius-full); transition: width 0.4s ease; }
.an-kpi__pct { font-size: 24rpx; font-weight: 700; color: var(--text-primary); width: 64rpx; text-align: right; flex-shrink: 0; }

/* 提示 */
.an-tip { padding-top: 16rpx; }
.an-tip__card { background: var(--bhp-primary-50); border-radius: var(--radius-lg); padding: 16rpx 20rpx; }
.an-tip__text { font-size: 22rpx; color: var(--bhp-primary-600, #059669); line-height: 1.6; display: block; }
</style>
