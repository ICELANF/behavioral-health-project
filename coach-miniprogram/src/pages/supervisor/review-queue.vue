<template>
  <view class="rq-page">
    <view class="rq-navbar">
      <view class="rq-back" @tap="goBack">←</view>
      <text class="rq-title">健康数据审核</text>
      <view class="rq-refresh" @tap="loadData">↻</view>
    </view>
    <scroll-view scroll-y class="rq-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view class="rq-stat-row">
        <view class="rq-stat"><text class="rq-stat-num" style="color:#E67E22;">{{ items.length }}</text><text class="rq-stat-label">待审核</text></view>
        <view class="rq-stat"><text class="rq-stat-num" style="color:#E74C3C;">{{ criticalCount }}</text><text class="rq-stat-label">危急</text></view>
        <view class="rq-stat"><text class="rq-stat-num" style="color:#E67E22;">{{ highCount }}</text><text class="rq-stat-label">高风险</text></view>
        <view class="rq-stat"><text class="rq-stat-num" style="color:#27AE60;">{{ medCount }}</text><text class="rq-stat-label">中风险</text></view>
      </view>

      <view v-for="item in items" :key="item.id" class="rq-card">
        <view class="rq-card-header">
          <view class="rq-avatar" :style="{ background: avatarColor(item.student_name) }">
            {{ (item.student_name || '?')[0] }}
          </view>
          <view class="rq-card-info">
            <text class="rq-card-name">{{ item.student_name || '学员' }}</text>
            <text class="rq-card-time">{{ formatDate(item.created_at) }}</text>
          </view>
          <view class="rq-risk-badge" :style="{ background: riskBg(item.risk_level), color: riskColor(item.risk_level) }">
            {{ riskLabel(item.risk_level) }}
          </view>
        </view>
        <text class="rq-summary">{{ item.ai_summary || item.summary || '暂无AI分析摘要' }}</text>
        <view class="rq-card-actions">
          <view
            class="rq-btn rq-btn--approve"
            :class="{ 'rq-btn--loading': processingIds.has(item.id) }"
            @tap="approveItem(item)"
          >{{ processingIds.has(item.id) ? '…' : '通过' }}</view>
          <view class="rq-btn rq-btn--revise" @tap="reviseItem(item)">修订</view>
          <view class="rq-btn rq-btn--reject" @tap="rejectItem(item)">退回</view>
        </view>
      </view>

      <view v-if="!loading && items.length === 0" class="rq-empty">
        <text class="rq-empty-icon">✅</text>
        <text class="rq-empty-text">暂无待审健康数据</text>
        <text class="rq-empty-hint">所有数据均已审核完毕</text>
      </view>
      <view style="height:120rpx;"></view>
    </scroll-view>

    <!-- 修订 Modal -->
    <view v-if="showReviseModal" class="rq-mask" @tap.self="showReviseModal = false">
      <view class="rq-modal">
        <text class="rq-modal-title">修订意见</text>
        <text class="rq-modal-label">请输入修订说明</text>
        <textarea class="rq-modal-textarea" v-model="reviseNote" placeholder="请描述需要修订的内容…" maxlength="500" />
        <view class="rq-modal-actions">
          <view class="rq-modal-btn rq-modal-cancel" @tap="showReviseModal = false">取消</view>
          <view class="rq-modal-btn rq-modal-submit" @tap="submitRevise">提交修订</view>
        </view>
      </view>
    </view>
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
const items = ref<any[]>([])
const processingIds = ref<Set<string>>(new Set())
const showReviseModal = ref(false)
const reviseNote = ref('')
const currentItem = ref<any>(null)

const criticalCount = computed(() => items.value.filter(i => i.risk_level === 'critical').length)
const highCount = computed(() => items.value.filter(i => i.risk_level === 'high').length)
const medCount = computed(() => items.value.filter(i => i.risk_level === 'medium').length)

