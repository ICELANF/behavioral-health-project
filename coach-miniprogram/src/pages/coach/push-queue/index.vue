<template>
  <view class="pq-page">
    <view class="pq-navbar">
      <view class="pq-nav-back" @tap="goBack">←</view>
      <text class="pq-nav-title">推送队列</text>
      <view class="pq-nav-action" @tap="refresh">↻</view>
    </view>

    <!-- 统计 + Tab 合并单行 -->
    <view class="pq-stattabs">
      <view v-for="t in statTabs" :key="t.key"
        class="pq-st" :class="{ 'pq-st--active': activeTab === t.key }"
        :style="activeTab === t.key ? { background: t.color } : {}"
        @tap="activeTab = t.key">
        <text class="pq-st-n" :style="activeTab === t.key ? { color: '#fff' } : { color: t.color }">{{ t.count }}</text>
        <text class="pq-st-l">{{ t.label }}</text>
      </view>
    </view>

    <!-- 队列列表 -->
    <scroll-view scroll-y class="pq-list" style="height:calc(100vh - 380rpx);" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-for="item in filteredItems" :key="item.id" class="pq-card">
        <view class="pq-card-header">
          <view class="pq-card-avatar">{{ (item.student_name || '?')[0] }}</view>
          <view class="pq-card-info">
            <text class="pq-card-name">{{ item.student_name }}</text>
            <text class="pq-card-type">{{ item.type_label }}</text>
          </view>
          <view class="pq-card-status" :style="{ background: statusColor(item.status) }">
            {{ statusLabel(item.status) }}
          </view>
        </view>
        <text class="pq-card-content">{{ item.content || item.ai_summary || '—' }}</text>
        <view class="pq-card-footer">
          <text class="pq-card-time">{{ item.scheduled_at || item.created_at || '' }}</text>
          <view v-if="item.status === 'pending'" class="pq-card-actions">
            <view class="pq-btn" :class="processingIds.has(item.id) ? 'pq-btn--loading' : 'pq-btn--send'" @tap="sendPush(item)">
              {{ processingIds.has(item.id) ? '…' : '发送' }}
            </view>
            <view class="pq-btn pq-btn--cancel" @tap="cancelPush(item)">取消</view>
          </view>
        </view>
      </view>

      <view v-if="filteredItems.length === 0" class="pq-empty">
        <text class="pq-empty-icon">📤</text>
        <text class="pq-empty-text">{{ activeTab === 'pending' ? '无待推送任务' : '暂无记录' }}</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const activeTab = ref('pending')
const refreshing = ref(false)
const queueItems = ref<any[]>([])
const processingIds = ref<Set<number>>(new Set())

const statTabs = computed(() => [
  { key: 'pending', label: '待推送', count: queueItems.value.filter(i => i.status === 'pending').length, color: '#E67E22' },
  { key: 'sent',    label: '已推送', count: queueItems.value.filter(i => i.status === 'sent').length,    color: '#27AE60' },
  { key: 'all',     label: '全部',   count: queueItems.value.length,                                      color: '#3498DB' },
])

const filteredItems = computed(() => {
  if (activeTab.value === 'all') return queueItems.value
  return queueItems.value.filter(i => i.status === activeTab.value)
})

function statusColor(s: string): string {
  const m: Record<string, string> = { pending: '#E67E22', sent: '#27AE60', cancelled: '#BDC3C7', failed: '#E74C3C' }
  return m[s] || '#8E99A4'
}
function statusLabel(s: string): string {
  const m: Record<string, string> = { pending: '待推送', sent: '已推送', cancelled: '已取消', failed: '失败' }
  return m[s] || s
}

const SOURCE_LABELS: Record<string, string> = {
  rx_push: '处方推送', reminder: '提醒', assessment: '评估邀请',
  ai_recommendation: 'AI推荐', content: '内容推送', system: '系统通知',
  coach_message: '消息推送', challenge: '挑战任务',
}

