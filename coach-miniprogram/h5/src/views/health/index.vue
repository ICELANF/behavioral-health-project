<template>
  <view class="hi-page">
    <view class="hi-navbar">
      <view class="hi-nav-back" @tap="goBack">←</view>
      <text class="hi-nav-title">健康数据</text>
      <view class="hi-nav-action" @tap="goPage('/pages/health/device-bind')">设备</view>
    </view>

    <scroll-view scroll-y class="hi-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 今日概览卡片 -->
      <view class="hi-summary">
        <view class="hi-sum-row">
          <view class="hi-sum-item" @tap="goPage('/pages/health/blood-glucose')">
            <text class="hi-sum-icon">🩸</text>
            <text class="hi-sum-val">{{ summary.glucose ?? '—' }}</text>
            <text class="hi-sum-unit">mmol/L</text>
            <text class="hi-sum-label">血糖</text>
            <text class="hi-sum-hint" :style="{ color: glucoseColor }">{{ glucoseHint }}</text>
          </view>
          <view class="hi-sum-item" @tap="goPage('/pages/health/weight')">
            <text class="hi-sum-icon">⚖️</text>
            <text class="hi-sum-val">{{ summary.weight ?? '—' }}</text>
            <text class="hi-sum-unit">kg</text>
            <text class="hi-sum-label">体重</text>
            <text class="hi-sum-hint" style="color:#8E99A4;">BMI {{ summary.bmi ?? '—' }}</text>
          </view>
        </view>
        <view class="hi-sum-row">
          <view class="hi-sum-item" @tap="goPage('/pages/health/exercise')">
            <text class="hi-sum-icon">👟</text>
            <text class="hi-sum-val">{{ summary.steps ?? '—' }}</text>
            <text class="hi-sum-unit">步</text>
            <text class="hi-sum-label">今日步数</text>
            <text class="hi-sum-hint" :style="{ color: stepsColor }">{{ stepsHint }}</text>
          </view>
          <view class="hi-sum-item">
            <text class="hi-sum-icon">😴</text>
            <text class="hi-sum-val">{{ summary.sleep ?? '—' }}</text>
            <text class="hi-sum-unit">小时</text>
            <text class="hi-sum-label">昨晚睡眠</text>
            <text class="hi-sum-hint" :style="{ color: sleepColor }">{{ sleepHint }}</text>
          </view>
        </view>
      </view>

      <!-- 快速记录 -->
      <view class="hi-section-title">⚡ 快速记录</view>
      <view class="hi-quick-row">
        <view class="hi-quick-btn" @tap="goPage('/pages/health/blood-glucose')">
          <text class="hi-quick-icon">🩸</text>
          <text class="hi-quick-label">记录血糖</text>
        </view>
        <view class="hi-quick-btn" @tap="goPage('/pages/health/weight')">
          <text class="hi-quick-icon">⚖️</text>
          <text class="hi-quick-label">记录体重</text>
        </view>
        <view class="hi-quick-btn" @tap="goPage('/pages/health/exercise')">
          <text class="hi-quick-icon">🏃</text>
          <text class="hi-quick-label">运动记录</text>
        </view>
        <view class="hi-quick-btn" @tap="goPage('/pages/food/scan')">
          <text class="hi-quick-icon">🥗</text>
          <text class="hi-quick-label">记录饮食</text>
        </view>
      </view>

      <!-- 设备状态 -->
      <view class="hi-section-title">📡 我的设备</view>
      <view class="hi-devices">
        <view v-if="devices.length > 0">
          <view v-for="d in devices" :key="d.id" class="hi-device-item">
            <text class="hi-device-icon">{{ deviceIcon(d.device_type) }}</text>
            <view class="hi-device-info">
              <text class="hi-device-name">{{ d.manufacturer || '' }} {{ d.model || d.device_type }}</text>
              <text class="hi-device-status">{{ d.status === 'active' ? '已连接' : '未连接' }} · 上次同步 {{ formatTime(d.last_sync_at) }}</text>
            </view>
            <view class="hi-device-dot" :style="{ background: d.status === 'active' ? '#27AE60' : '#BDC3C7' }"></view>
          </view>
        </view>
        <view v-else class="hi-device-empty" @tap="goPage('/pages/health/device-bind')">
          <text>＋ 绑定穿戴设备</text>
        </view>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const refreshing = ref(false)
const summary = ref<any>({})
const devices = ref<any[]>([])

