<template>
  <view class="sc-page">
    <view class="sc-navbar">
      <view class="sc-back" @tap="goBack">←</view>
      <text class="sc-title">我的投稿</text>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="sc-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 统计 -->
      <view class="sc-stat-row">
        <view class="sc-stat">
          <text class="sc-stat-num" style="color:#E67E22;">{{ pendingCount }}</text>
          <text class="sc-stat-label">待审核</text>
        </view>
        <view class="sc-stat">
          <text class="sc-stat-num" style="color:#27AE60;">{{ approvedCount }}</text>
          <text class="sc-stat-label">已通过</text>
        </view>
        <view class="sc-stat">
          <text class="sc-stat-num" style="color:#E74C3C;">{{ rejectedCount }}</text>
          <text class="sc-stat-label">已退回</text>
        </view>
      </view>

      <!-- 审核说明 -->
      <view class="sc-notice">
        <text class="sc-notice-icon">ℹ️</text>
        <text class="sc-notice-text">投稿提交后由教练审核，通过后将对外发布或收录入健康之路案例库</text>
      </view>

      <!-- 投稿列表 -->
      <view v-for="item in myContent" :key="item.id" class="sc-card">
        <view class="sc-card-header">
          <view class="sc-status-tag" :class="'sc-status--' + item.status">
            <text>{{ statusLabel(item.status) }}</text>
          </view>
          <text class="sc-card-date">{{ formatDate(item.created_at) }}</text>
        </view>
        <text class="sc-card-title">{{ item.title }}</text>
        <text v-if="item.review_note" class="sc-review-note">审核意见：{{ item.review_note }}</text>
        <view class="sc-card-footer" v-if="item.status === 'published'">
          <text class="sc-card-stat">❤️ {{ item.likes || 0 }}</text>
          <text class="sc-card-stat">👁 {{ item.views || 0 }}</text>
        </view>
      </view>

      <view v-if="!loading && myContent.length === 0" class="sc-empty">
        <text class="sc-empty-icon">📝</text>
        <text class="sc-empty-text">还没有投稿</text>
        <text class="sc-empty-hint">点击下方按钮提交你的健康经验分享</text>
      </view>
      <view style="height:160rpx;"></view>
    </scroll-view>

    <!-- 新建投稿按钮 -->
    <view class="sc-fab" @tap="openForm">＋ 新建投稿</view>

    <!-- 投稿表单（全页面风格，非 overlay，避免 WeChat textarea 问题） -->
    <view v-if="showForm" class="sc-form-page">
      <view class="sc-form-navbar">
        <view class="sc-form-cancel" @tap="showForm = false">取消</view>
        <text class="sc-form-nav-title">提交投稿</text>
        <view
          class="sc-form-submit"
          :class="{ disabled: !canSubmit || submitting }"
          @tap="submitContent"
        >{{ submitting ? '提交中…' : '提交审核' }}</view>
      </view>
      <scroll-view scroll-y style="height: calc(100vh - 100rpx);">
        <view class="sc-form-body">
          <text class="sc-form-tip">提交后等待教练审核，通常1个工作日内完成</text>

          <view class="sc-form-field">
            <text class="sc-form-label">标题 <text class="sc-required">*</text></text>
            <input
              class="sc-form-input"
              v-model="form.title"
              placeholder="用一句话概括你想分享的内容"
              :maxlength="60"
            />
          </view>

          <view class="sc-form-field">
            <text class="sc-form-label">分享内容 <text class="sc-required">*</text></text>
            <text class="sc-form-hint">分享你的健康经验、心得或故事（至少50字）</text>
            <textarea
              class="sc-form-ta"
              v-model="form.body"
              placeholder="写下你想分享的内容…"
              :maxlength="2000"
              :show-confirm-bar="false"
              auto-height
            />
            <text class="sc-form-count">{{ form.body.length }}/2000</text>
          </view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const loading = ref(false)
const refreshing = ref(false)
const showForm = ref(false)
const submitting = ref(false)
const myContent = ref<any[]>([])
const form = ref({ title: '', body: '' })

const pendingCount  = computed(() => myContent.value.filter(i => i.status === 'pending_review' || i.status === 'pending').length)
const approvedCount = computed(() => myContent.value.filter(i => i.status === 'published' || i.status === 'approved').length)
const rejectedCount = computed(() => myContent.value.filter(i => i.status === 'rejected').length)
const canSubmit = computed(() => form.value.title.trim().length >= 2 && form.value.body.trim().length >= 50)

function statusLabel(s: string): string {
  return ({ pending_review: '待审核', pending: '待审核', published: '已发布', approved: '已通过', rejected: '已退回' } as Record<string, string>)[s] || s
}

function formatDate(t: string): string {
  return t ? new Date(t).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) : ''
}

