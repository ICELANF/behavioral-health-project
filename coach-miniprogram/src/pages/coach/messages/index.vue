<template>
  <view class="msg-page">
    <view class="msg-navbar">
      <view class="msg-nav-back" @tap="goBack">←</view>
      <text class="msg-nav-title">推送记录</text>
      <view class="msg-nav-badge" v-if="unreadTotal > 0">{{ unreadTotal }}</view>
      <view v-else class="msg-nav-action" />
    </view>

    <!-- 说明条：与「我的学员」的区别 -->
    <view class="msg-desc-bar">
      <text class="msg-desc-text">教练→学员的处方、评估、AI建议推送历史 · {{ students.length }}名绑定学员</text>
    </view>

    <scroll-view scroll-y class="msg-list"
      refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <view v-for="s in students" :key="s.id" class="msg-conv-card" @tap="goDetail(s.id)">
        <view class="msg-conv-avatar" :style="{ background: avatarColor(s.name) }">
          {{ (s.name || '?')[0] }}
        </view>
        <view class="msg-conv-body">
          <view class="msg-conv-header">
            <text class="msg-conv-name">{{ s.name }}</text>
            <text class="msg-conv-time">{{ s.last_push_time }}</text>
          </view>
          <text class="msg-conv-preview">{{ s.last_push_content }}</text>
        </view>
        <view class="msg-conv-meta">
          <view v-if="s.unread > 0" class="msg-conv-unread">{{ s.unread }}</view>
          <text v-else class="msg-conv-arrow">›</text>
          <text class="msg-push-count" v-if="s.push_count > 0">{{ s.push_count }}条推送</text>
        </view>
      </view>

      <view v-if="!loading && students.length === 0" class="msg-empty">
        <text class="msg-empty-icon">📤</text>
        <text class="msg-empty-text">暂无推送记录</text>
        <text class="msg-empty-sub">在学员档案中开具处方或分配评估后会显示在这里</text>
      </view>
      <view v-if="loading" class="msg-empty">
        <text class="msg-empty-text">加载中...</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { httpReq as http } from '@/api/request'
import { avatarColor } from '@/utils/studentUtils'

const refreshing = ref(false)
const loading = ref(false)
const students = ref<any[]>([])

const unreadTotal = computed(() => students.value.reduce((s, i) => s + (i.unread || 0), 0))

async function loadData() {
  loading.value = true
  try {
    // 仅加载教练绑定学员（dashboard 数据）
    const res = await http<any>('/api/v1/coach/dashboard')
    const raw: any[] = res.students || res.data?.students || []

    students.value = (Array.isArray(raw) ? raw : []).map((s: any) => {
      const sid = s.id || s.user_id
      return {
        id: sid,
        name: s.name || s.full_name || '未知',
        last_push_content: s.last_action || '点击查看学员处方与督导记录',
        last_push_time: '',
        push_count: s.push_count ?? 0,
        unread: s.unread_count || 0,
      }
    })
  } catch (e) {
    console.warn('[coach/messages] loadData:', e)
    students.value = []
  }
  loading.value = false
}

function goDetail(id: number) {
  // 进入学员档案 → 督导记录 Tab 直接展示推送/处方互动历史
  uni.navigateTo({ url: '/pages/coach/students/detail?id=' + id + '&tab=supervision' })
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onShow(() => { loadData() })
</script>

<style scoped>
.msg-page { min-height: 100vh; background: #F5F6FA; }
.msg-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%); color: #fff;
}
.msg-nav-back { font-size: 40rpx; padding: 16rpx; }
.msg-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.msg-nav-badge {
  min-width: 40rpx; height: 40rpx; border-radius: 20rpx;
  background: #E74C3C; color: #fff; font-size: 22rpx;
  display: flex; align-items: center; justify-content: center; padding: 0 8rpx;
}
.msg-nav-action { width: 72rpx; }

.msg-desc-bar { padding: 12rpx 24rpx; background: #EBF5FB; }
.msg-desc-text { font-size: 22rpx; color: #3498DB; display: block; }

.msg-list { height: calc(100vh - 220rpx); padding: 16rpx 24rpx; }

.msg-conv-card {
  display: flex; align-items: center; gap: 16rpx;
  background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04);
}
.msg-conv-avatar {
  width: 80rpx; height: 80rpx; border-radius: 50%;
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; font-weight: 600; flex-shrink: 0;
}
.msg-conv-body { flex: 1; overflow: hidden; }
.msg-conv-header { display: flex; justify-content: space-between; align-items: center; }
.msg-conv-name { font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.msg-conv-time { font-size: 22rpx; color: #8E99A4; }
.msg-conv-preview {
  display: block; font-size: 24rpx; color: #8E99A4;
  margin-top: 6rpx; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
}
.msg-conv-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 6rpx; }
.msg-conv-unread {
  min-width: 36rpx; height: 36rpx; border-radius: 18rpx;
  background: #E74C3C; color: #fff; font-size: 22rpx;
  display: flex; align-items: center; justify-content: center; padding: 0 8rpx;
}
.msg-conv-arrow { font-size: 36rpx; color: #CCC; }
.msg-push-count { font-size: 20rpx; color: #3498DB; }

.msg-empty { text-align: center; padding: 100rpx 32rpx; }
.msg-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.msg-empty-text { display: block; font-size: 28rpx; color: #8E99A4; }
.msg-empty-sub { display: block; font-size: 24rpx; color: #BDC3C7; margin-top: 12rpx; line-height: 1.5; }
</style>
