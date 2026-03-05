<template>
  <view class="hr-page">
    <view class="hr-navbar">
      <view class="hr-back" @tap="goBack">←</view>
      <text class="hr-title">健康数据审核</text>
      <view class="hr-refresh" @tap="loadData">↻</view>
    </view>
    <scroll-view scroll-y class="hr-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view class="hr-stat-row">
        <view class="hr-stat"><text class="hr-stat-num" style="color:#2D8E69;">{{ items.length }}</text><text class="hr-stat-label">待审核</text></view>
        <view class="hr-stat"><text class="hr-stat-num" style="color:#27AE60;">{{ approvedToday }}</text><text class="hr-stat-label">今日通过</text></view>
        <view class="hr-stat"><text class="hr-stat-num" style="color:#E74C3C;">{{ rejectedToday }}</text><text class="hr-stat-label">今日退回</text></view>
      </view>

      <view v-for="item in items" :key="item.id" class="hr-card">
        <view class="hr-card-header">
          <view class="hr-avatar" :style="{ background: avatarColor(item.student_name) }">
            {{ (item.student_name || '?')[0] }}
          </view>
          <view class="hr-card-info">
            <text class="hr-card-name">{{ item.student_name || '学员' }}</text>
            <text class="hr-card-time">{{ formatDate(item.created_at) }}</text>
          </view>
          <view class="hr-risk-badge" :style="{ background: riskBg(item.risk_level), color: riskColor(item.risk_level) }">
            {{ riskLabel(item.risk_level) }}
          </view>
        </view>
        <text class="hr-summary">{{ item.ai_summary || item.summary || '暂无AI分析摘要' }}</text>
        <view class="hr-card-actions">
          <view
            class="hr-btn hr-btn--approve"
            :class="{ 'hr-btn--loading': processingIds.has(item.id) }"
            @tap="approveItem(item)"
          >{{ processingIds.has(item.id) ? '…' : '通过' }}</view>
          <view class="hr-btn hr-btn--reject" @tap="rejectItem(item)">退回</view>
        </view>
      </view>

      <view v-if="!loading && items.length === 0" class="hr-empty">
        <text class="hr-empty-icon">✅</text>
        <text class="hr-empty-text">暂无待审健康数据</text>
        <text class="hr-empty-hint">当前没有需要审核的健康记录</text>
      </view>
      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'
import { avatarColor } from '@/utils/studentUtils'

const loading = ref(false)
const refreshing = ref(false)
const items = ref<any[]>([])
const processingIds = ref<Set<string>>(new Set())
const approvedToday = ref(0)
const rejectedToday = ref(0)

function riskLabel(level: string): string {
  const m: Record<string, string> = { critical: '危急', high: '高风险', medium: '中风险', low: '低风险' }
  return m[level] || level
}
function riskColor(level: string): string {
  const m: Record<string, string> = { critical: '#C0392B', high: '#E74C3C', medium: '#E67E22', low: '#27AE60' }
  return m[level] || '#8E99A4'
}
function riskBg(level: string): string {
  const m: Record<string, string> = { critical: '#FDECEA', high: '#FFF0F0', medium: '#FFF7F0', low: '#F0FFF4' }
  return m[level] || '#F5F5F5'
}
function formatDate(t: string): string {
  return t ? new Date(t).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/health-review/queue?reviewer_role=coach&risk_level=medium')
    items.value = res.items || res || []
  } catch {
    items.value = []
  }
  loading.value = false
}

async function approveItem(item: any) {
  if (processingIds.value.has(item.id)) return
  processingIds.value.add(item.id)
  try {
    await http(`/api/v1/health-review/${item.id}/approve`, { method: 'POST' })
    uni.showToast({ title: '已通过', icon: 'success' })
    approvedToday.value++
    await loadData()
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    processingIds.value.delete(item.id)
  }
}

async function rejectItem(item: any) {
  if (processingIds.value.has(item.id)) return
  processingIds.value.add(item.id)
  try {
    // 不发 body — body 整体可选，发 {} 会触发 action required 422
    await http(`/api/v1/health-review/${item.id}/reject`, { method: 'POST' })
    uni.showToast({ title: '已退回', icon: 'success' })
    rejectedToday.value++
    await loadData()
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    processingIds.value.delete(item.id)
  }
}

async function onRefresh() {
  refreshing.value = true
  await loadData()
  refreshing.value = false
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/home/index' })
}

onMounted(() => loadData())
</script>

<style scoped>
.hr-page { min-height: 100vh; background: #F5F6FA; }
.hr-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #1E7A56, #2D8E69); color: #fff;
}
.hr-back { font-size: 40rpx; padding: 16rpx; }
.hr-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.hr-refresh { font-size: 40rpx; padding: 16rpx; }
.hr-scroll { height: calc(100vh - 180rpx); }
.hr-stat-row { display: flex; margin: 24rpx; gap: 16rpx; }
.hr-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx; text-align: center; }
.hr-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.hr-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.hr-card { margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.hr-card-header { display: flex; align-items: center; gap: 16rpx; margin-bottom: 16rpx; }
.hr-avatar {
  width: 64rpx; height: 64rpx; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 26rpx; font-weight: 700; flex-shrink: 0;
}
.hr-card-info { flex: 1; }
.hr-card-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.hr-card-time { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.hr-risk-badge { padding: 6rpx 16rpx; border-radius: 12rpx; font-size: 22rpx; font-weight: 700; }
.hr-summary { display: block; font-size: 26rpx; color: #5B6B7F; line-height: 1.6; margin-bottom: 20rpx; }
.hr-card-actions { display: flex; gap: 16rpx; }
.hr-btn { flex: 1; text-align: center; padding: 18rpx 0; border-radius: 12rpx; font-size: 28rpx; font-weight: 600; }
.hr-btn--approve { background: #2D8E69; color: #fff; }
.hr-btn--reject { background: #FFF0F0; color: #E74C3C; }
.hr-btn--loading { background: #BDC3C7; color: #fff; }
.hr-empty { text-align: center; padding: 120rpx 0; }
.hr-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.hr-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; }
.hr-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 8rpx; }
</style>