function openForm() {
  form.value = { title: '', body: '' }
  showForm.value = true
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/content?author=me')
    myContent.value = res.items || []
  } catch {
    myContent.value = []
  }
  loading.value = false
}

async function submitContent() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  try {
    await http('/api/v1/content', {
      method: 'POST',
      data: {
        title: form.value.title.trim(),
        body: form.value.body.trim(),
        content_type: 'article',
        status: 'pending_review',
      },
    })
    showForm.value = false
    form.value = { title: '', body: '' }
    uni.showToast({ title: '已提交审核', icon: 'success' })
    await loadData()
  } catch {
    uni.showToast({ title: '提交失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
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
.sc-page { min-height: 100vh; background: #F5F6FA; }
.sc-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2980B9, #3498DB); color: #fff;
}
.sc-back { font-size: 40rpx; padding: 16rpx; }
.sc-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.sc-scroll { height: calc(100vh - 180rpx); }

.sc-stat-row { display: flex; margin: 24rpx; gap: 16rpx; }
.sc-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx; text-align: center; }
.sc-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.sc-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.sc-notice {
  display: flex; align-items: flex-start; gap: 12rpx;
  margin: 0 24rpx 16rpx; background: #FFF8E6; border-radius: 12rpx; padding: 16rpx 20rpx;
}
.sc-notice-icon { font-size: 28rpx; flex-shrink: 0; }
.sc-notice-text { font-size: 24rpx; color: #8A6500; line-height: 1.5; }

.sc-card { margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.sc-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.sc-status-tag { padding: 4rpx 16rpx; border-radius: 20rpx; font-size: 22rpx; font-weight: 600; }
.sc-status--pending_review, .sc-status--pending { background: #FFF3CD; color: #D68910; }
.sc-status--published, .sc-status--approved { background: #E8F8F0; color: #27AE60; }
.sc-status--rejected { background: #FEE2E2; color: #E74C3C; }
.sc-card-date { font-size: 22rpx; color: #8E99A4; }
.sc-card-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 8rpx; line-height: 1.5; }
.sc-review-note { display: block; font-size: 22rpx; color: #E74C3C; margin-bottom: 8rpx; font-style: italic; }
.sc-card-footer { display: flex; gap: 20rpx; }
.sc-card-stat { font-size: 22rpx; color: #8E99A4; }

.sc-empty { text-align: center; padding: 100rpx 0; }
.sc-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.sc-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; }
.sc-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 8rpx; }

.sc-fab {
  position: fixed; bottom: calc(48rpx + env(safe-area-inset-bottom)); left: 50%;
  transform: translateX(-50%); background: #3498DB; color: #fff;
  padding: 24rpx 64rpx; border-radius: 50rpx; font-size: 28rpx; font-weight: 600;
  box-shadow: 0 8rpx 24rpx rgba(52,152,219,0.4); white-space: nowrap;
}

/* 投稿全屏表单 */
.sc-form-page {
  position: fixed; inset: 0; background: #F5F6FA; z-index: 200;
}
.sc-form-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top));
  background: #fff; border-bottom: 1rpx solid #f0f0f0;
}
.sc-form-cancel { font-size: 28rpx; color: #8E99A4; padding: 8rpx 16rpx; }
.sc-form-nav-title { font-size: 32rpx; font-weight: 700; color: #2C3E50; }
.sc-form-submit {
  font-size: 28rpx; font-weight: 600; color: #fff;
  background: #3498DB; padding: 10rpx 24rpx; border-radius: 20rpx;
}
.sc-form-submit.disabled { opacity: 0.4; }

.sc-form-body { padding: 24rpx; }
.sc-form-tip {
  display: block; font-size: 24rpx; color: #8A6500; background: #FFF8E6;
  border-radius: 10rpx; padding: 16rpx 20rpx; margin-bottom: 24rpx; line-height: 1.5;
}
.sc-form-field { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; }
.sc-form-label { display: block; font-size: 26rpx; font-weight: 700; color: #333; margin-bottom: 8rpx; }
.sc-required { color: #E74C3C; }
.sc-form-hint { display: block; font-size: 22rpx; color: #9ca3af; margin-bottom: 10rpx; }
.sc-form-input {
  width: 100%; font-size: 28rpx; color: #333;
  padding: 8rpx 0; border-bottom: 1rpx solid #f0f0f0;
}
.sc-form-ta {
  width: 100%; min-height: 200rpx; background: #fafafa; border-radius: 10rpx;
  padding: 16rpx; box-sizing: border-box; font-size: 28rpx; color: #333; line-height: 1.6;
}
.sc-form-count { display: block; text-align: right; font-size: 20rpx; color: #bbb; margin-top: 4rpx; }
</style>
