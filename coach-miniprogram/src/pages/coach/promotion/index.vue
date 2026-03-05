<template>
  <view class="pr-page">
    <view class="pr-navbar">
      <view class="pr-back" @tap="goBack">←</view>
      <text class="pr-title">晋级申请审核</text>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="pr-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 统计 -->
      <view class="pr-stat-row">
        <view class="pr-stat">
          <text class="pr-stat-num" style="color:#E67E22;">{{ pendingCount }}</text>
          <text class="pr-stat-label">待审核</text>
        </view>
        <view class="pr-stat">
          <text class="pr-stat-num" style="color:#27AE60;">{{ approvedCount }}</text>
          <text class="pr-stat-label">已通过</text>
        </view>
        <view class="pr-stat">
          <text class="pr-stat-num" style="color:#E74C3C;">{{ rejectedCount }}</text>
          <text class="pr-stat-label">已拒绝</text>
        </view>
      </view>

      <!-- 申请列表 -->
      <view v-for="item in applications" :key="item.application_id" class="pr-card">
        <view class="pr-card-head">
          <view class="pr-avatar" :style="{ background: avatarColor(item.full_name || item.username) }">
            {{ (item.full_name || item.username || '?')[0] }}
          </view>
          <view class="pr-card-info">
            <text class="pr-name">{{ item.full_name || item.username }}</text>
            <text class="pr-path">{{ roleLabel(item.current_level) }} → {{ roleLabel(item.target_level) }}</text>
          </view>
          <view class="pr-status-tag" :class="'pr-status--' + item.status">
            {{ statusLabel(item.status) }}
          </view>
        </view>

        <text class="pr-date">申请时间：{{ formatDate(item.applied_at) }}</text>

        <view v-if="item.status === 'pending'" class="pr-actions">
          <view class="pr-reject-btn" @tap="openReview(item, false)">拒绝</view>
          <view class="pr-approve-btn" @tap="openReview(item, true)">通过</view>
        </view>
        <text v-else-if="item.reviewer_comment" class="pr-comment">
          审核意见：{{ item.reviewer_comment }}
        </text>
      </view>

      <view v-if="!loading && applications.length === 0" class="pr-empty">
        <text class="pr-empty-icon">📋</text>
        <text class="pr-empty-text">暂无申请记录</text>
      </view>
      <view style="height:80rpx;"></view>
    </scroll-view>

    <!-- 审核弹窗 -->
    <view v-if="showModal" class="pr-mask" @tap.stop>
      <view class="pr-sheet">
        <text class="pr-sheet-title">{{ modalApprove ? '通过申请' : '拒绝申请' }}</text>
        <text class="pr-sheet-sub">{{ modalItem?.full_name || modalItem?.username }}</text>
        <textarea
          class="pr-reason-ta"
          v-model="reviewReason"
          :placeholder="modalApprove ? '填写通过意见（可选）' : '填写拒绝原因（建议填写）'"
          :maxlength="200"
          :show-confirm-bar="false"
        />
        <view class="pr-sheet-actions">
          <view class="pr-sheet-cancel" @tap="showModal = false">取消</view>
          <view
            class="pr-sheet-confirm"
            :class="{ 'pr-sheet-confirm--danger': !modalApprove, submitting }"
            @tap="submitReview"
          >{{ submitting ? '提交中…' : (modalApprove ? '确认通过' : '确认拒绝') }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'
import { avatarColor } from '@/utils/studentUtils'

const loading = ref(false)
const refreshing = ref(false)
const submitting = ref(false)
const applications = ref<any[]>([])

const showModal = ref(false)
const modalItem = ref<any>(null)
const modalApprove = ref(true)
const reviewReason = ref('')

const pendingCount  = computed(() => applications.value.filter(a => a.status === 'pending').length)
const approvedCount = computed(() => applications.value.filter(a => a.status === 'approved').length)
const rejectedCount = computed(() => applications.value.filter(a => a.status === 'rejected').length)

function roleLabel(r: string): string {
  return ({
    observer:'观察员', grower:'成长者', sharer:'分享者',
    coach:'行为健康教练', promoter:'行为健康促进师', supervisor:'行为健康促进师', master:'行为健康大师',
    OBSERVER:'观察员', GROWER:'成长者', SHARER:'分享者',
    COACH:'行为健康教练', PROMOTER:'行为健康促进师', MASTER:'行为健康大师',
  } as Record<string, string>)[r] || r || '—'
}
function statusLabel(s: string): string {
  return ({ pending:'待审核', approved:'已通过', rejected:'已拒绝' } as Record<string, string>)[s] || s
}
function formatDate(iso: string): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/promotion/applications')
    applications.value = res.applications || []
  } catch { applications.value = [] }
  loading.value = false
}

