<template>
  <view class="mp-page">
    <view class="mp-navbar">
      <view class="mp-back" @tap="goBack">←</view>
      <text class="mp-title">晋级终审（L3）</text>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="mp-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <view class="mp-notice">
        <text class="mp-notice-text">👑 以下申请已通过两级初审，需 ≥2 位行为健康大师联合确认方可晋级</text>
      </view>

      <view v-for="item in items" :key="item.application_id" class="mp-card">
        <view class="mp-card-head">
          <view class="mp-level-tag">{{ roleLabel(item.current_level) }} → {{ roleLabel(item.target_level) }}</view>
          <view class="mp-votes" :class="{ 'mp-votes--ready': item.l3_approval_count >= 2 }">
            {{ item.l3_approval_count }}/2 大师确认
          </view>
        </view>
        <text class="mp-name">{{ item.full_name || item.username }}</text>
        <text class="mp-date">申请于 {{ fmtDate(item.applied_at) }}</text>
        <text v-if="item.statement" class="mp-statement">{{ item.statement }}</text>

        <!-- 已有的大师确认列表 -->
        <view v-if="item.l3_approvals && item.l3_approvals.length > 0" class="mp-approvals">
          <text class="mp-approvals-label">已确认：</text>
          <text v-for="(a, i) in item.l3_approvals" :key="i" class="mp-approval-item">
            大师#{{ a.user_id }} · {{ fmtDate(a.approved_at) }}
          </text>
        </view>

        <view class="mp-actions">
          <view class="mp-view-btn" @tap="openDetail(item)">查看详情</view>
          <view class="mp-reject-btn" @tap="doReview(item, false)">拒绝</view>
          <view class="mp-approve-btn" @tap="doReview(item, true)">
            确认晋级{{ item.l3_approval_count === 1 ? '（完成）' : '' }}
          </view>
        </view>
      </view>

      <view v-if="!loading && items.length === 0" class="mp-empty">
        <text class="mp-empty-icon">👑</text>
        <text class="mp-empty-text">暂无待终审申请</text>
      </view>
      <view style="height:80rpx;"></view>
    </scroll-view>

    <!-- 详情弹窗 -->
    <view v-if="detailItem" class="mp-mask" @tap="detailItem = null">
      <view class="mp-sheet" @tap.stop>
        <view class="mp-sheet-head">
          <text class="mp-sheet-name">{{ detailItem.full_name || detailItem.username }}</text>
          <view class="mp-sheet-close" @tap="detailItem = null">×</view>
        </view>
        <view class="mp-sheet-meta">
          <text>{{ roleLabel(detailItem.current_level) }} → {{ roleLabel(detailItem.target_level) }}</text>
        </view>
        <view class="mp-votes-big" :class="{ 'mp-votes--ready': detailItem.l3_approval_count >= 2 }">
          {{ detailItem.l3_approval_count }}/2 大师已确认
        </view>
        <scroll-view scroll-y style="max-height:40vh;">
          <text class="mp-sheet-statement">{{ detailItem.statement || '（无申请说明）' }}</text>
        </scroll-view>
        <view class="mp-sheet-actions">
          <view class="mp-reject-btn" @tap="doReview(detailItem, false); detailItem = null">拒绝</view>
          <view class="mp-approve-btn" @tap="doReview(detailItem, true); detailItem = null">确认晋级</view>
        </view>
      </view>
    </view>

    <!-- 拒绝理由 -->
    <view v-if="rejectModal.show" class="mp-mask" @tap="rejectModal.show = false">
      <view class="mp-reject-sheet" @tap.stop>
        <text class="mp-reject-title">填写拒绝理由</text>
        <textarea class="mp-reject-input" v-model="rejectModal.reason"
          placeholder="请说明拒绝原因（必填）" maxlength="200" />
        <view class="mp-sheet-actions">
          <view class="mp-view-btn" @tap="rejectModal.show = false">取消</view>
          <view class="mp-reject-btn" @tap="confirmReject">确认拒绝</view>
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
const items = ref<any[]>([])
const detailItem = ref<any>(null)
const rejectModal = ref({ show: false, item: null as any, reason: '' })

const LEVEL_MAP: Record<string, string> = {
  grower: '成长者', sharer: '分享者',
  coach: '行为健康教练', promoter: '行为健康促进师',
  supervisor: '行为健康促进师', master: '行为健康大师',
  GROWER: '成长者', SHARER: '分享者', COACH: '行为健康教练',
}
function roleLabel(r: string) { return LEVEL_MAP[r] || r || '—' }
function fmtDate(iso: string) {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function openDetail(item: any) { detailItem.value = item }

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/promotion/applications?status=pending')
    items.value = (res.applications || []).filter((a: any) => a.review_stage === 'L3')
  } catch { items.value = [] }
  loading.value = false
}

function doReview(item: any, approve: boolean) {
  if (!approve) {
    rejectModal.value = { show: true, item, reason: '' }
    return
  }
  submitReview(item, true, '')
}

