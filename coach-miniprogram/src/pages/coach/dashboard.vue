<template>
  <view class="cd-page">
    <view class="cd-navbar safe-area-top">
      <view class="cd-navbar__back" @tap="goBack"><text class="cd-navbar__arrow">&#8249;</text></view>
      <text class="cd-navbar__title">教练工作台</text>
      <view class="cd-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="cd-body">
      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 200rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>
      <template v-else>

        <!-- 本月数据 -->
        <view class="cd-card">
          <text class="cd-card__title">本月数据</text>
          <view class="cd-stats">
            <view class="cd-stat">
              <text class="cd-stat__val">{{ todayStats.total_students }}</text>
              <text class="cd-stat__label">服务学员</text>
            </view>
            <view class="cd-stat">
              <text class="cd-stat__val">{{ todayStats.alert_students }}</text>
              <text class="cd-stat__label">预警学员</text>
            </view>
            <view class="cd-stat">
              <text class="cd-stat__val">{{ todayStats.pending_followups }}</text>
              <text class="cd-stat__label">待跟进</text>
            </view>
            <view class="cd-stat">
              <text class="cd-stat__val">{{ todayStats.completed_followups }}</text>
              <text class="cd-stat__label">已完成</text>
            </view>
          </view>
        </view>

        <!-- 学员风险分布 -->
        <view class="cd-card">
          <text class="cd-card__title">学员风险分布</text>
          <view class="cd-pie-wrap">
            <view class="cd-pie" :style="pieStyle"></view>
            <view class="cd-pie-legend">
              <view v-for="seg in riskSegments" :key="seg.label" class="cd-legend-item">
                <view class="cd-legend-dot" :style="{ background: seg.color }"></view>
                <text class="cd-legend-label">{{ seg.label }}</text>
                <text class="cd-legend-val">{{ seg.count }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 本周待办 -->
        <view class="cd-card">
          <text class="cd-card__title">本周待办</text>
          <view v-if="todos.length" class="cd-todos">
            <view v-for="(todo, idx) in todos" :key="idx" class="cd-todo" :class="{ 'cd-todo--done': todo.done }">
              <view class="cd-todo__check" @tap="todo.done = !todo.done">
                <text>{{ todo.done ? '&#9745;' : '&#9744;' }}</text>
              </view>
              <view class="cd-todo__body">
                <text class="cd-todo__text">{{ todo.title || todo.text }}</text>
                <text class="cd-todo__sub" v-if="todo.due_date">{{ todo.due_date }}</text>
              </view>
            </view>
          </view>
          <view v-else class="cd-empty-todo">
            <text class="text-sm" style="color: var(--text-tertiary);">暂无待办事项</text>
          </view>
        </view>

      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const loading     = ref(false)
const todayStats  = ref<any>({})
const coachInfo   = ref<any>({})
const studentList = ref<any[]>([])
const todos       = ref<any[]>([])

const RISK_COLORS: Record<string, string> = {
  low: '#22c55e', medium: '#f59e0b', high: '#ef4444', unknown: '#94a3b8',
}
const RISK_LABELS: Record<string, string> = {
  low: '低风险', medium: '中风险', high: '高风险', unknown: '未评估',
}

const riskSegments = computed(() => {
  // Compute risk distribution from students array
  const dist: Record<string, number> = {}
  for (const s of studentList.value) {
    const key = s.risk_level || 'unknown'
    dist[key] = (dist[key] || 0) + 1
  }
  return Object.entries(dist).map(([key, count]) => ({
    label: RISK_LABELS[key] || key,
    count,
    color: RISK_COLORS[key] || '#94a3b8',
  }))
})

const pieStyle = computed(() => {
  const segs = riskSegments.value
  const total = segs.reduce((s, seg) => s + seg.count, 0) || 1
  let acc = 0
  const stops = segs.map(seg => {
    const start = acc
    acc += (seg.count / total) * 100
    return `${seg.color} ${start}% ${acc}%`
  })
  if (!stops.length) return { background: 'var(--bhp-gray-100)' }
  return { background: `conic-gradient(${stops.join(', ')})` }
})

onMounted(() => loadDashboard())

async function loadDashboard() {
  loading.value = true
  try {
    const res = await http.get<any>('/v1/coach/dashboard')
    coachInfo.value   = res.coach || {}
    todayStats.value  = res.today_stats || {}
    studentList.value = res.students || []
    // Build todos from students needing followup
    const todoItems = res.todos || res.pending_tasks || []
    if (todoItems.length) {
      todos.value = todoItems.map((t: any) => ({ ...t, done: t.done ?? t.completed ?? false }))
    } else {
      // Auto-generate todos from pending followups
      todos.value = studentList.value
        .filter((s: any) => s.days_since_contact >= 7)
        .map((s: any) => ({ title: `跟进 ${s.name}（${s.last_contact}）`, done: false }))
    }
  } catch {
    todayStats.value = {}
  } finally {
    loading.value = false
  }
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.cd-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.cd-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.cd-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cd-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cd-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cd-navbar__placeholder { width: 64rpx; }
.cd-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

.cd-card { background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light); }
.cd-card__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 20rpx; }

.cd-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx; }
.cd-stat { text-align: center; padding: 16rpx; background: var(--surface-secondary); border-radius: var(--radius-md); }
.cd-stat__val { display: block; font-size: 36rpx; font-weight: 800; color: var(--bhp-primary-600); }
.cd-stat__label { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }

.cd-pie-wrap { display: flex; align-items: center; gap: 32rpx; }
.cd-pie { width: 160rpx; height: 160rpx; border-radius: 50%; flex-shrink: 0; }
.cd-pie-legend { flex: 1; display: flex; flex-direction: column; gap: 12rpx; }
.cd-legend-item { display: flex; align-items: center; gap: 12rpx; }
.cd-legend-dot { width: 20rpx; height: 20rpx; border-radius: 50%; flex-shrink: 0; }
.cd-legend-label { font-size: 24rpx; color: var(--text-secondary); flex: 1; }
.cd-legend-val { font-size: 24rpx; font-weight: 700; color: var(--text-primary); }

.cd-todos { display: flex; flex-direction: column; gap: 12rpx; }
.cd-todo { display: flex; align-items: flex-start; gap: 12rpx; }
.cd-todo--done { opacity: 0.5; }
.cd-todo__check { font-size: 32rpx; cursor: pointer; flex-shrink: 0; line-height: 1; }
.cd-todo__body { flex: 1; }
.cd-todo__text { display: block; font-size: 26rpx; color: var(--text-primary); }
.cd-todo--done .cd-todo__text { text-decoration: line-through; }
.cd-todo__sub { display: block; font-size: 22rpx; color: var(--text-tertiary); margin-top: 2rpx; }
.cd-empty-todo { text-align: center; padding: 32rpx; }
</style>
