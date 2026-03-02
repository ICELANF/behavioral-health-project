<template>
  <view class="risk-page">
    <!-- 导航栏 -->
    <view class="risk-navbar">
      <view class="risk-nav-back" @tap="goBack">←</view>
      <text class="risk-nav-title">风险管理</text>
      <view class="risk-nav-action" @tap="refresh">↻</view>
    </view>

    <!-- 风险概览 -->
    <view class="risk-overview">
      <view class="risk-stat" v-for="s in riskStats" :key="s.label">
        <text class="risk-stat-num" :style="{ color: s.color }">{{ s.value }}</text>
        <text class="risk-stat-label">{{ s.label }}</text>
      </view>
    </view>

    <!-- 风险等级Tab -->
    <view class="risk-tabs">
      <view
        v-for="tab in tabs" :key="tab.key"
        class="risk-tab" :class="{ 'risk-tab--active': activeTab === tab.key }"
        @tap="activeTab = tab.key"
      >
        <text>{{ tab.label }}</text>
        <view v-if="tab.count > 0" class="risk-badge" :style="{ background: tab.color }">{{ tab.count }}</view>
      </view>
    </view>

    <!-- 学员风险列表 -->
    <scroll-view scroll-y class="risk-list" @scrolltolower="loadMore" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-for="student in filteredStudents" :key="student.id" class="risk-card" @tap="goDetail(student.id)">
        <view class="risk-card-header">
          <view class="risk-avatar">{{ (student.name || '?')[0] }}</view>
          <view class="risk-card-info">
            <text class="risk-card-name">{{ student.name }}</text>
            <text class="risk-card-meta">{{ student.stage || '未评估' }} · 最近活跃 {{ student.days_since || '—' }}天前</text>
          </view>
          <view class="risk-level-badge" :style="{ background: riskColor(student.risk_level) }">
            R{{ student.risk_level || 0 }}
          </view>
        </view>
        <!-- 风险因素 -->
        <view class="risk-factors" v-if="student.risk_factors && student.risk_factors.length">
          <view class="risk-factor-tag" v-for="(f, i) in student.risk_factors.slice(0, 3)" :key="i">{{ f }}</view>
        </view>
        <!-- 干预状态 -->
        <view class="risk-card-footer">
          <text class="risk-intervention-status" :style="{ color: student.has_intervention ? '#27AE60' : '#E67E22' }">
            {{ student.has_intervention ? '✓ 已有干预方案' : '⚠ 待干预' }}
          </text>
          <text class="risk-card-arrow">›</text>
        </view>
      </view>

      <view v-if="filteredStudents.length === 0" class="risk-empty">
        <text class="risk-empty-icon">🛡️</text>
        <text class="risk-empty-text">当前无{{ activeTab === 'all' ? '' : activeTab === 'high' ? '高风险' : activeTab === 'medium' ? '中风险' : '待跟进' }}学员</text>
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

interface Student {
  id: number
  name: string
  risk_level: number
  stage?: string
  days_since?: number
  risk_factors?: string[]
  has_intervention?: boolean
}

const activeTab = ref('all')
const students = ref<Student[]>([])
const loading = ref(false)
const refreshing = ref(false)

const tabs = computed(() => [
  { key: 'all', label: '全部', count: students.value.length, color: '#5B6B7F' },
  { key: 'high', label: '高风险', count: students.value.filter(s => s.risk_level >= 3).length, color: '#E74C3C' },
  { key: 'medium', label: '中风险', count: students.value.filter(s => s.risk_level === 2).length, color: '#E67E22' },
  { key: 'followup', label: '待跟进', count: students.value.filter(s => (s.days_since || 0) >= 7).length, color: '#3498DB' },
])

const riskStats = computed(() => [
  { label: '高风险', value: students.value.filter(s => s.risk_level >= 3).length, color: '#E74C3C' },
  { label: '中风险', value: students.value.filter(s => s.risk_level === 2).length, color: '#E67E22' },
  { label: '低风险', value: students.value.filter(s => s.risk_level <= 1).length, color: '#27AE60' },
  { label: '待跟进', value: students.value.filter(s => (s.days_since || 0) >= 7).length, color: '#3498DB' },
])

const filteredStudents = computed(() => {
  if (activeTab.value === 'all') return students.value
  if (activeTab.value === 'high') return students.value.filter(s => s.risk_level >= 3)
  if (activeTab.value === 'medium') return students.value.filter(s => s.risk_level === 2)
  if (activeTab.value === 'followup') return students.value.filter(s => (s.days_since || 0) >= 7)
  return students.value
})