async function confirmReject() {
  if (!rejectModal.value.reason.trim()) {
    uni.showToast({ title: '请填写拒绝理由', icon: 'none' }); return
  }
  await submitReview(rejectModal.value.item, false, rejectModal.value.reason)
  rejectModal.value.show = false
}

async function submitReview(item: any, approved: boolean, reason: string) {
  try {
    const res = await http<any>(`/api/v1/promotion/review/${item.application_id}`, {
      method: 'POST', data: { approved, reason }
    }) as any
    if (approved) {
      if (res.status === 'approved') {
        uni.showToast({ title: '🎉 晋级成功！', icon: 'success', duration: 2500 })
        items.value = items.value.filter(i => i.application_id !== item.application_id)
      } else {
        const count = res.approval_count || 0
        uni.showToast({ title: `已确认（${count}/2）`, icon: 'none' })
        // 刷新列表更新票数
        await loadData()
      }
    } else {
      uni.showToast({ title: '已拒绝', icon: 'success' })
      items.value = items.value.filter(i => i.application_id !== item.application_id)
    }
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}
onMounted(() => loadData())
</script>

<style scoped>
.mp-page { min-height: 100vh; background: #F5F6FA; }
.mp-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #b8860b, #faad14); color: #fff;
}
.mp-back { font-size: 40rpx; padding: 16rpx; }
.mp-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.mp-scroll { height: calc(100vh - 180rpx); }

.mp-notice { margin: 16rpx 24rpx; background: #fff8e1; border-radius: 12rpx; padding: 16rpx 20rpx; }
.mp-notice-text { font-size: 24rpx; color: #b8860b; line-height: 1.5; }

.mp-card { margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.mp-card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10rpx; }
.mp-level-tag { padding: 4rpx 16rpx; background: #fff8e1; color: #b8860b; border-radius: 20rpx; font-size: 22rpx; font-weight: 700; }
.mp-votes { font-size: 22rpx; color: #8E99A4; padding: 4rpx 12rpx; border-radius: 12rpx; background: #F5F6FA; }
.mp-votes--ready { background: #fff8e1; color: #b8860b; font-weight: 700; }
.mp-name { display: block; font-size: 30rpx; font-weight: 700; color: #2C3E50; margin-bottom: 4rpx; }
.mp-date { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 8rpx; }
.mp-statement { display: block; font-size: 24rpx; color: #5B6B7F; margin-bottom: 12rpx; line-height: 1.6;
  overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.mp-approvals { margin-bottom: 16rpx; background: #FFF8DC; border-radius: 8rpx; padding: 10rpx 14rpx; }
.mp-approvals-label { font-size: 22rpx; color: #b8860b; margin-right: 8rpx; }
.mp-approval-item { font-size: 22rpx; color: #5B6B7F; display: block; }

.mp-actions { display: flex; gap: 10rpx; }
.mp-view-btn { flex: 1; padding: 14rpx; border-radius: 12rpx; background: #fff8e1; color: #b8860b; text-align: center; font-size: 24rpx; font-weight: 600; }
.mp-approve-btn { flex: 1; padding: 14rpx; border-radius: 12rpx; background: linear-gradient(135deg,#b8860b,#faad14); color: #fff; text-align: center; font-size: 24rpx; font-weight: 600; }
.mp-reject-btn { flex: 1; padding: 14rpx; border-radius: 12rpx; background: #F5F6FA; color: #8E99A4; border: 1rpx solid #E0E0E0; text-align: center; font-size: 24rpx; font-weight: 600; }

.mp-empty { text-align: center; padding: 120rpx 0; }
.mp-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.mp-empty-text { font-size: 26rpx; color: #8E99A4; }

.mp-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: flex-end; }
.mp-sheet { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 32rpx 32rpx calc(48rpx + env(safe-area-inset-bottom)); max-height: 85vh; display: flex; flex-direction: column; }
.mp-sheet-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.mp-sheet-name { font-size: 32rpx; font-weight: 700; color: #2C3E50; }
.mp-sheet-close { font-size: 40rpx; color: #8E99A4; padding: 0 0 0 16rpx; }
.mp-sheet-meta { font-size: 22rpx; color: #8E99A4; margin-bottom: 16rpx; }
.mp-votes-big { font-size: 28rpx; font-weight: 700; color: #8E99A4; text-align: center; padding: 12rpx; background: #F5F6FA; border-radius: 12rpx; margin-bottom: 16rpx; }
.mp-votes-big.mp-votes--ready { background: #fff8e1; color: #b8860b; }
.mp-sheet-statement { font-size: 26rpx; color: #5B6B7F; line-height: 1.8; white-space: pre-wrap; }
.mp-sheet-actions { display: flex; gap: 12rpx; margin-top: 24rpx; }

.mp-reject-sheet { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 40rpx 32rpx calc(48rpx + env(safe-area-inset-bottom)); }
.mp-reject-title { display: block; font-size: 32rpx; font-weight: 700; color: #2C3E50; margin-bottom: 24rpx; }
.mp-reject-input { width: 100%; background: #F5F6FA; border-radius: 12rpx; padding: 16rpx 20rpx; font-size: 28rpx; color: #2C3E50; min-height: 120rpx; box-sizing: border-box; }
</style>