async function loadData() {
  try {
    // Fetch all statuses: pending + approved/sent for history tabs
    const [pendingRes, sentRes] = await Promise.allSettled([
      http<any>('/api/v1/coach/push-queue?page_size=50&status=pending'),
      http<any>('/api/v1/coach/push-queue?page_size=50&status=approved'),
    ])
    const allItems: any[] = []
    if (pendingRes.status === 'fulfilled') allItems.push(...(pendingRes.value.items || []))
    if (sentRes.status === 'fulfilled')    allItems.push(...(sentRes.value.items || []))

    queueItems.value = allItems.map((i: any) => ({
      id: i.id,
      student_id: i.student_id,
      student_name: i.student_name || i.grower_name || '学员',
      type_label: SOURCE_LABELS[i.source_type] || SOURCE_LABELS[i.type] || '消息推送',
      content: i.content || i.ai_summary || i.title || '',
      status: i.status === 'approved' ? 'sent' : (i.status || 'pending'),
      scheduled_at: i.scheduled_time || i.scheduled_at || '',
      created_at: i.created_at || '',
    }))
  } catch {
    queueItems.value = []
  }
}

async function sendPush(item: any) {
  if (processingIds.value.has(item.id)) return   // 防重复点击
  processingIds.value.add(item.id)
  try {
    await http('/api/v1/coach/push-queue/' + item.id + '/approve', { method: 'POST' })
    uni.showToast({ title: '已发送', icon: 'success' })
    await loadData()
  } catch (e: any) {
    const code = (e as any)?.statusCode || 0
    uni.showToast({ title: code === 400 ? '状态已更新，刷新中' : '发送失败', icon: 'none' })
    await loadData()
  } finally {
    processingIds.value.delete(item.id)
  }
}

async function cancelPush(item: any) {
  if (processingIds.value.has(item.id)) return   // 防重复点击
  processingIds.value.add(item.id)
  try {
    await http('/api/v1/coach/push-queue/' + item.id + '/reject', { method: 'POST' })
    uni.showToast({ title: '已取消', icon: 'success' })
    await loadData()
  } catch (e: any) {
    const code = (e as any)?.statusCode || 0
    uni.showToast({ title: code === 400 ? '状态已更新，刷新中' : '取消失败', icon: 'none' })
    await loadData()
  } finally {
    processingIds.value.delete(item.id)
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
function refresh() { loadData() }
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pq-page { min-height: 100vh; background: #F5F6FA; }
.pq-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #E67E22 0%, #F39C12 100%); color: #fff; }
.pq-nav-back { font-size: 40rpx; padding: 16rpx; }
.pq-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.pq-nav-action { font-size: 36rpx; padding: 16rpx; }

.pq-stattabs { display: flex; padding: 16rpx 24rpx; gap: 12rpx; }
.pq-st { flex: 1; background: #fff; border-radius: 16rpx; padding: 18rpx 0; text-align: center; transition: background 0.2s; }
.pq-st-n { display: block; font-size: 40rpx; font-weight: 800; }
.pq-st-l { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.pq-st--active .pq-st-l { color: rgba(255,255,255,0.85); }

.pq-list { padding: 0 24rpx; }
.pq-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.pq-card-header { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; }
.pq-card-avatar { width: 56rpx; height: 56rpx; border-radius: 50%; background: #3498DB; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 600; }
.pq-card-info { flex: 1; }
.pq-card-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.pq-card-type { display: block; font-size: 22rpx; color: #8E99A4; }
.pq-card-status { padding: 6rpx 16rpx; border-radius: 8rpx; color: #fff; font-size: 22rpx; }
.pq-card-content { display: block; font-size: 26rpx; color: #5B6B7F; line-height: 1.5; margin-bottom: 12rpx; }
.pq-card-footer { display: flex; justify-content: space-between; align-items: center; }
.pq-card-time { font-size: 22rpx; color: #BDC3C7; }
.pq-card-actions { display: flex; gap: 12rpx; }
.pq-btn { padding: 10rpx 24rpx; border-radius: 8rpx; font-size: 24rpx; font-weight: 600; }
.pq-btn--send { background: #27AE60; color: #fff; }
.pq-btn--cancel { background: #F0F0F0; color: #5B6B7F; }
.pq-btn--loading { background: #BDC3C7; color: #fff; }

.pq-empty { text-align: center; padding: 120rpx 0; }
.pq-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.pq-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>