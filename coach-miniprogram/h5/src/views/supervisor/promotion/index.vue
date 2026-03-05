<template>
  <view class="sp-page">
    <view class="sp-navbar">
      <view class="sp-back" @tap="goBack">←</view>
      <text class="sp-title">晋级复核（L2）</text>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="sp-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <view class="sp-notice">
        <text class="sp-notice-text">🏅 以下申请已通过教练初审，请作为行为健康促进师进行复核</text>
      </view>

      <view v-for="item in items" :key="item.application_id" class="sp-card">
        <view class="sp-card-head">
          <view class="sp-level-tag">{{ roleLabel(item.current_level) }} → {{ roleLabel(item.target_level) }}</view>
          <text class="sp-date">{{ fmtDate(item.applied_at) }}</text>
        </view>
        <text class="sp-name">{{ item.full_name || item.username }}</text>
        <text v-if="item.statement" class="sp-statement">{{ item.statement }}</text>

        <view class="sp-actions">
          <view class="sp-view-btn" @tap="openDetail(item)">查看详情</view>
          <view class="sp-reject-btn" @tap="doReview(item, false)">拒绝</view>
          <view class="sp-approve-btn" @tap="doReview(item, true)">通过 →L3</view>
        </view>
      </view>

      <view v-if="!loading && items.length === 0" class="sp-empty">
        <text class="sp-empty-icon">✅</text>
        <text class="sp-empty-text">暂无待复核申请</text>
      </view>
      <view style="height:80rpx;"></view>
    </scroll-view>

    <!-- 详情弹窗 -->
    <view v-if="detailItem" class="sp-mask" @tap="detailItem = null">
      <view class="sp-sheet" @tap.stop>
        <view class="sp-sheet-head">
          <text class="sp-sheet-name">{{ detailItem.full_name || detailItem.username }}</text>
          <view class="sp-sheet-close" @tap="detailItem = null">×</view>
        </view>
        <view class="sp-sheet-meta">
          <text>{{ roleLabel(detailItem.current_level) }} → {{ roleLabel(detailItem.target_level) }}</text>
          <text style="margin-left:16rpx;">申请于 {{ fmtDate(detailItem.applied_at) }}</text>
        </view>
        <scroll-view scroll-y style="max-height:50vh;">
          <text class="sp-sheet-statement">{{ detailItem.statement || '（申请人未填写说明）' }}</text>
        </scroll-view>
        <view class="sp-sheet-actions">
          <view class="sp-reject-btn" @tap="doReview(detailItem, false); detailItem = null">拒绝</view>
          <view class="sp-approve-btn" @tap="doReview(detailItem, true); detailItem = null">通过复核</view>
        </view>
      </view>
    </view>

    <!-- 拒绝理由 Modal -->
    <view v-if="rejectModal.show" class="sp-mask" @tap="rejectModal.show = false">
      <view class="sp-reject-sheet" @tap.stop>
        <text class="sp-reject-title">填写拒绝理由</text>
        <textarea class="sp-reject-input" v-model="rejectModal.reason"
          placeholder="请说明拒绝原因（必填）" maxlength="200" />
        <view class="sp-sheet-actions">
          <view class="sp-view-btn" @tap="rejectModal.show = false">取消</view>
          <view class="sp-reject-btn" @tap="confirmReject">确认拒绝</view>
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
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function openDetail(item: any) { detailItem.value = item }

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/promotion/applications?status=pending')
    items.value = (res.applications || []).filter((a: any) => a.review_stage === 'L2')
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
    })
    uni.showToast({ title: approved ? '已通过，转大师终审' : '已拒绝', icon: 'success' })
    items.value = items.value.filter(i => i.application_id !== item.application_id)
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
.sp-page { min-height: 100vh; background: #F5F6FA; }
.sp-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #8e24aa, #ce93d8); color: #fff;
}
.sp-back { font-size: 40rpx; padding: 16rpx; }
.sp-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.sp-scroll { height: calc(100vh - 180rpx); }

.sp-notice { margin: 16rpx 24rpx; background: #f3e5f5; border-radius: 12rpx; padding: 16rpx 20rpx; }
.sp-notice-text { font-size: 24rpx; color: #7b1fa2; line-height: 1.5; }

.sp-card { margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.sp-card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10rpx; }
.sp-level-tag { padding: 4rpx 16rpx; background: #f3e5f5; color: #8e24aa; border-radius: 20rpx; font-size: 22rpx; font-weight: 700; }
.sp-date { font-size: 22rpx; color: #8E99A4; }
.sp-name { display: block; font-size: 30rpx; font-weight: 700; color: #2C3E50; margin-bottom: 8rpx; }
.sp-statement { display: block; font-size: 24rpx; color: #5B6B7F; margin-bottom: 16rpx; line-height: 1.6;
  overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.sp-actions { display: flex; gap: 10rpx; }
.sp-view-btn { flex: 1; padding: 14rpx; border-radius: 12rpx; background: #f3e5f5; color: #8e24aa; text-align: center; font-size: 24rpx; font-weight: 600; }
.sp-approve-btn { flex: 1; padding: 14rpx; border-radius: 12rpx; background: #8e24aa; color: #fff; text-align: center; font-size: 24rpx; font-weight: 600; }
.sp-reject-btn { flex: 1; padding: 14rpx; border-radius: 12rpx; background: #F5F6FA; color: #8E99A4; border: 1rpx solid #E0E0E0; text-align: center; font-size: 24rpx; font-weight: 600; }

.sp-empty { text-align: center; padding: 120rpx 0; }
.sp-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.sp-empty-text { font-size: 26rpx; color: #8E99A4; }

.sp-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: flex-end; }
.sp-sheet { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 32rpx 32rpx calc(48rpx + env(safe-area-inset-bottom)); max-height: 85vh; display: flex; flex-direction: column; }
.sp-sheet-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.sp-sheet-name { font-size: 32rpx; font-weight: 700; color: #2C3E50; }
.sp-sheet-close { font-size: 40rpx; color: #8E99A4; padding: 0 0 0 16rpx; }
.sp-sheet-meta { font-size: 22rpx; color: #8E99A4; margin-bottom: 20rpx; display: flex; }
.sp-sheet-statement { font-size: 26rpx; color: #5B6B7F; line-height: 1.8; white-space: pre-wrap; }
.sp-sheet-actions { display: flex; gap: 12rpx; margin-top: 24rpx; }

.sp-reject-sheet { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 40rpx 32rpx calc(48rpx + env(safe-area-inset-bottom)); }
.sp-reject-title { display: block; font-size: 32rpx; font-weight: 700; color: #2C3E50; margin-bottom: 24rpx; }
.sp-reject-input { width: 100%; background: #F5F6FA; border-radius: 12rpx; padding: 16rpx 20rpx; font-size: 28rpx; color: #2C3E50; min-height: 120rpx; box-sizing: border-box; }
</style>