const glucoseColor = computed(() => {
  const v = summary.value.glucose
  if (!v) return '#8E99A4'
  if (v < 3.9 || v > 10) return '#E74C3C'
  if (v > 7.8) return '#E67E22'
  return '#27AE60'
})
const glucoseHint = computed(() => {
  const v = summary.value.glucose
  if (!v) return '尚未记录'
  if (v < 3.9) return '偏低'
  if (v > 10) return '偏高'
  if (v > 7.8) return '需关注'
  return '正常范围'
})
const stepsColor = computed(() => {
  const v = summary.value.steps
  if (!v) return '#8E99A4'
  return v >= 8000 ? '#27AE60' : v >= 5000 ? '#E67E22' : '#E74C3C'
})
const stepsHint = computed(() => {
  const v = summary.value.steps
  if (!v) return '未获取'
  if (v >= 10000) return '完成目标'
  if (v >= 8000) return '良好'
  if (v >= 5000) return '继续加油'
  return '运动不足'
})
const sleepColor = computed(() => {
  const v = summary.value.sleep
  if (!v) return '#8E99A4'
  return v >= 7 ? '#27AE60' : v >= 6 ? '#E67E22' : '#E74C3C'
})
const sleepHint = computed(() => {
  const v = summary.value.sleep
  if (!v) return '未记录'
  if (v >= 7) return '充足'
  if (v >= 6) return '略少'
  return '睡眠不足'
})

function deviceIcon(type: string): string {
  const m: Record<string,string> = {
    cgm:'🩸', glucometer:'🩸', smartwatch:'⌚', fitness_band:'📿',
    smart_scale:'⚖️', blood_pressure_monitor:'💓', pulse_oximeter:'🫁', sleep_tracker:'😴',
  }
  return m[type] || '📱'
}

function formatTime(t: string): string {
  if (!t) return '从未'
  const d = new Date(t)
  const diff = (Date.now() - d.getTime()) / 1000 / 60
  if (diff < 60) return `${Math.round(diff)}分钟前`
  if (diff < 1440) return `${Math.round(diff/60)}小时前`
  return `${Math.round(diff/1440)}天前`
}

async function loadData() {
  try {
    const res = await http<any>('/api/v1/health-data/summary')
    summary.value = {
      glucose: res.latest_glucose?.value?.toFixed(1) ?? null,
      weight:  res.latest_weight?.toFixed(1) ?? null,
      bmi:     res.bmi?.toFixed(1) ?? null,
      steps:   res.today_steps ?? null,
      sleep:   res.last_sleep_hours?.toFixed(1) ?? null,
    }
  } catch (e) { console.warn('[health/index] summary:', e) }
  try {
    const res = await http<any>('/api/v1/devices')
    devices.value = res.devices || res.items || (Array.isArray(res) ? res : [])
  } catch (e) { console.warn('[health/index] devices:', e) }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
function goPage(url: string) { uni.navigateTo({ url }) }
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/home/index' })
}

onMounted(() => loadData())
</script>

<style scoped>
.hi-page { min-height: 100vh; background: #F0F7FF; }
.hi-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #1565C0 0%, #1E88E5 100%); color: #fff; }
.hi-nav-back { font-size: 40rpx; padding: 16rpx; }
.hi-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.hi-nav-action { font-size: 26rpx; padding: 8rpx 16rpx; background: rgba(255,255,255,0.2); border-radius: 8rpx; }
.hi-scroll { height: calc(100vh - 180rpx); }

.hi-summary { margin: 24rpx; background: #fff; border-radius: 20rpx; padding: 24rpx; }
.hi-sum-row { display: flex; gap: 16rpx; margin-bottom: 16rpx; }
.hi-sum-row:last-child { margin-bottom: 0; }
.hi-sum-item { flex: 1; background: #F0F7FF; border-radius: 16rpx; padding: 20rpx; display: flex; flex-direction: column; align-items: center; text-align: center; }
.hi-sum-icon  { font-size: 32rpx; margin-bottom: 8rpx; }
.hi-sum-val   { font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.hi-sum-unit  { font-size: 18rpx; color: #8E99A4; }
.hi-sum-label { font-size: 22rpx; color: #5B6B7F; margin-top: 6rpx; }
.hi-sum-hint  { font-size: 20rpx; margin-top: 4rpx; }

.hi-section-title { font-size: 28rpx; font-weight: 700; color: #2C3E50; margin: 0 24rpx 16rpx; }

.hi-quick-row { display: flex; gap: 16rpx; padding: 0 24rpx 24rpx; }
.hi-quick-btn { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx 8rpx; display: flex; flex-direction: column; align-items: center; gap: 8rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.hi-quick-icon  { font-size: 40rpx; }
.hi-quick-label { font-size: 22rpx; color: #5B6B7F; }

.hi-devices { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; overflow: hidden; }
.hi-device-item { display: flex; align-items: center; gap: 16rpx; padding: 24rpx; border-bottom: 1rpx solid #F8F8F8; }
.hi-device-item:last-child { border-bottom: none; }
.hi-device-icon { font-size: 36rpx; }
.hi-device-info { flex: 1; }
.hi-device-name   { display: block; font-size: 28rpx; color: #2C3E50; }
.hi-device-status { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.hi-device-dot { width: 16rpx; height: 16rpx; border-radius: 50%; }
.hi-device-empty { text-align: center; padding: 48rpx; font-size: 28rpx; color: #27AE60; }
</style>
