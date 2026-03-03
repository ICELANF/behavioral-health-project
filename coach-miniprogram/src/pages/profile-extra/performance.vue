<template>
  <view class="perf-page">
    <view class="perf-header">
      <text class="perf-title">我的绩效</text>
      <text class="perf-sub">教练工作数据</text>
    </view>

    <scroll-view scroll-y class="perf-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 核心指标 -->
      <view class="perf-kpi-grid">
        <view class="perf-kpi-card">
          <text class="perf-kpi-num">{{ stats.student_count || 0 }}</text>
          <text class="perf-kpi-label">管理学员</text>
        </view>
        <view class="perf-kpi-card">
          <text class="perf-kpi-num">{{ stats.total_interventions || 0 }}</text>
          <text class="perf-kpi-label">干预次数</text>
        </view>
        <view class="perf-kpi-card">
          <text class="perf-kpi-num">{{ stats.assessments_reviewed || 0 }}</text>
          <text class="perf-kpi-label">完成评审</text>
        </view>
        <view class="perf-kpi-card">
          <text class="perf-kpi-num">{{ stats.total_days || 0 }}</text>
          <text class="perf-kpi-label">服务天数</text>
        </view>
      </view>

      <!-- 今日数据 -->
      <view class="perf-today">
        <text class="perf-section-title">今日数据</text>
        <view class="perf-today-row">
          <view class="perf-today-item">
            <text class="perf-today-label">今日消息</text>
            <text class="perf-today-val">{{ today.messages || 0 }}</text>
          </view>
          <view class="perf-today-item">
            <text class="perf-today-label">待处理</text>
            <text class="perf-today-val">{{ today.pending || 0 }}</text>
          </view>
          <view class="perf-today-item">
            <text class="perf-today-label">高风险</text>
            <text class="perf-today-val">{{ today.alert_count || 0 }}</text>
          </view>
        </view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const stats = ref<any>({})
const today = ref<any>({})
const refreshing = ref(false)

async function loadData() {
  try {
    const dash = await http<any>('/api/v1/coach/dashboard')
    stats.value = {
      student_count: dash?.today_stats?.total_students || (dash?.students || []).length || 0,
      total_interventions: dash?.today_stats?.total_interventions || 0,
      assessments_reviewed: dash?.today_stats?.assessments_reviewed || 0,
      total_days: dash?.coach?.total_days || 0,
    }
    today.value = {
      messages: dash?.today_stats?.messages_sent || 0,
      pending: dash?.today_stats?.pending_followups || 0,
      alert_count: dash?.today_stats?.alert_students || 0,
    }
  } catch (e) { console.warn('[profile-extra/performance] dashboard:', e) }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.perf-page { min-height: 100vh; background: #F5F6FA; }
.perf-header { padding: 24rpx 32rpx; padding-top: calc(80rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
.perf-title { display: block; font-size: 38rpx; font-weight: 700; }
.perf-sub { display: block; font-size: 24rpx; opacity: 0.85; margin-top: 6rpx; }
.perf-scroll { height: calc(100vh - 200rpx); }
.perf-kpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx; padding: 24rpx; }
.perf-kpi-card { background: #fff; border-radius: 16rpx; padding: 28rpx; text-align: center; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.perf-kpi-num { display: block; font-size: 48rpx; font-weight: 700; color: #2D8E69; margin-bottom: 8rpx; }
.perf-kpi-label { font-size: 24rpx; color: #8E99A4; }
.perf-today { background: #fff; margin: 0 24rpx 16rpx; border-radius: 16rpx; padding: 20rpx 24rpx; }
.perf-section-title { display: block; font-size: 28rpx; font-weight: 700; color: #2C3E50; margin-bottom: 16rpx; }
.perf-today-row { display: flex; }
.perf-today-item { flex: 1; text-align: center; border-right: 1rpx solid #F0F0F0; }
.perf-today-item:last-child { border-right: none; }
.perf-today-label { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 8rpx; }
.perf-today-val { font-size: 40rpx; font-weight: 700; color: #2C3E50; }
</style>
