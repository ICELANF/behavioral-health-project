<template>
  <view class="cinv-page">
    <scroll-view scroll-y class="cinv-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <view class="cinv-list">
        <view v-for="item in invitations" :key="item.id" class="cinv-card">
          <view class="cinv-card-top">
            <view class="cinv-avatar" :style="{ background: avatarColor(item.from_name || item.from_user?.name) }">
              {{ (item.from_name || item.from_user?.name || '?')[0] }}
            </view>
            <view class="cinv-card-info">
              <text class="cinv-from-name">{{ item.from_name || item.from_user?.name || '用户' }}</text>
              <text class="cinv-time">{{ formatTime(item.created_at) }}邀请你</text>
            </view>
          </view>
          <text v-if="item.message" class="cinv-message">💬 {{ item.message }}</text>
          <view class="cinv-actions">
            <view class="cinv-accept-btn" @tap="accept(item)"><text>接受</text></view>
            <view class="cinv-reject-btn" @tap="reject(item)"><text>拒绝</text></view>
          </view>
        </view>
      </view>

      <view v-if="invitations.length === 0 && !loading" class="cinv-empty">
        <text class="cinv-empty-icon">📩</text>
        <text class="cinv-empty-text">暂无待处理邀请</text>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const invitations = ref<any[]>([])
const refreshing = ref(false)
const loading = ref(false)

const colorPool = ['#3498DB','#E74C3C','#27AE60','#9B59B6','#E67E22','#1ABC9C']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0; for (const c of name) h = c.charCodeAt(0) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}

function formatTime(iso: string): string {
  if (!iso) return ''
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  return Math.floor(diff / 86400) + '天前'
}

async function loadData() {
  loading.value = true
  try {
    // companions/{id} routing conflict workaround: load from companions with status=pending
    const res = await http<any>('/api/v1/companions?status=pending_invitation')
    invitations.value = res?.items || []
  } catch { invitations.value = [] } finally { loading.value = false }
}

async function accept(item: any) {
  try {
    await http(`/api/v1/companions/invitations/${item.id}/accept`, { method: 'POST' })
    invitations.value = invitations.value.filter(i => i.id !== item.id)
    uni.showToast({ title: '已接受邀请', icon: 'success' })
  } catch { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

async function reject(item: any) {
  try {
    await http(`/api/v1/companions/invitations/${item.id}/reject`, { method: 'POST' })
    invitations.value = invitations.value.filter(i => i.id !== item.id)
    uni.showToast({ title: '已拒绝邀请', icon: 'none' })
  } catch { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.cinv-page { min-height: 100vh; background: #F5F6FA; }
.cinv-scroll { height: 100vh; }
.cinv-list { padding: 16rpx 24rpx; }
.cinv-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; }
.cinv-card-top { display: flex; align-items: center; gap: 16rpx; margin-bottom: 16rpx; }
.cinv-avatar { width: 72rpx; height: 72rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 28rpx; font-weight: 700; flex-shrink: 0; }
.cinv-card-info { flex: 1; }
.cinv-from-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.cinv-time { font-size: 22rpx; color: #8E99A4; }
.cinv-message { display: block; font-size: 24rpx; color: #5B6B7F; background: #F8F8F8; border-radius: 8rpx; padding: 10rpx 14rpx; margin-bottom: 16rpx; }
.cinv-actions { display: flex; gap: 12rpx; }
.cinv-accept-btn, .cinv-reject-btn { flex: 1; padding: 14rpx; border-radius: 12rpx; text-align: center; font-size: 26rpx; font-weight: 600; }
.cinv-accept-btn { background: #2D8E69; color: #fff; }
.cinv-reject-btn { background: #F5F6FA; color: #8E99A4; border: 1rpx solid #E0E0E0; }
.cinv-empty { text-align: center; padding: 120rpx 0; }
.cinv-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.cinv-empty-text { font-size: 26rpx; color: #8E99A4; }
</style>
