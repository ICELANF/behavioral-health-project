<template>
  <view class="sv-page">
    <view class="sv-navbar">
      <view class="sv-back" @tap="goBack">←</view>
      <text class="sv-title">督导工作台</text>
      <view style="width:80rpx;"></view>
    </view>
    <scroll-view scroll-y class="sv-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 统计卡片 -->
      <view class="sv-stat-grid">
        <view class="sv-stat-card">
          <text class="sv-stat-num">{{ stats.coach_count || 0 }}</text>
          <text class="sv-stat-label">管理教练数</text>
        </view>
        <view class="sv-stat-card">
          <text class="sv-stat-num" style="color:#E67E22;">{{ stats.pending_review || 0 }}</text>
          <text class="sv-stat-label">待审核</text>
        </view>
        <view class="sv-stat-card">
          <text class="sv-stat-num" style="color:#E74C3C;">{{ stats.high_risk_count || 0 }}</text>
          <text class="sv-stat-label">高风险</text>
        </view>
        <view class="sv-stat-card">
          <text class="sv-stat-num" style="color:#27AE60;">{{ stats.approved_today || 0 }}</text>
          <text class="sv-stat-label">今日审批</text>
        </view>
      </view>

      <!-- 快捷入口 -->
      <view class="sv-section-title">快捷入口</view>
      <view class="sv-shortcut-list">
        <view class="sv-shortcut-item" @tap="navTo('/pages/supervisor/coaches')">
          <view class="sv-shortcut-icon" style="background:#FFF3E0;">
            <text style="color:#E67E22; font-size:40rpx;">👨‍🏫</text>
          </view>
          <view class="sv-shortcut-info">
            <text class="sv-shortcut-name">教练管理</text>
            <text class="sv-shortcut-desc">查看所有教练及其学员</text>
          </view>
          <text class="sv-shortcut-arrow">›</text>
        </view>
        <view class="sv-shortcut-item" @tap="navTo('/pages/supervisor/review-queue')">
          <view class="sv-shortcut-icon" style="background:#FFF0E6;">
            <text style="color:#E74C3C; font-size:40rpx;">📋</text>
          </view>
          <view class="sv-shortcut-info">
            <text class="sv-shortcut-name">审核队列</text>
            <text class="sv-shortcut-desc">{{ stats.pending_review || 0 }} 条待审核</text>
          </view>
          <text class="sv-shortcut-arrow">›</text>
        </view>
        <view class="sv-shortcut-item" @tap="navTo('/pages/coach/analytics/index')">
          <view class="sv-shortcut-icon" style="background:#EEF6FF;">
            <text style="color:#3498DB; font-size:40rpx;">📊</text>
          </view>
          <view class="sv-shortcut-info">
            <text class="sv-shortcut-name">数据分析</text>
            <text class="sv-shortcut-desc">整体运营数据概览</text>
          </view>
          <text class="sv-shortcut-arrow">›</text>
        </view>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'

function getToken(): string {
  return uni.getStorageSync('access_token') || ''
}

async function http<T = any>(url: string, opts: any = {}): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method: opts.method || 'GET',
      data: opts.data,
      header: {
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json',
      },
      success: (res: any) => {
        if (res.statusCode === 401) {
          uni.removeStorageSync('access_token')
          uni.reLaunch({ url: '/pages/auth/login' })
          reject(new Error('401'))
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: reject,
    })
  })
}

const refreshing = ref(false)
const stats = ref({
  coach_count: 0,
  pending_review: 0,
  high_risk_count: 0,
  approved_today: 0,
})

async function loadData() {
  try {
    const res = await http<any>('/api/v1/supervisor/dashboard')
    stats.value = {
      coach_count: res.coach_count || 0,
      pending_review: res.pending_review || 0,
      high_risk_count: res.high_risk_count || 0,
      approved_today: res.approved_today || 0,
    }
  } catch {
    // API not yet implemented — keep zero defaults
  }
}

async function onRefresh() {
  refreshing.value = true
  await loadData()
  refreshing.value = false
}

function navTo(url: string) {
  uni.navigateTo({ url })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => loadData())
</script>

<style scoped>
.sv-page { min-height: 100vh; background: #F5F6FA; }
.sv-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #D35400, #E67E22); color: #fff;
}
.sv-back { font-size: 40rpx; padding: 16rpx; }
.sv-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.sv-scroll { height: calc(100vh - 180rpx); }
.sv-stat-grid { display: flex; flex-wrap: wrap; gap: 16rpx; margin: 24rpx; }
.sv-stat-card {
  flex: 1; min-width: calc(50% - 8rpx); background: #fff;
  border-radius: 16rpx; padding: 28rpx 20rpx; text-align: center; box-sizing: border-box;
}
.sv-stat-num { display: block; font-size: 44rpx; font-weight: 700; color: #2C3E50; }
.sv-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 6rpx; }
.sv-section-title { font-size: 28rpx; font-weight: 600; color: #2C3E50; margin: 8rpx 24rpx 12rpx; }
.sv-shortcut-list { margin: 0 24rpx; background: #fff; border-radius: 16rpx; overflow: hidden; }
.sv-shortcut-item {
  display: flex; align-items: center; gap: 20rpx; padding: 28rpx 24rpx;
  border-bottom: 1rpx solid #F5F6FA;
}
.sv-shortcut-item:last-child { border-bottom: none; }
.sv-shortcut-icon {
  width: 80rpx; height: 80rpx; border-radius: 20rpx;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sv-shortcut-info { flex: 1; }
.sv-shortcut-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.sv-shortcut-desc { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.sv-shortcut-arrow { font-size: 40rpx; color: #BDC3C7; }
</style>
