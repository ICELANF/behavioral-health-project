<template>
  <view class="jp-page">
    <scroll-view scroll-y class="jp-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 统计 -->
      <view class="jp-stats">
        <view class="jp-stat-item">
          <text class="jp-stat-num">{{ data.completed || 0 }}</text>
          <text class="jp-stat-label">已完成</text>
        </view>
        <view class="jp-stat-item">
          <text class="jp-stat-num">{{ data.total || 0 }}</text>
          <text class="jp-stat-label">总任务</text>
        </view>
        <view class="jp-stat-item">
          <text class="jp-stat-num">{{ remaining }}</text>
          <text class="jp-stat-label">待完成</text>
        </view>
      </view>

      <!-- 进度条 -->
      <view class="jp-progress-section">
        <view class="jp-progress-bar">
          <view class="jp-progress-fill" :style="{ width: progressPct + '%' }" />
        </view>
        <text class="jp-progress-text">完成 {{ data.completed || 0 }}/{{ data.total || 0 }} 项任务</text>
      </view>

      <!-- 任务列表 -->
      <view class="jp-task-list">
        <view v-for="task in tasks" :key="task.id" class="jp-task-item"
          :class="{ 'jp-task-item--done': task.completed }">
          <view class="jp-task-check">
            <text>{{ task.completed ? '✅' : '⬜' }}</text>
          </view>
          <view class="jp-task-body">
            <text class="jp-task-title">{{ task.title || task.name || '任务' }}</text>
            <text class="jp-task-desc">{{ task.description || task.desc }}</text>
            <text v-if="task.points" class="jp-task-points">+{{ task.points }} 积分</text>
          </view>
          <view v-if="task.completed" class="jp-task-badge-done">已完成</view>
        </view>
      </view>

      <view v-if="tasks.length === 0 && !loading" class="jp-empty">
        <text class="jp-empty-icon">📋</text>
        <text class="jp-empty-text">暂无进度任务</text>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const data = ref<any>({ completed: 0, total: 10, items: [] })
const refreshing = ref(false)
const loading = ref(false)

const tasks = computed(() => data.value?.items || [])
const remaining = computed(() => Math.max(0, (data.value?.total || 0) - (data.value?.completed || 0)))
const progressPct = computed(() => {
  const t = data.value?.total || 0
  const c = data.value?.completed || 0
  return t > 0 ? Math.round(c / t * 100) : 0
})

async function loadData() {
  loading.value = true
  try {
    data.value = await http<any>('/api/v1/journey/progress')
  } catch {} finally { loading.value = false }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.jp-page { min-height: 100vh; background: #F5F6FA; }
.jp-scroll { height: 100vh; }

.jp-stats { display: flex; background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); padding: 32rpx 0; }
.jp-stat-item { flex: 1; text-align: center; border-right: 1rpx solid rgba(255,255,255,0.3); }
.jp-stat-item:last-child { border-right: none; }
.jp-stat-num { display: block; font-size: 48rpx; font-weight: 700; color: #fff; }
.jp-stat-label { display: block; font-size: 22rpx; color: rgba(255,255,255,0.8); margin-top: 4rpx; }

.jp-progress-section { background: #fff; padding: 20rpx 32rpx; }
.jp-progress-bar { height: 12rpx; background: #F0F0F0; border-radius: 6rpx; overflow: hidden; margin-bottom: 10rpx; }
.jp-progress-fill { height: 100%; background: linear-gradient(90deg, #2D8E69, #3BAF7C); border-radius: 6rpx; min-width: 12rpx; }
.jp-progress-text { font-size: 22rpx; color: #8E99A4; }

.jp-task-list { padding: 16rpx 24rpx; }
.jp-task-item { display: flex; align-items: flex-start; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 20rpx 24rpx; margin-bottom: 12rpx; }
.jp-task-item--done { opacity: 0.7; }
.jp-task-check { font-size: 32rpx; flex-shrink: 0; }
.jp-task-body { flex: 1; }
.jp-task-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 6rpx; }
.jp-task-desc { display: block; font-size: 22rpx; color: #8E99A4; line-height: 1.5; }
.jp-task-points { display: block; font-size: 20rpx; color: #E67E22; margin-top: 6rpx; }
.jp-task-badge-done { background: #E8F8F0; color: #2D8E69; font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; white-space: nowrap; }

.jp-empty { text-align: center; padding: 100rpx 0; }
.jp-empty-icon { display: block; font-size: 64rpx; margin-bottom: 16rpx; }
.jp-empty-text { font-size: 26rpx; color: #8E99A4; }
</style>
