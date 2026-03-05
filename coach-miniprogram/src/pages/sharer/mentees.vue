<template>
  <view class="mt-page">
    <view class="mt-navbar">
      <view class="mt-back" @tap="goBack">←</view>
      <text class="mt-title">我的伙伴</text>
      <view style="width:80rpx;"></view>
    </view>
    <scroll-view scroll-y class="mt-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view class="mt-stat-row">
        <view class="mt-stat"><text class="mt-stat-num">{{ mentees.length }}</text><text class="mt-stat-label">伙伴总数</text></view>
        <view class="mt-stat"><text class="mt-stat-num" style="color:#27AE60;">{{ activeCount }}</text><text class="mt-stat-label">今日打卡</text></view>
        <view class="mt-stat"><text class="mt-stat-num" style="color:#E74C3C;">{{ inactiveCount }}</text><text class="mt-stat-label">未打卡</text></view>
      </view>

      <view v-for="m in mentees" :key="m.id" class="mt-card">
        <view class="mt-avatar" :style="{ background: avatarColor(m.name) }">{{ (m.name || '?')[0] }}</view>
        <view class="mt-info">
          <text class="mt-name">{{ m.name }}</text>
          <text class="mt-meta">连续打卡 {{ m.streak || 0 }} 天 · 上次活跃 {{ m.last_active || '—' }}</text>
          <view class="mt-progress-bar">
            <view
              class="mt-progress-fill"
              :style="{ width: (m.today_pct || 0) + '%', background: m.status === 'active' ? '#27AE60' : '#E67E22' }"
            ></view>
          </view>
        </view>
        <view
          class="mt-badge"
          :style="{ background: m.status === 'active' ? '#E8F8F0' : '#FFF0F0', color: m.status === 'active' ? '#27AE60' : '#E74C3C' }"
        >
          {{ m.status === 'active' ? '已打卡' : '未打卡' }}
        </view>
      </view>

      <view v-if="!loading && mentees.length === 0" class="mt-empty">
        <text class="mt-empty-icon">👥</text>
        <text class="mt-empty-text">暂无伙伴</text>
        <text class="mt-empty-hint">联系教练了解如何引导成长伙伴</text>
      </view>
      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'
import { avatarColor } from '@/utils/studentUtils'

const loading = ref(false)
const refreshing = ref(false)
const mentees = ref<any[]>([])

const activeCount = computed(() => mentees.value.filter(m => m.status === 'active').length)
const inactiveCount = computed(() => mentees.value.filter(m => m.status !== 'active').length)


async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/sharer/mentee-progress')
    mentees.value = res.mentees || []
  } catch {
    mentees.value = []
  }
  loading.value = false
}

async function onRefresh() {
  refreshing.value = true
  await loadData()
  refreshing.value = false
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => loadData())
</script>

<style scoped>
.mt-page { min-height: 100vh; background: #F5F6FA; }
.mt-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2980B9, #3498DB); color: #fff;
}
.mt-back { font-size: 40rpx; padding: 16rpx; }
.mt-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.mt-scroll { height: calc(100vh - 180rpx); }
.mt-stat-row { display: flex; margin: 24rpx; gap: 16rpx; }
.mt-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx; text-align: center; }
.mt-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.mt-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.mt-card {
  display: flex; align-items: center; gap: 16rpx;
  margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx;
}
.mt-avatar {
  width: 72rpx; height: 72rpx; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; font-weight: 700; flex-shrink: 0;
}
.mt-info { flex: 1; }
.mt-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.mt-meta { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.mt-progress-bar { height: 6rpx; background: #F0F0F0; border-radius: 3rpx; overflow: hidden; margin-top: 10rpx; }
.mt-progress-fill { height: 100%; border-radius: 3rpx; }
.mt-badge { padding: 6rpx 16rpx; border-radius: 20rpx; font-size: 22rpx; font-weight: 600; white-space: nowrap; }
.mt-empty { text-align: center; padding: 120rpx 0; }
.mt-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.mt-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; }
.mt-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 8rpx; }
</style>
