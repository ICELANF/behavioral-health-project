<template>
  <view class="md-page">
    <view class="md-navbar">
      <view class="md-back" @tap="goBack">←</view>
      <text class="md-title">专家工作台</text>
      <view style="width:80rpx;"></view>
    </view>
    <scroll-view scroll-y class="md-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 统计卡片 -->
      <view class="md-stat-grid">
        <view class="md-stat-card" @tap="navTo('/pages/master/critical-review')">
          <text class="md-stat-num" style="color:#E74C3C;">{{ stats.critical_count || 0 }}</text>
          <text class="md-stat-label">危急病例 ›</text>
        </view>
        <view class="md-stat-card">
          <text class="md-stat-num" style="color:#E67E22;">{{ stats.ai_pending || 0 }}</text>
          <text class="md-stat-label">AI分析待审</text>
        </view>
        <view class="md-stat-card" @tap="navTo('/pages/master/knowledge')">
          <text class="md-stat-num" style="color:#9B59B6;">{{ stats.knowledge_pending || 0 }}</text>
          <text class="md-stat-label">知识待发布 ›</text>
        </view>
        <view class="md-stat-card">
          <text class="md-stat-num" style="color:#27AE60;">{{ stats.reviewed_today || 0 }}</text>
          <text class="md-stat-label">今日审核</text>
        </view>
      </view>

      <!-- 快捷入口 -->
      <view class="md-section-title">快捷入口</view>
      <view class="md-shortcut-list">
        <view class="md-shortcut-item" @tap="navTo('/pages/master/critical-review')">
          <view class="md-shortcut-icon" style="background:#FFF0F0;">
            <text style="color:#E74C3C; font-size:40rpx;">🚨</text>
          </view>
          <view class="md-shortcut-info">
            <text class="md-shortcut-name">危急审核</text>
            <text class="md-shortcut-desc">{{ stats.critical_count || 0 }} 例危急病例待处理</text>
          </view>
          <text class="md-shortcut-arrow">›</text>
        </view>
        <view class="md-shortcut-item" @tap="navTo('/pages/master/knowledge')">
          <view class="md-shortcut-icon" style="background:#F5EEF8;">
            <text style="color:#9B59B6; font-size:40rpx;">📚</text>
          </view>
          <view class="md-shortcut-info">
            <text class="md-shortcut-name">知识库</text>
            <text class="md-shortcut-desc">{{ stats.knowledge_pending || 0 }} 条内容待审发布</text>
          </view>
          <text class="md-shortcut-arrow">›</text>
        </view>
        <view class="md-shortcut-item" @tap="navTo('/pages/coach/analytics/index')">
          <view class="md-shortcut-icon" style="background:#EEF6FF;">
            <text style="color:#3498DB; font-size:40rpx;">📊</text>
          </view>
          <view class="md-shortcut-info">
            <text class="md-shortcut-name">数据概览</text>
            <text class="md-shortcut-desc">全平台运营数据分析</text>
          </view>
          <text class="md-shortcut-arrow">›</text>
        </view>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const refreshing = ref(false)
const stats = ref({
  critical_count: 0,
  ai_pending: 0,
  knowledge_pending: 0,
  reviewed_today: 0,
})

async function loadData() {
  try {
    const res = await http<any>('/api/v1/master/dashboard')
    stats.value = {
      critical_count: res.critical_count || 0,
      ai_pending: res.ai_pending || 0,
      knowledge_pending: res.knowledge_pending || 0,
      reviewed_today: res.reviewed_today || 0,
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
.md-page { min-height: 100vh; background: #F5F6FA; }
.md-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #7D3C98, #9B59B6); color: #fff;
}
.md-back { font-size: 40rpx; padding: 16rpx; }
.md-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.md-scroll { height: calc(100vh - 180rpx); }
.md-stat-grid { display: flex; flex-wrap: wrap; gap: 16rpx; margin: 24rpx; }
.md-stat-card {
  flex: 1; min-width: calc(50% - 8rpx); background: #fff;
  border-radius: 16rpx; padding: 28rpx 20rpx; text-align: center; box-sizing: border-box;
}
.md-stat-num { display: block; font-size: 44rpx; font-weight: 700; color: #2C3E50; }
.md-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 6rpx; }
.md-section-title { font-size: 28rpx; font-weight: 600; color: #2C3E50; margin: 8rpx 24rpx 12rpx; }
.md-shortcut-list { margin: 0 24rpx; background: #fff; border-radius: 16rpx; overflow: hidden; }
.md-shortcut-item {
  display: flex; align-items: center; gap: 20rpx; padding: 28rpx 24rpx;
  border-bottom: 1rpx solid #F5F6FA;
}
.md-shortcut-item:last-child { border-bottom: none; }
.md-shortcut-icon {
  width: 80rpx; height: 80rpx; border-radius: 20rpx;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.md-shortcut-info { flex: 1; }
.md-shortcut-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.md-shortcut-desc { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.md-shortcut-arrow { font-size: 40rpx; color: #BDC3C7; }
</style>
