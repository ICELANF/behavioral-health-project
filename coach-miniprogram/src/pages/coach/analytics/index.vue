<template>
  <view class="ca-page">

    <!-- 导航栏 -->
    <view class="ca-navbar safe-area-top">
      <view class="ca-navbar__back" @tap="goBack">
        <text class="ca-navbar__arrow">‹</text>
      </view>
      <text class="ca-navbar__title">数据分析</text>
      <view class="ca-navbar__placeholder"></view>
    </view>

    <!-- 时间筛选 -->
    <view class="ca-tabs">
      <view
        v-for="tab in PERIODS"
        :key="tab.key"
        class="ca-tab"
        :class="{ 'ca-tab--active': period === tab.key }"
        @tap="switchPeriod(tab.key)"
      >
        <text>{{ tab.label }}</text>
      </view>
    </view>

    <scroll-view scroll-y class="ca-body">

      <!-- 4 核心指标 -->
      <view class="ca-metrics">
        <view class="ca-metric" v-for="m in metrics" :key="m.key">
          <text class="ca-metric__val" :style="{ color: m.color }">{{ m.value }}</text>
          <text class="ca-metric__label">{{ m.label }}</text>
        </view>
      </view>

      <!-- 学员风险分布 -->
      <view class="ca-card">
        <text class="ca-card__title">学员风险分布</text>
        <view class="ca-risk-bar">
          <view
            class="ca-risk-bar__seg ca-risk-bar__seg--high"
            :style="{ width: riskPct.high + '%' }"
            v-if="riskPct.high > 0"
          >
            <text v-if="riskPct.high > 10">{{ data?.risk_high ?? 0 }}</text>
          </view>
          <view
            class="ca-risk-bar__seg ca-risk-bar__seg--mid"
            :style="{ width: riskPct.mid + '%' }"
            v-if="riskPct.mid > 0"
          >
            <text v-if="riskPct.mid > 10">{{ data?.risk_mid ?? 0 }}</text>
          </view>
          <view
            class="ca-risk-bar__seg ca-risk-bar__seg--low"
            :style="{ width: riskPct.low + '%' }"
            v-if="riskPct.low > 0"
          >
            <text v-if="riskPct.low > 10">{{ data?.risk_low ?? 0 }}</text>
          </view>
        </view>
        <view class="ca-risk-legend">
          <view class="ca-risk-legend__item"><view class="ca-dot ca-dot--high"></view><text>高风险</text></view>
          <view class="ca-risk-legend__item"><view class="ca-dot ca-dot--mid"></view><text>中风险</text></view>
          <view class="ca-risk-legend__item"><view class="ca-dot ca-dot--low"></view><text>低风险</text></view>
        </view>
      </view>

      <!-- 学员活跃度排行 -->
      <view class="ca-card">
        <text class="ca-card__title">学员活跃度 TOP5</text>
        <view class="ca-rank" v-if="data?.top_students?.length">
          <view
            v-for="(stu, idx) in data.top_students.slice(0, 5)"
            :key="idx"
            class="ca-rank__item"
          >
            <view class="ca-rank__pos" :class="{ 'ca-rank__pos--gold': idx === 0, 'ca-rank__pos--silver': idx === 1, 'ca-rank__pos--bronze': idx === 2 }">
              <text>{{ idx + 1 }}</text>
            </view>
            <text class="ca-rank__name">{{ stu.full_name || stu.username }}</text>
            <text class="ca-rank__pts">{{ stu.points ?? 0 }} 分</text>
            <text class="ca-rank__trend" :class="getTrendClass(stu.trend)">{{ getTrendIcon(stu.trend) }}</text>
          </view>
        </view>
        <view class="ca-empty-inline" v-else>
          <text>暂无数据</text>
        </view>
      </view>

      <!-- 推送效果漏斗 -->
      <view class="ca-card">
        <text class="ca-card__title">本期推送效果</text>
        <view class="ca-funnel" v-if="data?.push_stats">
          <view class="ca-funnel__step" :style="{ width: '100%' }">
            <view class="ca-funnel__bar ca-funnel__bar--sent">
              <text class="ca-funnel__num">{{ data.push_stats.sent ?? 0 }}</text>
            </view>
            <text class="ca-funnel__label">已发送</text>
          </view>
          <view class="ca-funnel__step" :style="{ width: funnelPct(data.push_stats.approved, data.push_stats.sent) + '%' }">
            <view class="ca-funnel__bar ca-funnel__bar--approved">
              <text class="ca-funnel__num">{{ data.push_stats.approved ?? 0 }}</text>
            </view>
            <text class="ca-funnel__label">已通过</text>
          </view>
          <view class="ca-funnel__step" :style="{ width: funnelPct(data.push_stats.completed, data.push_stats.sent) + '%' }">
            <view class="ca-funnel__bar ca-funnel__bar--completed">
              <text class="ca-funnel__num">{{ data.push_stats.completed ?? 0 }}</text>
            </view>
            <text class="ca-funnel__label">已完成</text>
          </view>
        </view>
        <view class="ca-empty-inline" v-else>
          <text>暂无数据</text>
        </view>
      </view>

    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const PERIODS = [
  { key: 'week',  label: '本周' },
  { key: 'month', label: '本月' },
  { key: '3month', label: '近3月' },
]

