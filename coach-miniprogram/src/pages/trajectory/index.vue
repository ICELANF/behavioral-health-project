<template>
  <view class="traj-page">
    <!-- 自定义导航 -->
    <view class="traj-nav">
      <view class="traj-nav-back" @tap="goBack">‹</view>
      <text class="traj-nav-title">行为轨迹</text>
    </view>

    <scroll-view scroll-y class="traj-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 加载中 -->
      <view v-if="loading" class="traj-loading"><text>加载中…</text></view>

      <template v-else>
        <!-- 综合评分环 -->
        <view class="score-card">
          <view class="score-ring-wrap">
            <!-- SVG 评分环 -->
            <view class="score-ring">
              <text class="score-num">{{ traj.trajectory_score || 0 }}</text>
              <text class="score-label">综合成长分</text>
            </view>
          </view>
          <view class="score-meta">
            <view class="score-meta-row">
              <text class="score-meta-label">评估日期</text>
              <text class="score-meta-val">近 {{ traj.days || 30 }} 天</text>
            </view>
            <view class="score-meta-row">
              <text class="score-meta-label">评估项目数</text>
              <text class="score-meta-val">{{ totalMetrics }}</text>
            </view>
          </view>
        </view>

        <!-- 分享者资质提示 -->
        <view v-if="traj.qualifies_for_sharer" class="qualify-banner qualify-banner--yes" @tap="goBecome">
          <text class="qualify-icon">🌟</text>
          <view class="qualify-body">
            <text class="qualify-title">你已达到分享者资质！</text>
            <text class="qualify-sub">点击申请成为分享者，照亮更多同道者 →</text>
          </view>
        </view>
        <view v-else class="qualify-banner qualify-banner--no">
          <text class="qualify-icon">💪</text>
          <view class="qualify-body">
            <text class="qualify-title">继续积累，距分享者资质还差一步</text>
            <text class="qualify-sub">需: 成长分≥60 · 依从率≥50% · 连续打卡≥3天</text>
          </view>
        </view>

        <!-- 4 指标卡 -->
        <view class="metric-grid">
          <view class="metric-card metric-card--green">
            <text class="metric-icon">✅</text>
            <text class="metric-val">{{ pct(traj.adherence_rate) }}</text>
            <text class="metric-key">依从率</text>
            <view class="metric-bar-bg"><view class="metric-bar-fill metric-bar-fill--green" :style="{ width: pct(traj.adherence_rate) }"></view></view>
          </view>
          <view class="metric-card metric-card--blue">
            <text class="metric-icon">📚</text>
            <text class="metric-val">{{ fmtHours(traj.learning_hours) }}</text>
            <text class="metric-key">学习时长</text>
            <view class="metric-bar-bg"><view class="metric-bar-fill metric-bar-fill--blue" :style="{ width: learningBarPct }"></view></view>
          </view>
          <view class="metric-card metric-card--orange">
            <text class="metric-icon">🔥</text>
            <text class="metric-val">{{ traj.current_streak || 0 }} 天</text>
            <text class="metric-key">当前连续</text>
            <text class="metric-sub">最高 {{ traj.max_streak || 0 }} 天</text>
          </view>
          <view class="metric-card metric-card--purple">
            <text class="metric-icon">⚡</text>
            <text class="metric-val">{{ fmtRecovery(traj.recovery_speed) }}</text>
            <text class="metric-key">恢复速度</text>
            <text class="metric-sub">中断后重返</text>
          </view>
        </view>

        <!-- 每周依从率 -->
        <view class="chart-card" v-if="adherenceWeekly.length">
          <text class="chart-title">📊 近周依从率趋势</text>
          <view class="bar-chart">
            <view v-for="(d, i) in adherenceWeekly" :key="i" class="bar-col">
              <view class="bar-wrap">
                <view class="bar-fill bar-fill--green" :style="{ height: barH(d.adherence_rate) }"></view>
              </view>
              <text class="bar-label">{{ d.week_label || ('W'+(i+1)) }}</text>
            </view>
          </view>
        </view>

        <!-- 评估提升 -->
        <view class="assess-card" v-if="traj.assessment_delta != null">
          <text class="assess-title">📋 评估改善</text>
          <view class="assess-row">
            <view class="assess-item">
              <text class="assess-num">{{ traj.first_score ?? '—' }}</text>
              <text class="assess-lbl">首次评分</text>
            </view>
            <text class="assess-arrow">→</text>
            <view class="assess-item">
              <text class="assess-num assess-num--latest">{{ traj.latest_score ?? '—' }}</text>
              <text class="assess-lbl">最新评分</text>
            </view>
            <view class="assess-delta" :class="traj.assessment_delta >= 0 ? 'delta--pos' : 'delta--neg'">
              <text>{{ traj.assessment_delta >= 0 ? '+' : '' }}{{ traj.assessment_delta }}</text>
            </view>
          </view>
        </view>

        <!-- 行动建议 -->
        <view class="advice-card" v-if="advices.length">
          <text class="advice-title">💡 成长建议</text>
          <view v-for="(a, i) in advices" :key="i" class="advice-item">
            <text class="advice-dot">·</text>
            <text class="advice-text">{{ a }}</text>
          </view>
        </view>

        <view style="height:120rpx;"></view>
      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

