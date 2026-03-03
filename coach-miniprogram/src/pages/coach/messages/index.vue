<template>
  <view class="msg-page">
    <view class="msg-navbar">
      <view class="msg-nav-back" @tap="goBack">←</view>
      <text class="msg-nav-title">学员会话</text>
      <view class="msg-nav-action" />
    </view>

    <scroll-view scroll-y class="msg-list"
      refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <view v-for="s in students" :key="s.id" class="msg-conv-card" @tap="goStudentDetail(s.id)">
        <view class="msg-conv-avatar" :style="{ background: s.risk_level >= 3 ? '#E74C3C' : '#27AE60' }">
          {{ (s.name || '?')[0] }}
        </view>
        <view class="msg-conv-body">
          <view class="msg-conv-header">
            <text class="msg-conv-name">{{ s.name }}</text>
            <text class="msg-conv-time">{{ s.last_time }}</text>
          </view>
          <text class="msg-conv-preview">{{ s.last_message }}</text>
        </view>
        <view v-if="s.unread > 0" class="msg-conv-unread">{{ s.unread }}</view>
        <text v-else class="msg-conv-arrow">›</text>
      </view>

      <view v-if="!loading && students.length === 0" class="msg-empty">
        <text class="msg-empty-icon">💬</text>
        <text class="msg-empty-text">暂无学员会话</text>
      </view>
      <view v-if="loading" class="msg-empty">
        <text class="msg-empty-text">加载中...</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const refreshing = ref(false)
const loading = ref(false)
const students = ref<any[]>([])

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    const raw = res.students || res.data?.students || []
    students.value = (Array.isArray(raw) ? raw : []).map((s: any) => ({
      id: s.id || s.user_id,
      name: s.name || s.full_name || '未知',
      risk_level: parseInt(String(s.risk_level ?? '0').replace(/\D/g, '') || '0'),
      last_message: s.last_action || ('最近活跃' + (s.days_since_last_contact ?? '—') + '天前'),
      last_time: '',
      unread: s.unread_count || 0,
    }))
  } catch (e) {
    console.warn('[coach/messages] load:', e)
    try {
      const res2 = await http<any>('/api/v1/coach/students')
      const raw2 = res2.items || res2.students || (Array.isArray(res2) ? res2 : [])
      students.value = raw2.map((s: any) => ({
        id: s.id || s.user_id,
        name: s.name || s.full_name || '未知',
        risk_level: parseInt(String(s.risk_level ?? '0').replace(/\D/g, '') || '0'),
        last_message: '最近活跃' + (s.days_since_last_contact ?? '—') + '天前',
        last_time: '',
        unread: 0,
      }))
    } catch (e2) { console.warn('[coach/messages] fallback:', e2) }
  }
  loading.value = false
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

function goStudentDetail(id: number) {
  uni.navigateTo({ url: '/pages/coach/students/detail?id=' + id })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
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
.msg-nav-action { width: 60rpx; }

.msg-list { height: calc(100vh - 180rpx); padding: 16rpx 24rpx; }

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
.msg-conv-unread {
  min-width: 36rpx; height: 36rpx; border-radius: 18rpx;
  background: #E74C3C; color: #fff; font-size: 22rpx;
  display: flex; align-items: center; justify-content: center; padding: 0 8rpx;
}
.msg-conv-arrow { font-size: 36rpx; color: #CCC; }

.msg-empty { text-align: center; padding: 120rpx 0; }
.msg-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.msg-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>
