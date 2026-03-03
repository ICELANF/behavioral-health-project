<template>
  <view class="sc-page">
    <view class="sc-navbar">
      <view class="sc-back" @tap="goBack">←</view>
      <text class="sc-title">教练管理</text>
      <view style="width:80rpx;"></view>
    </view>
    <scroll-view scroll-y class="sc-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view class="sc-stat-row">
        <view class="sc-stat"><text class="sc-stat-num">{{ coaches.length }}</text><text class="sc-stat-label">教练总数</text></view>
        <view class="sc-stat">
          <text class="sc-stat-num" style="color:#E67E22;">{{ totalPending }}</text>
          <text class="sc-stat-label">待审总计</text>
        </view>
        <view class="sc-stat">
          <text class="sc-stat-num" style="color:#3498DB;">{{ totalStudents }}</text>
          <text class="sc-stat-label">学员总计</text>
        </view>
      </view>

      <view v-for="coach in coaches" :key="coach.id" class="sc-card">
        <view class="sc-avatar" :style="{ background: avatarColor(coach.name) }">{{ (coach.name || '?')[0] }}</view>
        <view class="sc-info">
          <view class="sc-name-row">
            <text class="sc-name">{{ coach.name }}</text>
            <view v-if="coach.risk_level" class="sc-risk-badge" :style="{ background: riskBg(coach.risk_level), color: riskColor(coach.risk_level) }">
              {{ riskLabel(coach.risk_level) }}
            </view>
          </view>
          <text class="sc-meta">学员 {{ coach.student_count || 0 }} 人 · 待审核 {{ coach.pending_review || 0 }} 条</text>
        </view>
        <view class="sc-contact-btn" @tap="contactCoach(coach)">联系</view>
      </view>

      <view v-if="!loading && coaches.length === 0" class="sc-empty">
        <text class="sc-empty-icon">👨‍🏫</text>
        <text class="sc-empty-text">暂无教练数据</text>
        <text class="sc-empty-hint">当前督导下无教练分配</text>
      </view>
      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

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

const loading = ref(false)
const refreshing = ref(false)
const coaches = ref<any[]>([])

const totalPending = computed(() => coaches.value.reduce((s, c) => s + (c.pending_review || 0), 0))
const totalStudents = computed(() => coaches.value.reduce((s, c) => s + (c.student_count || 0), 0))

const colorPool = ['#3498DB', '#E74C3C', '#27AE60', '#9B59B6', '#E67E22', '#1ABC9C']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0
  for (const c of name) h = c.charCodeAt(0) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}

function riskLabel(level: string): string {
  const m: Record<string, string> = { high: '高风险', medium: '中风险', low: '低风险' }
  return m[level] || level
}
function riskColor(level: string): string {
  const m: Record<string, string> = { high: '#E74C3C', medium: '#E67E22', low: '#27AE60' }
  return m[level] || '#8E99A4'
}
function riskBg(level: string): string {
  const m: Record<string, string> = { high: '#FFF0F0', medium: '#FFF7F0', low: '#F0FFF4' }
  return m[level] || '#F5F5F5'
}

function contactCoach(coach: any) {
  uni.showToast({ title: `联系 ${coach.name}`, icon: 'none' })
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/supervisor/coaches')
    coaches.value = res.coaches || []
  } catch {
    coaches.value = []
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
.sc-page { min-height: 100vh; background: #F5F6FA; }
.sc-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #D35400, #E67E22); color: #fff;
}
.sc-back { font-size: 40rpx; padding: 16rpx; }
.sc-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.sc-scroll { height: calc(100vh - 180rpx); }
.sc-stat-row { display: flex; margin: 24rpx; gap: 16rpx; }
.sc-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx; text-align: center; }
.sc-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.sc-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.sc-card {
  display: flex; align-items: center; gap: 16rpx;
  margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx;
}
.sc-avatar {
  width: 72rpx; height: 72rpx; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; font-weight: 700; flex-shrink: 0;
}
.sc-info { flex: 1; }
.sc-name-row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 6rpx; }
.sc-name { font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.sc-risk-badge { padding: 4rpx 12rpx; border-radius: 12rpx; font-size: 20rpx; font-weight: 600; }
.sc-meta { display: block; font-size: 22rpx; color: #8E99A4; }
.sc-contact-btn {
  padding: 12rpx 28rpx; border-radius: 12rpx;
  background: #E67E22; color: #fff; font-size: 24rpx; font-weight: 600;
}
.sc-empty { text-align: center; padding: 120rpx 0; }
.sc-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.sc-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; }
.sc-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 8rpx; }
</style>