interface TrajData {
  days?: number
  trajectory_score?: number
  adherence_rate?: number
  adherence_weekly?: { week_label?: string; adherence_rate: number }[]
  learning_hours?: number
  current_streak?: number
  max_streak?: number
  recovery_speed?: number
  assessment_delta?: number
  first_score?: number
  latest_score?: number
  qualifies_for_sharer?: boolean
  total_tasks?: number
  completed_tasks?: number
  total_learning_days?: number
}

const loading = ref(true)
const refreshing = ref(false)
const traj = ref<TrajData>({})

const adherenceWeekly = computed(() => traj.value.adherence_weekly || [])
const totalMetrics = computed(() => {
  let n = 0
  if (traj.value.adherence_rate != null) n++
  if (traj.value.learning_hours != null) n++
  if (traj.value.current_streak != null) n++
  if (traj.value.assessment_delta != null) n++
  return n
})

const learningBarPct = computed(() => {
  const h = traj.value.learning_hours || 0
  const maxH = 20 // 20小时满格
  return Math.min(100, (h / maxH) * 100).toFixed(0) + '%'
})

const advices = computed(() => {
  const list: string[] = []
  const t = traj.value
  if (!t.trajectory_score) return list
  if ((t.adherence_rate || 0) < 0.5) list.push('依从率不足50%，尝试把任务分解成更小步骤')
  if ((t.current_streak || 0) < 3) list.push('连续打卡天数不足3天，每日睡前设提醒更容易坚持')
  if ((t.learning_hours || 0) < 5) list.push('近期学习时长较少，建议每天利用碎片时间学习15分钟')
  if ((t.recovery_speed || 0) > 3) list.push('中断后恢复较慢，中断时告知教练获得支持')
  if (list.length === 0) list.push('各项指标良好！继续保持当前节奏，向分享者目标迈进')
  return list
})

function pct(val?: number) {
  if (val == null) return '—'
  return Math.round((val || 0) * 100) + '%'
}

function fmtHours(h?: number) {
  if (h == null) return '—'
  if (h < 1) return Math.round(h * 60) + 'min'
  return h.toFixed(1) + 'h'
}

function fmtRecovery(days?: number) {
  if (days == null) return '—'
  if (days === 0) return '从不中断'
  return days.toFixed(1) + '天'
}

function barH(rate: number) {
  return Math.max(4, Math.round((rate || 0) * 100)) + 'rpx'
}