function riskColor(level: number): string {
  if (level >= 4) return '#C0392B'
  if (level >= 3) return '#E74C3C'
  if (level >= 2) return '#E67E22'
  if (level >= 1) return '#F1C40F'
  return '#27AE60'
}

async function loadStudents() {
  loading.value = true
  try {
    // 从 dashboard 获取学员列表（含风险数据）
    const res = await http<any>('/api/v1/coach/dashboard')
    const raw = res.students || res.data?.students || []
    students.value = raw.map((s: any) => ({
      id: s.id || s.user_id,
      name: s.name || s.full_name || s.username || '未知',
      risk_level: s.risk_level ?? s.risk_score ?? 0,
      stage: s.ttm_stage || s.stage || '',
      days_since: s.days_since_last_contact ?? s.days_since ?? null,
      risk_factors: s.risk_factors || [],
      has_intervention: s.has_prescription ?? s.has_intervention ?? false,
    }))
    // 按风险等级降序
    students.value.sort((a, b) => (b.risk_level || 0) - (a.risk_level || 0))
  } catch (e) {
    console.warn('[Risk] load failed:', e)
    // fallback: 尝试 coach/students
    try {
      const res2 = await http<any>('/api/v1/coach/students')
      const raw2 = res2.items || res2.students || res2 || []
      students.value = (Array.isArray(raw2) ? raw2 : []).map((s: any) => ({
        id: s.id || s.user_id,
        name: s.name || s.full_name || '未知',
        risk_level: s.risk_level ?? 0,
        stage: s.ttm_stage || '',
        days_since: s.days_since_last_contact ?? null,
        risk_factors: [],
        has_intervention: false,
      }))
    } catch {}
  }
  loading.value = false
}

async function onRefresh() {
  refreshing.value = true
  await loadStudents()
  refreshing.value = false
}

function refresh() { loadStudents() }
function loadMore() {}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

function goDetail(id: number) {
  uni.navigateTo({ url: '/pages/coach/students/detail?id=' + id })
}

onMounted(() => { loadStudents() })
</script>

<style scoped>
.risk-page { min-height: 100vh; background: #F5F6FA; }
.risk-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); color: #fff; }
.risk-nav-back { font-size: 40rpx; padding: 16rpx; }
.risk-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.risk-nav-action { font-size: 36rpx; padding: 16rpx; }

.risk-overview { display: flex; padding: 24rpx; gap: 16rpx; }
.risk-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx 12rpx; text-align: center; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06); }
.risk-stat-num { display: block; font-size: 44rpx; font-weight: 700; }
.risk-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.risk-tabs { display: flex; padding: 0 24rpx; gap: 16rpx; margin-bottom: 16rpx; }
.risk-tab { display: flex; align-items: center; gap: 8rpx; padding: 12rpx 24rpx; border-radius: 32rpx; background: #fff; font-size: 26rpx; color: #5B6B7F; }
.risk-tab--active { background: #E74C3C; color: #fff; }
.risk-badge { min-width: 32rpx; height: 32rpx; border-radius: 16rpx; color: #fff; font-size: 20rpx; display: flex; align-items: center; justify-content: center; padding: 0 8rpx; }

.risk-list { height: calc(100vh - 500rpx); padding: 0 24rpx; }
.risk-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.risk-card-header { display: flex; align-items: center; gap: 16rpx; }
.risk-avatar { width: 72rpx; height: 72rpx; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 28rpx; font-weight: 600; }
.risk-card-info { flex: 1; }
.risk-card-name { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.risk-card-meta { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.risk-level-badge { padding: 6rpx 16rpx; border-radius: 8rpx; color: #fff; font-size: 24rpx; font-weight: 700; }

.risk-factors { display: flex; flex-wrap: wrap; gap: 8rpx; margin-top: 16rpx; }
.risk-factor-tag { padding: 4rpx 12rpx; border-radius: 6rpx; background: #FFF3E0; color: #E67E22; font-size: 22rpx; }

.risk-card-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 16rpx; padding-top: 16rpx; border-top: 1rpx solid #F0F0F0; }
.risk-intervention-status { font-size: 24rpx; }
.risk-card-arrow { font-size: 32rpx; color: #CCC; }

.risk-empty { text-align: center; padding: 120rpx 0; }
.risk-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.risk-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>