const colorPool = ['#3498DB', '#E74C3C', '#27AE60', '#9B59B6', '#E67E22', '#1ABC9C']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0
  for (const c of name) h = c.charCodeAt(0) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}

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
    const res = await http<any>('/api/v1/health-review/queue?reviewer_role=supervisor')
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
    await http(`/api/v1/health-review/${item.id}/approve`, { method: 'POST', data: {} })
    uni.showToast({ title: '已通过', icon: 'success' })
    await loadData()
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    processingIds.value.delete(item.id)
  }
}

function reviseItem(item: any) {
  currentItem.value = item
  reviseNote.value = ''
  showReviseModal.value = true
}

async function submitRevise() {
  if (!reviseNote.value.trim()) { uni.showToast({ title: '请填写修订意见', icon: 'none' }); return }
  if (!currentItem.value) return
  try {
    await http(`/api/v1/health-review/${currentItem.value.id}/approve`, {
      method: 'POST',
      data: { note: reviseNote.value, action: 'revise' },
    })
    showReviseModal.value = false
    uni.showToast({ title: '修订意见已提交', icon: 'success' })
    await loadData()
  } catch {
    uni.showToast({ title: '提交失败', icon: 'none' })
  }
}

async function rejectItem(item: any) {
  if (processingIds.value.has(item.id)) return
  processingIds.value.add(item.id)
  try {
    await http(`/api/v1/health-review/${item.id}/reject`, { method: 'POST', data: {} })
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
.rq-page { min-height: 100vh; background: #F5F6FA; }
.rq-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #D35400, #E67E22); color: #fff;
}
.rq-back { font-size: 40rpx; padding: 16rpx; }
.rq-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.rq-refresh { font-size: 40rpx; padding: 16rpx; }
.rq-scroll { height: calc(100vh - 180rpx); }
.rq-stat-row { display: flex; margin: 24rpx; gap: 12rpx; }
.rq-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 16rpx; text-align: center; }
.rq-stat-num { display: block; font-size: 36rpx; font-weight: 700; color: #2C3E50; }
.rq-stat-label { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.rq-card { margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.rq-card-header { display: flex; align-items: center; gap: 16rpx; margin-bottom: 16rpx; }
.rq-avatar {
  width: 64rpx; height: 64rpx; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 26rpx; font-weight: 700; flex-shrink: 0;
}
.rq-card-info { flex: 1; }
.rq-card-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.rq-card-time { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.rq-risk-badge { padding: 6rpx 16rpx; border-radius: 12rpx; font-size: 22rpx; font-weight: 700; }
.rq-summary { display: block; font-size: 26rpx; color: #5B6B7F; line-height: 1.6; margin-bottom: 20rpx; }
.rq-card-actions { display: flex; gap: 12rpx; }
.rq-btn { flex: 1; text-align: center; padding: 16rpx 0; border-radius: 12rpx; font-size: 26rpx; font-weight: 600; }
.rq-btn--approve { background: #27AE60; color: #fff; }
.rq-btn--revise { background: #FFF3E0; color: #E67E22; }
.rq-btn--reject { background: #FFF0F0; color: #E74C3C; }
.rq-btn--loading { background: #BDC3C7; color: #fff; }
.rq-empty { text-align: center; padding: 120rpx 0; }
.rq-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.rq-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; }
.rq-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 8rpx; }
.rq-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: flex-end; }
.rq-modal {
  width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0;
  padding: 40rpx 32rpx calc(48rpx + env(safe-area-inset-bottom));
}
.rq-modal-title { display: block; font-size: 34rpx; font-weight: 700; color: #2C3E50; text-align: center; margin-bottom: 24rpx; }
.rq-modal-label { display: block; font-size: 24rpx; color: #8E99A4; margin-bottom: 8rpx; }
.rq-modal-textarea {
  width: 100%; background: #F5F6FA; border-radius: 12rpx;
  padding: 18rpx 20rpx; font-size: 26rpx; box-sizing: border-box; height: 180rpx; line-height: 1.6;
}
.rq-modal-actions { display: flex; gap: 20rpx; margin-top: 28rpx; }
.rq-modal-btn { flex: 1; text-align: center; padding: 26rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.rq-modal-cancel { background: #F0F0F0; color: #5B6B7F; }
.rq-modal-submit { background: #E67E22; color: #fff; }
</style>
