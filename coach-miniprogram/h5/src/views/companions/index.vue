<template>
  <view class="comp-page">
    <view class="comp-header">
      <text class="comp-title">我的支持网络</text>
      <view class="comp-invite-btn" @tap="goInvite">
        <text>+ 邀请</text>
      </view>
    </view>

    <scroll-view scroll-y class="comp-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 我的教练卡 -->
      <view v-if="myCoach" class="comp-coach-card">
        <view class="comp-coach-avatar" :style="{ background: avatarColor(myCoach.name) }">
          {{ (myCoach.name || '教')[0] }}
        </view>
        <view class="comp-coach-info">
          <text class="comp-coach-name">{{ myCoach.name }}</text>
          <text class="comp-coach-role">🏅 我的教练</text>
        </view>
        <view class="comp-coach-msg-btn" @tap="goMessage">💬 发消息</view>
      </view>

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
import { avatarColor } from '@/utils/studentUtils'

const companions = ref<any[]>([])
const invitationCount = ref(0)
const refreshing = ref(false)
const loading = ref(false)
const myCoach = ref<any>(null)


function levelName(key: string): string {
  return { observer: '观察员', grower: '成长者', sharer: '分享者', coach: '行为健康教练', promoter: '行为健康促进师', supervisor: '行为健康促进师', master: '行为健康大师' }[key] || (key || '成长者')
}

async function loadData() {
  loading.value = true
  // 我的教练
  try {
    const res = await http<any>('/api/v1/companions/my-coach')
    myCoach.value = res?.coach || null
  } catch { myCoach.value = null }
  // 同道者列表
  try {
    const res = await http<any>('/api/v1/companions')
    companions.value = res?.items || []
  } catch { companions.value = [] } finally { loading.value = false }
}

function goMessage() {
  const name = encodeURIComponent(myCoach.value?.name || '')
  const id = myCoach.value?.id || ''
  uni.navigateTo({ url: `/companions/message?coach_name=${name}&coach_id=${id}` })
}

function goInvite() { uni.navigateTo({ url: '/companions/invite' }) }
function goInvitations() { uni.navigateTo({ url: '/companions/invitations' }) }
function goDetail(c: any) { uni.navigateTo({ url: '/companions/detail?id=' + c.id }) }

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

/* 教练卡 */
.comp-coach-card { display: flex; align-items: center; gap: 20rpx; background: linear-gradient(135deg, #EFF6FF 0%, #F0FFF8 100%); margin: 16rpx 24rpx; border-radius: 20rpx; padding: 24rpx; border: 1rpx solid #D1FAE5; }
.comp-coach-avatar { width: 80rpx; height: 80rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 32rpx; font-weight: 700; flex-shrink: 0; }
.comp-coach-info { flex: 1; }
.comp-coach-name { display: block; font-size: 30rpx; font-weight: 700; color: #2C3E50; }
.comp-coach-role { display: block; font-size: 22rpx; color: #2D8E69; margin-top: 4rpx; }
.comp-coach-msg-btn { padding: 12rpx 24rpx; background: #2D8E69; color: #fff; border-radius: 10rpx; font-size: 24rpx; white-space: nowrap; }

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
