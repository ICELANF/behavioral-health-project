<template>
  <view class="risk-page">
    <!-- 导航栏 -->
    <view class="risk-navbar">
      <view class="risk-nav-back" @tap="goBack">←</view>
      <text class="risk-nav-title">风险管理</text>
      <view class="risk-nav-action" @tap="refresh">↻</view>
    </view>

    <!-- 统计 + Tab 合并单排 -->
    <view class="risk-stattabs">
      <view
        v-for="t in statTabs" :key="t.key"
        class="risk-st" :class="{ 'risk-st--active': activeTab === t.key }"
        @tap="activeTab = t.key"
      >
        <text class="risk-st-num" :style="activeTab === t.key ? {} : { color: t.color }">{{ t.count }}</text>
        <text class="risk-st-label">{{ t.label }}</text>
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
        <text class="risk-empty-text">当前无{{ statTabs.find(t => t.key === activeTab)?.label || '' }}学员</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'
import { riskColor } from '@/utils/studentUtils'

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

// 统计 + Tab 合并：单排四格，数字展示 + 筛选器二合一
const statTabs = computed(() => [
  { key: 'all',      label: '全部',  color: '#5B6B7F', count: students.value.length },
  { key: 'high',     label: '高风险', color: '#E74C3C', count: students.value.filter(s => s.risk_level >= 3).length },
  { key: 'medium',   label: '中风险', color: '#E67E22', count: students.value.filter(s => s.risk_level === 2).length },
  { key: 'followup', label: '待跟进', color: '#3498DB', count: students.value.filter(s => (s.days_since || 0) >= 7).length },
])

const filteredStudents = computed(() => {
  if (activeTab.value === 'all') return students.value
  if (activeTab.value === 'high') return students.value.filter(s => s.risk_level >= 3)
  if (activeTab.value === 'medium') return students.value.filter(s => s.risk_level === 2)
  if (activeTab.value === 'followup') return students.value.filter(s => (s.days_since || 0) >= 7)
  return students.value
})

async function loadStudents() {
  loading.value = true
  try {
    // 从 dashboard 获取学员列表（含风险数据）
    const res = await http<any>('/api/v1/coach/dashboard')
    const raw = res.students || res.data?.students || []
    students.value = raw.map((s: any) => ({
      id: s.id || s.user_id,
      name: s.name || s.full_name || s.username || '未知',
      // 兼容字符串 "R3" 和数字 3
      risk_level: parseInt(String(s.risk_level ?? s.risk_score ?? '0').replace(/\D/g, '') || '0'),
      stage: s.ttm_stage || s.stage || s.stage_label || '',
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
        risk_level: parseInt(String(s.risk_level ?? '0').replace(/\D/g, '') || '0'),
        stage: s.ttm_stage || s.stage_label || '',
        days_since: s.days_since_last_contact ?? null,
        risk_factors: [],
        has_intervention: false,
      }))
    } catch (e) { console.warn('[coach/risk/index] students:', e) }
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
  else uni.switchTab({ url: '/home/index' })
}

function goDetail(id: number) {
  uni.navigateTo({ url: '/coach/students/detail?id=' + id })
}

onMounted(() => { loadStudents() })
</script>

<style scoped>
.risk-page { min-height: 100vh; background: #F5F6FA; }
.risk-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); color: #fff; }
.risk-nav-back { font-size: 40rpx; padding: 16rpx; }
.risk-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.risk-nav-action { font-size: 36rpx; padding: 16rpx; }

/* ── 统计+Tab 合并单排 ── */
.risk-stattabs { display: flex; padding: 16rpx 24rpx 12rpx; gap: 12rpx; }
.risk-st { flex: 1; background: #fff; border-radius: 14rpx; padding: 18rpx 8rpx 14rpx; text-align: center; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.risk-st--active { background: #E74C3C; box-shadow: 0 4rpx 12rpx rgba(231,76,60,0.3); }
.risk-st-num { display: block; font-size: 36rpx; font-weight: 700; color: #2C3E50; }
.risk-st--active .risk-st-num { color: #fff; }
.risk-st-label { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.risk-st--active .risk-st-label { color: rgba(255,255,255,0.85); }

.risk-list { height: calc(100vh - 420rpx); padding: 0 24rpx; }
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