const period = ref('week')
const data   = ref<any>(null)

const metrics = computed(() => [
  { key: 'students',   label: '管理学员',   value: data.value?.student_count ?? '-',       color: '#3b82f6' },
  { key: 'completion', label: '本期完课率', value: (data.value?.completion_rate ?? '-') + '%', color: '#10b981' },
  { key: 'risk',       label: '平均风险',   value: data.value?.avg_risk_score ?? '-',      color: '#f59e0b' },
  { key: 'pending',    label: '待处理',     value: data.value?.pending_tasks ?? '-',       color: '#ef4444' },
])

const riskPct = computed(() => {
  const h = data.value?.risk_high ?? 0
  const m = data.value?.risk_mid ?? 0
  const l = data.value?.risk_low ?? 0
  const total = h + m + l
  if (total === 0) return { high: 33, mid: 34, low: 33 }
  return {
    high: Math.round((h / total) * 100),
    mid:  Math.round((m / total) * 100),
    low:  Math.round((l / total) * 100),
  }
})

onMounted(async () => {
  await loadData()
})

async function loadData() {
  try {
    const [risk, stage, pushStats] = await Promise.all([
      http.get<any>('/v1/analytics/coach/risk-trend', { period: period.value }),
      http.get<any>('/v1/analytics/coach/stage-distribution', { period: period.value }),
      http.get<any>('/v1/coach/push-queue/analytics', { period: period.value }),
    ])
    data.value = { ...risk, ...stage, push_stats: pushStats }
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

function switchPeriod(key: string) {
  if (period.value === key) return
  period.value = key
  loadData()
}

function getTrendClass(trend: string): string {
  if (trend === 'up') return 'ca-rank__trend--up'
  if (trend === 'down') return 'ca-rank__trend--down'
  return ''
}

function getTrendIcon(trend: string): string {
  if (trend === 'up') return '↑'
  if (trend === 'down') return '↓'
  return '—'
}

function funnelPct(value: number | undefined, total: number | undefined): number {
  if (!total || !value) return 40
  return Math.max(40, Math.round((value / total) * 100))
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.ca-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

.ca-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.ca-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ca-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.ca-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.ca-navbar__placeholder { width: 64rpx; }

/* 时间Tab */
.ca-tabs {
  display: flex; background: var(--surface); padding: 12rpx 32rpx 16rpx;
  gap: 16rpx; border-bottom: 1px solid var(--border-light);
}
.ca-tab {
  flex: 1; text-align: center; padding: 12rpx 0; border-radius: var(--radius-full);
  font-size: 24rpx; font-weight: 600; color: var(--text-secondary);
  background: var(--surface-secondary); cursor: pointer;
}
.ca-tab--active { background: var(--bhp-primary-500); color: #fff; }

.ca-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

/* 核心指标 */
.ca-metrics { display: flex; flex-wrap: wrap; gap: 16rpx; margin-bottom: 20rpx; }
.ca-metric {
  width: calc(50% - 8rpx); background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx 20rpx; display: flex; flex-direction: column; align-items: center; gap: 6rpx;
  border: 1px solid var(--border-light);
}
.ca-metric__val { font-size: 44rpx; font-weight: 800; }
.ca-metric__label { font-size: 22rpx; color: var(--text-secondary); }

/* 卡片 */
.ca-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light);
}
.ca-card__title { font-size: 28rpx; font-weight: 700; color: var(--text-primary); display: block; margin-bottom: 20rpx; }

/* 风险分布 */
.ca-risk-bar { display: flex; height: 40rpx; border-radius: var(--radius-full); overflow: hidden; }
.ca-risk-bar__seg {
  display: flex; align-items: center; justify-content: center;
  font-size: 20rpx; font-weight: 700; color: #fff; transition: width 0.4s;
}
.ca-risk-bar__seg--high { background: #ef4444; }
.ca-risk-bar__seg--mid { background: #f59e0b; }
.ca-risk-bar__seg--low { background: #10b981; }

.ca-risk-legend { display: flex; gap: 24rpx; margin-top: 16rpx; justify-content: center; }
.ca-risk-legend__item { display: flex; align-items: center; gap: 6rpx; font-size: 22rpx; color: var(--text-secondary); }
.ca-dot { width: 16rpx; height: 16rpx; border-radius: 50%; }
.ca-dot--high { background: #ef4444; }
.ca-dot--mid { background: #f59e0b; }
.ca-dot--low { background: #10b981; }

/* 排行 */
.ca-rank { display: flex; flex-direction: column; gap: 12rpx; }
.ca-rank__item { display: flex; align-items: center; gap: 16rpx; padding: 12rpx 0; border-bottom: 1px solid var(--border-light); }
.ca-rank__item:last-child { border-bottom: none; }
.ca-rank__pos {
  width: 44rpx; height: 44rpx; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; font-weight: 700; color: var(--text-tertiary);
  background: var(--bhp-gray-100);
}
.ca-rank__pos--gold { background: #fef3c7; color: #d97706; }
.ca-rank__pos--silver { background: #f1f5f9; color: #64748b; }
.ca-rank__pos--bronze { background: #fff7ed; color: #ea580c; }
.ca-rank__name { flex: 1; font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.ca-rank__pts { font-size: 24rpx; color: var(--text-secondary); font-weight: 600; }
.ca-rank__trend { font-size: 28rpx; width: 40rpx; text-align: center; color: var(--text-tertiary); }
.ca-rank__trend--up { color: #10b981; }
.ca-rank__trend--down { color: #ef4444; }

/* 漏斗 */
.ca-funnel { display: flex; flex-direction: column; align-items: center; gap: 12rpx; }
.ca-funnel__step { display: flex; align-items: center; gap: 12rpx; min-width: 40%; transition: width 0.4s; }
.ca-funnel__bar {
  flex: 1; height: 48rpx; border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
}
.ca-funnel__bar--sent { background: #3b82f6; }
.ca-funnel__bar--approved { background: #f59e0b; }
.ca-funnel__bar--completed { background: #10b981; }
.ca-funnel__num { font-size: 22rpx; font-weight: 700; color: #fff; }
.ca-funnel__label { font-size: 22rpx; color: var(--text-secondary); white-space: nowrap; flex-shrink: 0; width: 80rpx; }

.ca-empty-inline { text-align: center; padding: 24rpx; font-size: 24rpx; color: var(--text-tertiary); }
</style>
