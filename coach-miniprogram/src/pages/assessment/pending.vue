<template>
  <view class="pending-page">
    <view class="pending-navbar">
      <view class="pending-nav-back" @tap="goBack">←</view>
      <text class="pending-nav-title">我的评估</text>
    </view>

    <scroll-view scroll-y class="pending-content" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 待完成 -->
      <view class="pending-section" v-if="pendingList.length">
        <text class="pending-section-title">⏳ 待完成 ({{ pendingList.length }})</text>
        <view v-for="item in pendingList" :key="item.id" class="pending-card pending-card--active" @tap="goAssessment(item)">
          <view class="pending-card-icon">📝</view>
          <view class="pending-card-info">
            <text class="pending-card-title">{{ item.assessment_name || item.scale_names || '综合评估' }}</text>
            <text class="pending-card-meta">分配教练: {{ item.coach_name || '系统分配' }}</text>
            <text class="pending-card-meta" v-if="item.deadline">截止: {{ formatDate(item.deadline) }}</text>
          </view>
          <view class="pending-go-btn">开始 →</view>
        </view>
      </view>

      <!-- 进行中（有草稿） -->
      <view class="pending-section" v-if="inProgressList.length">
        <text class="pending-section-title">✍️ 进行中 ({{ inProgressList.length }})</text>
        <view v-for="item in inProgressList" :key="item.id" class="pending-card pending-card--progress" @tap="goAssessment(item)">
          <view class="pending-card-icon">📊</view>
          <view class="pending-card-info">
            <text class="pending-card-title">{{ item.assessment_name || item.scale_names || '综合评估' }}</text>
            <view class="pending-progress-bar">
              <view class="pending-progress-fill" :style="{ width: (item.progress || 30) + '%' }"></view>
            </view>
            <text class="pending-card-meta">已完成 {{ item.progress || 30 }}%</text>
          </view>
          <view class="pending-go-btn">继续 →</view>
        </view>
      </view>

      <!-- 已完成 -->
      <view class="pending-section" v-if="completedList.length">
        <text class="pending-section-title">✅ 已完成 ({{ completedList.length }})</text>
        <view v-for="item in completedList" :key="item.id" class="pending-card pending-card--done" @tap="goResult(item)">
          <view class="pending-card-icon">📈</view>
          <view class="pending-card-info">
            <text class="pending-card-title">{{ item.assessment_name || item.scale_names || '综合评估' }}</text>
            <text class="pending-card-meta">完成时间: {{ formatDate(item.completed_at) }}</text>
            <text class="pending-card-meta" v-if="item.score != null">得分: {{ item.score }}</text>
          </view>
          <view class="pending-go-btn pending-go-view">查看 →</view>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="!loading && allItems.length === 0" class="pending-empty">
        <text class="pending-empty-icon">📋</text>
        <text class="pending-empty-text">暂无评估任务</text>
        <text class="pending-empty-hint">教练分配评估后会在这里显示</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'

function getToken(): string {
  return uni.getStorageSync('access_token') || ''
}

async function http<T = any>(url: string, options: any = {}): Promise<T> {
  const { method = 'GET', data } = options
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: {
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        if (res.statusCode === 401) {
          uni.removeStorageSync('access_token')
          uni.reLaunch({ url: '/pages/auth/login' })
          reject(new Error('401')); return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: (err: any) => reject(err)
    })
  })
}

const loading = ref(false)
const refreshing = ref(false)
const allItems = ref<any[]>([])

const pendingList = computed(() => allItems.value.filter(a => ['pending', 'assigned'].includes(a.status)))
const inProgressList = computed(() => allItems.value.filter(a => a.status === 'in_progress'))
const completedList = computed(() => allItems.value.filter(a => ['completed', 'submitted', 'reviewed'].includes(a.status)))

function formatDate(d: string): string { return d ? d.slice(0, 10) : '-' }

async function loadData() {
  loading.value = true
  // ★ 使用已验证端点 ★
  const endpoints = [
    '/api/v1/assessment-assignments/my-pending',
    '/api/v1/assessment-assignments/review-list',
    '/api/v1/assessment/user/latest',
  ]
  for (const ep of endpoints) {
    try {
      const res = await http<any>(ep)
      const list = res.items || res.assignments || (Array.isArray(res) ? res : [])
      if (list.length > 0 || allItems.value.length === 0) {
        allItems.value = [...allItems.value, ...list]
      }
    } catch { /* 继续尝试 */ }
  }
  // 去重
  const seen = new Set()
  allItems.value = allItems.value.filter(item => {
    const key = item.id || (item.student_id + '_' + item.assessment_type)
    if (seen.has(key)) return false
    seen.add(key); return true
  })
  loading.value = false
}

async function onRefresh() { refreshing.value = true; allItems.value = []; await loadData(); refreshing.value = false }

function goAssessment(item: any) {
  uni.navigateTo({ url: '/pages/assessment/do?id=' + item.id })
}

function goResult(item: any) {
  uni.navigateTo({ url: '/pages/assessment/result?id=' + item.id })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pending-page { min-height: 100vh; background: #F5F6FA; }
.pending-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.pending-nav-back { font-size: 40rpx; padding: 16rpx; }
.pending-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }

.pending-content { height: calc(100vh - 180rpx); padding: 24rpx; }
.pending-section { margin-bottom: 24rpx; }
.pending-section-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }

.pending-card { display: flex; align-items: center; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.pending-card--active { border-left: 6rpx solid #E67E22; }
.pending-card--progress { border-left: 6rpx solid #3498DB; }
.pending-card--done { border-left: 6rpx solid #27AE60; opacity: 0.85; }

.pending-card-icon { font-size: 48rpx; }
.pending-card-info { flex: 1; }
.pending-card-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 6rpx; }
.pending-card-meta { display: block; font-size: 22rpx; color: #8E99A4; }

.pending-progress-bar { height: 8rpx; background: #F0F0F0; border-radius: 4rpx; margin: 8rpx 0; overflow: hidden; }
.pending-progress-fill { height: 100%; background: #3498DB; border-radius: 4rpx; }

.pending-go-btn { padding: 12rpx 24rpx; background: #9B59B6; color: #fff; border-radius: 8rpx; font-size: 24rpx; white-space: nowrap; }
.pending-go-view { background: #27AE60; }

.pending-empty { text-align: center; padding: 200rpx 0; }
.pending-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.pending-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; margin-bottom: 8rpx; }
.pending-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; }
</style>