function openReview(item: any, approve: boolean) {
  modalItem.value = item
  modalApprove.value = approve
  reviewReason.value = ''
  showModal.value = true
}

async function submitReview() {
  if (submitting.value || !modalItem.value) return
  submitting.value = true
  try {
    await http(`/api/v1/promotion/review/${modalItem.value.application_id}`, {
      method: 'POST',
      data: { approved: modalApprove.value, reason: reviewReason.value.trim() },
    })
    uni.showToast({ title: modalApprove.value ? '已通过申请' : '已拒绝申请', icon: 'success' })
    showModal.value = false
    await loadData()
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally { submitting.value = false }
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
.pr-page { min-height: 100vh; background: #F5F6FA; }
.pr-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #8E44AD, #9B59B6); color: #fff;
}
.pr-back { font-size: 40rpx; padding: 16rpx; }
.pr-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.pr-scroll { height: calc(100vh - 180rpx); }

.pr-stat-row { display: flex; margin: 24rpx; gap: 16rpx; }
.pr-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx; text-align: center; }
.pr-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.pr-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.pr-card { margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.pr-card-head { display: flex; align-items: center; gap: 16rpx; margin-bottom: 12rpx; }
.pr-avatar { width: 72rpx; height: 72rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 28rpx; font-weight: 700; flex-shrink: 0; }
.pr-card-info { flex: 1; }
.pr-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.pr-path { font-size: 22rpx; color: #8E99A4; }
.pr-status-tag { padding: 4rpx 16rpx; border-radius: 20rpx; font-size: 22rpx; font-weight: 600; }
.pr-status--pending { background: #FFF3CD; color: #D68910; }
.pr-status--approved { background: #E8F8F0; color: #27AE60; }
.pr-status--rejected { background: #FEE2E2; color: #E74C3C; }
.pr-date { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 16rpx; }
.pr-actions { display: flex; gap: 12rpx; }
.pr-approve-btn, .pr-reject-btn { flex: 1; padding: 16rpx; border-radius: 12rpx; text-align: center; font-size: 26rpx; font-weight: 600; }
.pr-approve-btn { background: #2D8E69; color: #fff; }
.pr-reject-btn { background: #F5F6FA; color: #8E99A4; border: 1rpx solid #E0E0E0; }
.pr-comment { display: block; font-size: 22rpx; color: #8E99A4; font-style: italic; }

.pr-empty { text-align: center; padding: 120rpx 0; }
.pr-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.pr-empty-text { font-size: 26rpx; color: #8E99A4; }

/* Modal */
.pr-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: flex-end; }
.pr-sheet { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 40rpx 32rpx calc(48rpx + env(safe-area-inset-bottom)); }
.pr-sheet-title { display: block; font-size: 34rpx; font-weight: 700; color: #2C3E50; text-align: center; }
.pr-sheet-sub { display: block; font-size: 26rpx; color: #8E99A4; text-align: center; margin: 8rpx 0 24rpx; }
.pr-reason-ta { width: 100%; min-height: 120rpx; background: #F5F6FA; border-radius: 12rpx; padding: 16rpx; box-sizing: border-box; font-size: 26rpx; color: #333; margin-bottom: 24rpx; }
.pr-sheet-actions { display: flex; gap: 16rpx; }
.pr-sheet-cancel { flex: 1; padding: 24rpx 0; border-radius: 16rpx; background: #F0F0F0; color: #5B6B7F; text-align: center; font-size: 28rpx; font-weight: 600; }
.pr-sheet-confirm { flex: 2; padding: 24rpx 0; border-radius: 16rpx; background: #2D8E69; color: #fff; text-align: center; font-size: 28rpx; font-weight: 600; }
.pr-sheet-confirm--danger { background: #E74C3C; }
.pr-sheet-confirm.submitting { opacity: 0.5; }
</style>
