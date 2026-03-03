<template>
  <view class="cr-page">
    <view class="cr-navbar">
      <view class="cr-back" @tap="goBack">←</view>
      <text class="cr-title">危急病例审核</text>
      <view class="cr-refresh" @tap="loadData">↻</view>
    </view>
    <scroll-view scroll-y class="cr-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view class="cr-stat-row">
        <view class="cr-stat"><text class="cr-stat-num" style="color:#E74C3C;">{{ items.length }}</text><text class="cr-stat-label">危急待审</text></view>
        <view class="cr-stat"><text class="cr-stat-num" style="color:#27AE60;">{{ doneToday }}</text><text class="cr-stat-label">今日已处理</text></view>
      </view>

      <view v-for="item in items" :key="item.id" class="cr-card">
        <view class="cr-card-header">
          <view class="cr-avatar" :style="{ background: avatarColor(item.patient_name || item.student_name) }">
            {{ ((item.patient_name || item.student_name) || '?')[0] }}
          </view>
          <view class="cr-card-info">
            <text class="cr-card-name">{{ item.patient_name || item.student_name || '患者' }}</text>
            <text class="cr-card-time">{{ formatDate(item.created_at) }}</text>
          </view>
          <view class="cr-critical-badge">危急</view>
        </view>
        <view class="cr-ai-block">
          <text class="cr-ai-label">AI分析结论</text>
          <text class="cr-ai-text">{{ item.ai_summary || item.ai_conclusion || '暂无AI分析结论' }}</text>
        </view>
        <text class="cr-disposal-label">处置建议</text>
        <textarea
          class="cr-disposal-input"
          v-model="item._note"
          placeholder="请输入处置建议（选填）…"
          maxlength="500"
        />
        <view class="cr-card-actions">
          <view
            class="cr-btn cr-btn--push"
            :class="{ 'cr-btn--loading': processingIds.has(item.id) }"
            @tap="pushDirect(item)"
          >{{ processingIds.has(item.id) ? '…' : '直接推送' }}</view>
          <view class="cr-btn cr-btn--revise" @tap="pushRevised(item)">修订后推送</view>
          <view class="cr-btn cr-btn--reject" @tap="rejectItem(item)">退回</view>
        </view>
      </view>

      <view v-if="!loading && items.length === 0" class="cr-empty">
        <text class="cr-empty-icon">✅</text>
        <text class="cr-empty-text">暂无危急病例</text>
        <text class="cr-empty-hint">当前没有需要紧急处理的病例</text>
      </view>
      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const loading = ref(false)
const refreshing = ref(false)
const items = ref<any[]>([])
const processingIds = ref<Set<string>>(new Set())
const doneToday = ref(0)

const colorPool = ['#9B59B6', '#E74C3C', '#7D3C98', '#C0392B', '#8E44AD', '#6C3483']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0
  for (const c of name) h = c.charCodeAt(0) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}

function formatDate(t: string): string {
  return t ? new Date(t).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/health-review/queue?reviewer_role=master&risk_level=critical')
    const rawItems = res.items || res || []
    items.value = rawItems.map((i: any) => ({ ...i, _note: '' }))
  } catch {
    items.value = []
  }
  loading.value = false
}

async function pushDirect(item: any) {
  if (processingIds.value.has(item.id)) return
  processingIds.value.add(item.id)
  try {
    await http(`/api/v1/health-review/${item.id}/approve`, {
      method: 'POST',
      data: { note: item._note || '', action: 'push_direct' },
    })
    uni.showToast({ title: '已直接推送', icon: 'success' })
    doneToday.value++
    await loadData()
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    processingIds.value.delete(item.id)
  }
}

async function pushRevised(item: any) {
  if (!item._note.trim()) {
    uni.showToast({ title: '请先填写处置建议', icon: 'none' })
    return
  }
  if (processingIds.value.has(item.id)) return
  processingIds.value.add(item.id)
  try {
    await http(`/api/v1/health-review/${item.id}/approve`, {
      method: 'POST',
      data: { note: item._note, action: 'push_revised' },
    })
    uni.showToast({ title: '已修订推送', icon: 'success' })
    doneToday.value++
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
    await http(`/api/v1/health-review/${item.id}/reject`, { method: 'POST', data: { note: item._note || '' } })
    uni.showToast({ title: '已退回', icon: 'success' })
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
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => loadData())
</script>

<style scoped>
.cr-page { min-height: 100vh; background: #F5F6FA; }
.cr-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #7D3C98, #9B59B6); color: #fff;
}
.cr-back { font-size: 40rpx; padding: 16rpx; }
.cr-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.cr-refresh { font-size: 40rpx; padding: 16rpx; }
.cr-scroll { height: calc(100vh - 180rpx); }
.cr-stat-row { display: flex; margin: 24rpx; gap: 16rpx; }
.cr-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx; text-align: center; }
.cr-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.cr-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.cr-card { margin: 0 24rpx 16rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; border-left: 6rpx solid #E74C3C; }
.cr-card-header { display: flex; align-items: center; gap: 16rpx; margin-bottom: 20rpx; }
.cr-avatar {
  width: 64rpx; height: 64rpx; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 26rpx; font-weight: 700; flex-shrink: 0;
}
.cr-card-info { flex: 1; }
.cr-card-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.cr-card-time { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.cr-critical-badge {
  padding: 6rpx 18rpx; border-radius: 12rpx; background: #E74C3C;
  color: #fff; font-size: 22rpx; font-weight: 700;
}
.cr-ai-block { background: #F8F0FF; border-radius: 12rpx; padding: 16rpx 20rpx; margin-bottom: 16rpx; }
.cr-ai-label { display: block; font-size: 22rpx; color: #9B59B6; font-weight: 600; margin-bottom: 8rpx; }
.cr-ai-text { display: block; font-size: 26rpx; color: #2C3E50; line-height: 1.6; }
.cr-disposal-label { display: block; font-size: 24rpx; color: #8E99A4; margin-bottom: 8rpx; }
.cr-disposal-input {
  width: 100%; background: #F5F6FA; border-radius: 12rpx;
  padding: 16rpx 20rpx; font-size: 26rpx; box-sizing: border-box;
  height: 160rpx; line-height: 1.6; margin-bottom: 20rpx;
}
.cr-card-actions { display: flex; gap: 12rpx; }
.cr-btn { flex: 1; text-align: center; padding: 16rpx 0; border-radius: 12rpx; font-size: 24rpx; font-weight: 600; }
.cr-btn--push { background: #9B59B6; color: #fff; }
.cr-btn--revise { background: #F5EEF8; color: #7D3C98; }
.cr-btn--reject { background: #FFF0F0; color: #E74C3C; }
.cr-btn--loading { background: #BDC3C7; color: #fff; }
.cr-empty { text-align: center; padding: 120rpx 0; }
.cr-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.cr-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; }
.cr-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 8rpx; }
</style>