async function load() {
  try {
    const res = await http<TrajData>('/api/v1/learning/trajectory?days=30')
    traj.value = res as TrajData
  } catch (e) {
    // graceful fallback
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function onRefresh() {
  refreshing.value = true
  load()
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
  } else {
    uni.reLaunch({ url: '/pages/home/index' })
  }
}

function goBecome() {
  uni.navigateTo({ url: '/pages/become-sharer/index' })
}

onMounted(() => load())
</script>

<style scoped>
.traj-page { min-height: 100vh; background: #f5f6fa; }
.traj-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 88rpx; padding-top: env(safe-area-inset-top);
  background: linear-gradient(135deg, #1e3a5f 0%, #2d6a4f 100%);
  display: flex; align-items: center; padding-left: 28rpx;
}
.traj-nav-back { color: #fff; font-size: 48rpx; padding-right: 16rpx; line-height: 1; }
.traj-nav-title { color: #fff; font-size: 32rpx; font-weight: 700; }
.traj-scroll { position: fixed; top: calc(88rpx + env(safe-area-inset-top)); bottom: 0; left: 0; right: 0; }
.traj-loading { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }

/* 评分卡 */
.score-card {
  background: linear-gradient(135deg, #1e3a5f 0%, #2d6a4f 100%);
  padding: 40rpx 32rpx 32rpx;
  display: flex; align-items: center; gap: 40rpx;
}
.score-ring-wrap { flex-shrink: 0; }
.score-ring {
  width: 160rpx; height: 160rpx; border-radius: 50%;
  border: 8rpx solid rgba(255,255,255,0.4);
  background: rgba(255,255,255,0.1);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.score-num { font-size: 56rpx; font-weight: 900; color: #fff; line-height: 1; }
.score-label { font-size: 20rpx; color: rgba(255,255,255,0.8); margin-top: 4rpx; }
.score-meta { flex: 1; }
.score-meta-row { display: flex; justify-content: space-between; margin-bottom: 12rpx; }
.score-meta-label { font-size: 24rpx; color: rgba(255,255,255,0.7); }
.score-meta-val { font-size: 24rpx; color: #fff; font-weight: 600; }

/* 资质横幅 */
.qualify-banner {
  margin: 20rpx 24rpx 0;
  padding: 20rpx 24rpx;
  border-radius: 20rpx;
  display: flex; align-items: center; gap: 16rpx;
}
.qualify-banner--yes { background: linear-gradient(135deg, #dcfce7, #bbf7d0); }
.qualify-banner--no  { background: #f9fafb; border: 2rpx solid #e5e7eb; }
.qualify-icon { font-size: 44rpx; flex-shrink: 0; }
.qualify-body { flex: 1; }
.qualify-title { font-size: 26rpx; font-weight: 700; color: #111; display: block; }
.qualify-sub { font-size: 22rpx; color: #6b7280; display: block; margin-top: 4rpx; }

/* 4 指标卡 */
.metric-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 16rpx; margin: 20rpx 24rpx 0;
}
.metric-card {
  background: #fff; border-radius: 20rpx; padding: 24rpx 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.metric-icon { font-size: 36rpx; display: block; }
.metric-val { font-size: 44rpx; font-weight: 900; display: block; margin: 8rpx 0 2rpx; }
.metric-key { font-size: 22rpx; color: #6b7280; display: block; }
.metric-sub { font-size: 20rpx; color: #9ca3af; display: block; margin-top: 4rpx; }
.metric-card--green .metric-val { color: #16a34a; }
.metric-card--blue  .metric-val { color: #1565c0; }
.metric-card--orange .metric-val { color: #d97706; }
.metric-card--purple .metric-val { color: #7c3aed; }
.metric-bar-bg {
  height: 8rpx; background: #f3f4f6; border-radius: 4rpx;
  margin-top: 12rpx; overflow: hidden;
}
.metric-bar-fill { height: 100%; border-radius: 4rpx; }
.metric-bar-fill--green { background: #16a34a; }
.metric-bar-fill--blue  { background: #1565c0; }

/* 柱状图 */
.chart-card {
  background: #fff; margin: 16rpx 24rpx 0;
  border-radius: 20rpx; padding: 28rpx 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.chart-title { font-size: 28rpx; font-weight: 700; color: #111; display: block; margin-bottom: 24rpx; }
.bar-chart { display: flex; align-items: flex-end; gap: 12rpx; height: 120rpx; }
.bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.bar-wrap { flex: 1; display: flex; align-items: flex-end; width: 100%; }
.bar-fill { width: 100%; border-radius: 6rpx 6rpx 0 0; min-height: 4rpx; }
.bar-fill--green { background: linear-gradient(180deg, #86efac, #16a34a); }
.bar-label { font-size: 18rpx; color: #9ca3af; }

/* 评估 */
.assess-card {
  background: #fff; margin: 16rpx 24rpx 0;
  border-radius: 20rpx; padding: 28rpx 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.assess-title { font-size: 28rpx; font-weight: 700; color: #111; display: block; margin-bottom: 20rpx; }
.assess-row { display: flex; align-items: center; gap: 16rpx; }
.assess-item { flex: 1; text-align: center; }
.assess-num { font-size: 52rpx; font-weight: 900; color: #374151; display: block; }
.assess-num--latest { color: #16a34a; }
.assess-lbl { font-size: 22rpx; color: #6b7280; display: block; }
.assess-arrow { font-size: 36rpx; color: #9ca3af; }
.assess-delta {
  padding: 8rpx 20rpx; border-radius: 40rpx;
  font-size: 30rpx; font-weight: 800;
}
.delta--pos { background: #dcfce7; color: #16a34a; }
.delta--neg { background: #fee2e2; color: #dc2626; }

/* 建议 */
.advice-card {
  background: #fff; margin: 16rpx 24rpx 0;
  border-radius: 20rpx; padding: 28rpx 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.advice-title { font-size: 28rpx; font-weight: 700; color: #111; display: block; margin-bottom: 16rpx; }
.advice-item { display: flex; gap: 8rpx; margin-bottom: 12rpx; }
.advice-dot { color: #7c3aed; font-size: 30rpx; flex-shrink: 0; line-height: 1.4; }
.advice-text { font-size: 26rpx; color: #374151; line-height: 1.6; }
</style>
