<template>
  <view class="cr-page">
    <view class="cr-navbar">
      <view class="cr-back" @tap="goBack">←</view>
      <text class="cr-title">内容投稿审核</text>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="cr-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <view class="cr-notice">
        <text class="cr-notice-text">📋 以下为学员投稿的个人经验分享，审核通过后将收录入健康之路案例库</text>
      </view>

      <!-- 投稿列表 -->
      <view v-for="item in pending" :key="item.id" class="cr-card">
        <view class="cr-card-head">
          <view class="cr-tier-tag" :class="'cr-tier--' + (item.evidence_tier || 'T4').toLowerCase()">
            {{ item.evidence_tier || 'T4' }}
          </view>
          <text class="cr-date">{{ formatDate(item.created_at) }}</text>
        </view>
        <text class="cr-card-title">{{ item.title }}</text>
        <text class="cr-card-author">投稿者：{{ item.author || '匿名' }}</text>
        <text v-if="item.domain_id" class="cr-domain">领域：{{ item.domain_id }}</text>

        <view class="cr-actions">
          <view class="cr-view-btn" @tap="openDetail(item)">查看全文</view>
          <view class="cr-reject-btn" @tap="doAction(item, false)">拒绝</view>
          <view class="cr-approve-btn" @tap="doAction(item, true)">通过</view>
        </view>
      </view>

      <view v-if="!loading && pending.length === 0" class="cr-empty">
        <text class="cr-empty-icon">✅</text>
        <text class="cr-empty-text">暂无待审核投稿</text>
      </view>
      <view style="height:80rpx;"></view>
    </scroll-view>

    <!-- 全文弹窗 -->
    <view v-if="detailItem" class="cr-detail-mask" @tap="detailItem = null">
      <view class="cr-detail-sheet" @tap.stop>
        <view class="cr-detail-head">
          <text class="cr-detail-title">{{ detailItem.title }}</text>
          <view class="cr-detail-close" @tap="detailItem = null">×</view>
        </view>
        <scroll-view scroll-y style="max-height: 60vh;">
          <text class="cr-detail-content">{{ detailItem.raw_content || '（内容为空）' }}</text>
        </scroll-view>
        <view class="cr-detail-actions">
          <view class="cr-reject-btn" @tap="doAction(detailItem, false); detailItem = null">拒绝</view>
          <view class="cr-approve-btn" @tap="doAction(detailItem, true); detailItem = null">通过</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const loading = ref(false)
const refreshing = ref(false)
const pending = ref<any[]>([])
const detailItem = ref<any>(null)

function formatDate(iso: string): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

function openDetail(item: any) {
  detailItem.value = item
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/contributions/review/pending')
    pending.value = res.data || []
  } catch { pending.value = [] }
  loading.value = false
}

async function doAction(item: any, approve: boolean) {
  const action = approve ? 'approve' : 'reject'
  try {
    await http(`/api/v1/contributions/review/${item.id}/${action}`, { method: 'POST' })
    uni.showToast({ title: approve ? '已通过' : '已拒绝', icon: 'success' })
    pending.value = pending.value.filter(p => p.id !== item.id)
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/home/index' })
}
onMounted(() => loadData())
</script>

<style scoped>
.cr-page { min-height: 100vh; background: #F5F6FA; }
.cr-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #16A085, #1ABC9C); color: #fff;
}
.cr-back { font-size: 40rpx; padding: 16rpx; }
.cr-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.cr-scroll { height: calc(100vh - 180rpx); }

.cr-notice { margin: 16rpx 24rpx; background: #E8F8F5; border-radius: 12rpx; padding: 16rpx 20rpx; }
.cr-notice-text { font-size: 24rpx; color: #1A7A67; line-height: 1.5; }

.cr-card { margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.cr-card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10rpx; }
.cr-tier-tag { padding: 4rpx 14rpx; border-radius: 20rpx; font-size: 20rpx; font-weight: 700; }
.cr-tier--t1 { background: #FEF3C7; color: #D97706; }
.cr-tier--t2 { background: #DBEAFE; color: #2563EB; }
.cr-tier--t3 { background: #F3E8FF; color: #7C3AED; }
.cr-tier--t4 { background: #F0FFF4; color: #16A085; }
.cr-date { font-size: 22rpx; color: #8E99A4; }
.cr-card-title { display: block; font-size: 28rpx; font-weight: 700; color: #2C3E50; margin-bottom: 6rpx; line-height: 1.5; }
.cr-card-author { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 4rpx; }
.cr-domain { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 16rpx; }
.cr-actions { display: flex; gap: 10rpx; }
.cr-view-btn { flex: 1; padding: 14rpx; border-radius: 12rpx; background: #F0F4FF; color: #3498DB; text-align: center; font-size: 24rpx; font-weight: 600; }
.cr-approve-btn { flex: 1; padding: 14rpx; border-radius: 12rpx; background: #2D8E69; color: #fff; text-align: center; font-size: 24rpx; font-weight: 600; }
.cr-reject-btn { flex: 1; padding: 14rpx; border-radius: 12rpx; background: #F5F6FA; color: #8E99A4; border: 1rpx solid #E0E0E0; text-align: center; font-size: 24rpx; font-weight: 600; }

.cr-empty { text-align: center; padding: 120rpx 0; }
.cr-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.cr-empty-text { font-size: 26rpx; color: #8E99A4; }

/* 全文弹窗 */
.cr-detail-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: flex-end; }
.cr-detail-sheet { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 32rpx 32rpx calc(48rpx + env(safe-area-inset-bottom)); max-height: 85vh; display: flex; flex-direction: column; }
.cr-detail-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20rpx; }
.cr-detail-title { flex: 1; font-size: 30rpx; font-weight: 700; color: #2C3E50; line-height: 1.5; }
.cr-detail-close { font-size: 40rpx; color: #8E99A4; padding: 0 0 0 16rpx; flex-shrink: 0; }
.cr-detail-content { font-size: 26rpx; color: #5B6B7F; line-height: 1.8; white-space: pre-wrap; }
.cr-detail-actions { display: flex; gap: 12rpx; margin-top: 24rpx; }
</style>
