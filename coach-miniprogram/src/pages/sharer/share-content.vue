<template>
  <view class="sc-page">
    <view class="sc-navbar">
      <view class="sc-back" @tap="goBack">←</view>
      <text class="sc-title">内容分享</text>
      <view style="width:80rpx;"></view>
    </view>
    <scroll-view scroll-y class="sc-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view class="sc-stat-row">
        <view class="sc-stat"><text class="sc-stat-num">{{ myContent.length }}</text><text class="sc-stat-label">已发布</text></view>
        <view class="sc-stat"><text class="sc-stat-num" style="color:#E67E22;">{{ totalLikes }}</text><text class="sc-stat-label">获赞</text></view>
        <view class="sc-stat"><text class="sc-stat-num" style="color:#3498DB;">{{ totalViews }}</text><text class="sc-stat-label">阅读</text></view>
      </view>

      <view v-for="item in myContent" :key="item.id" class="sc-card">
        <view class="sc-card-header">
          <view class="sc-type-tag" :style="{ background: item.content_type === 'video' ? '#FFF0E6' : '#EEF6FF' }">
            <text :style="{ color: item.content_type === 'video' ? '#E67E22' : '#3498DB' }">
              {{ item.content_type === 'video' ? '视频' : '文章' }}
            </text>
          </view>
          <text class="sc-card-date">{{ formatDate(item.created_at) }}</text>
        </view>
        <text class="sc-card-title">{{ item.title }}</text>
        <view class="sc-card-footer">
          <text class="sc-card-stat">❤️ {{ item.likes || 0 }}</text>
          <text class="sc-card-stat">👁 {{ item.views || 0 }}</text>
        </view>
      </view>

      <view v-if="!loading && myContent.length === 0" class="sc-empty">
        <text class="sc-empty-icon">📝</text>
        <text class="sc-empty-text">还没有发布内容</text>
        <text class="sc-empty-hint">点击下方按钮分享您的健康经验</text>
      </view>
      <view style="height:160rpx;"></view>
    </scroll-view>

    <!-- 发布按钮 -->
    <view class="sc-fab" @tap="showModal = true">＋ 发布新内容</view>

    <!-- 发布 Modal -->
    <view v-if="showModal" class="sc-mask" @tap.self="showModal = false">
      <view class="sc-modal">
        <text class="sc-modal-title">发布内容</text>
        <text class="sc-modal-label">标题 *</text>
        <input class="sc-modal-input" v-model="form.title" placeholder="请输入内容标题" maxlength="50" />
        <text class="sc-modal-label">内容 *</text>
        <textarea class="sc-modal-textarea" v-model="form.body" placeholder="分享您的健康经验、心得或故事…" maxlength="1000" />
        <view class="sc-modal-actions">
          <view class="sc-modal-btn sc-modal-cancel" @tap="showModal = false">取消</view>
          <view
            class="sc-modal-btn sc-modal-submit"
            :class="{ 'sc-modal-btn--loading': submitting }"
            @tap="submitContent"
          >{{ submitting ? '发布中…' : '发布' }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const loading = ref(false)
const refreshing = ref(false)
const showModal = ref(false)
const submitting = ref(false)
const myContent = ref<any[]>([])
const form = ref({ title: '', body: '' })

const totalLikes = computed(() => myContent.value.reduce((s, i) => s + (i.likes || 0), 0))
const totalViews = computed(() => myContent.value.reduce((s, i) => s + (i.views || 0), 0))

function formatDate(t: string): string {
  return t ? new Date(t).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) : ''
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/content?author=me&status=published')
    myContent.value = res.items || []
  } catch {
    myContent.value = []
  }
  loading.value = false
}

async function submitContent() {
  if (!form.value.title.trim() || !form.value.body.trim()) {
    uni.showToast({ title: '标题和内容不能为空', icon: 'none' })
    return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    await http('/api/v1/content', {
      method: 'POST',
      data: { title: form.value.title, body: form.value.body, content_type: 'article', status: 'published' },
    })
    showModal.value = false
    form.value = { title: '', body: '' }
    uni.showToast({ title: '发布成功', icon: 'success' })
    await loadData()
  } catch {
    uni.showToast({ title: '发布失败', icon: 'none' })
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
  else uni.switchTab({ url: '/pages/home/index' })
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
.sc-card { margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.sc-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.sc-type-tag { padding: 4rpx 16rpx; border-radius: 20rpx; font-size: 22rpx; }
.sc-card-date { font-size: 22rpx; color: #8E99A4; }
.sc-card-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 12rpx; line-height: 1.5; }
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
.sc-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  z-index: 100; display: flex; align-items: flex-end;
}
.sc-modal {
  width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0;
  padding: 40rpx 32rpx calc(48rpx + env(safe-area-inset-bottom));
}
.sc-modal-title { display: block; font-size: 34rpx; font-weight: 700; color: #2C3E50; text-align: center; margin-bottom: 32rpx; }
.sc-modal-label { display: block; font-size: 24rpx; color: #8E99A4; margin-bottom: 8rpx; margin-top: 16rpx; }
.sc-modal-input {
  width: 100%; background: #F5F6FA; border-radius: 12rpx;
  padding: 18rpx 20rpx; font-size: 28rpx; box-sizing: border-box;
}
.sc-modal-textarea {
  width: 100%; background: #F5F6FA; border-radius: 12rpx;
  padding: 18rpx 20rpx; font-size: 26rpx; box-sizing: border-box;
  height: 200rpx; line-height: 1.6;
}
.sc-modal-actions { display: flex; gap: 20rpx; margin-top: 32rpx; }
.sc-modal-btn { flex: 1; text-align: center; padding: 26rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.sc-modal-cancel { background: #F0F0F0; color: #5B6B7F; }
.sc-modal-submit { background: #3498DB; color: #fff; }
.sc-modal-btn--loading { background: #9EC4DB; }
</style>
