<template>
  <view class="comp-page">
    <view class="comp-header">
      <text class="comp-title">我的同道者</text>
      <view class="comp-invite-btn" @tap="goInvite">
        <text>+ 邀请</text>
      </view>
    </view>

    <scroll-view scroll-y class="comp-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 邀请通知 -->
      <view v-if="invitationCount > 0" class="comp-notice" @tap="goInvitations">
        <text class="comp-notice-icon">🔔</text>
        <text class="comp-notice-text">你有 {{ invitationCount }} 条同道者邀请待处理</text>
        <text class="comp-notice-arrow">›</text>
      </view>

      <!-- 同道者列表 -->
      <view class="comp-list">
        <view v-for="c in companions" :key="c.id" class="comp-card" @tap="goDetail(c)">
          <view class="comp-avatar" :style="{ background: avatarColor(c.name || c.username) }">
            {{ (c.name || c.username || '?')[0] }}
          </view>
          <view class="comp-card-info">
            <text class="comp-card-name">{{ c.name || c.username || '同道者' }}</text>
            <text class="comp-card-level">{{ levelName(c.level || c.journey_level) }}</text>
          </view>
          <view class="comp-card-days">
            <text class="comp-days-num">{{ c.companion_days || 0 }}</text>
            <text class="comp-days-label">同行天</text>
          </view>
        </view>
      </view>

      <view v-if="companions.length === 0 && !loading" class="comp-empty">
        <text class="comp-empty-icon">👥</text>
        <text class="comp-empty-title">还没有同道者</text>
        <text class="comp-empty-sub">邀请志同道合的朋友共同成长</text>
        <view class="comp-empty-btn" @tap="goInvite">
          <text>邀请同道者</text>
        </view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const companions = ref<any[]>([])
const invitationCount = ref(0)
const refreshing = ref(false)
const loading = ref(false)

const colorPool = ['#3498DB','#E74C3C','#27AE60','#9B59B6','#E67E22','#1ABC9C','#34495E']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0; for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}

function levelName(key: string): string {
  return { observer: '观察者', grower: '成长者', sharer: '分享者', guide: '向导者', master: '大师' }[key] || (key || '成长者')
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/companions')
    companions.value = res?.items || []
  } catch { companions.value = [] } finally { loading.value = false }
}

function goInvite() { uni.navigateTo({ url: '/pages/companions/invite' }) }
function goInvitations() { uni.navigateTo({ url: '/pages/companions/invitations' }) }
function goDetail(c: any) { uni.navigateTo({ url: '/pages/companions/detail?id=' + c.id }) }

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.comp-page { min-height: 100vh; background: #F5F6FA; }

.comp-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 24rpx 32rpx;
  padding-top: calc(80rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  color: #fff;
}
.comp-title { font-size: 38rpx; font-weight: 700; }
.comp-invite-btn { background: rgba(255,255,255,0.2); padding: 10rpx 24rpx; border-radius: 12rpx; font-size: 26rpx; }

.comp-scroll { height: calc(100vh - 200rpx); }

.comp-notice { display: flex; align-items: center; gap: 12rpx; background: #FFF8E7; padding: 20rpx 32rpx; border-bottom: 1rpx solid #FDE8A8; }
.comp-notice-icon { font-size: 28rpx; }
.comp-notice-text { flex: 1; font-size: 26rpx; color: #E67E22; }
.comp-notice-arrow { font-size: 32rpx; color: #E67E22; }

.comp-list { padding: 16rpx 24rpx; }
.comp-card { display: flex; align-items: center; gap: 20rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.comp-avatar { width: 80rpx; height: 80rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 32rpx; font-weight: 700; flex-shrink: 0; }
.comp-card-info { flex: 1; }
.comp-card-name { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.comp-card-level { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.comp-card-days { text-align: center; flex-shrink: 0; }
.comp-days-num { display: block; font-size: 36rpx; font-weight: 700; color: #2D8E69; }
.comp-days-label { display: block; font-size: 18rpx; color: #8E99A4; }

.comp-empty { text-align: center; padding: 100rpx 32rpx; }
.comp-empty-icon { display: block; font-size: 80rpx; margin-bottom: 20rpx; }
.comp-empty-title { display: block; font-size: 30rpx; font-weight: 700; color: #2C3E50; margin-bottom: 12rpx; }
.comp-empty-sub { display: block; font-size: 24rpx; color: #8E99A4; margin-bottom: 40rpx; }
.comp-empty-btn { display: inline-block; padding: 16rpx 48rpx; background: #2D8E69; color: #fff; border-radius: 16rpx; font-size: 28rpx; }
</style>
