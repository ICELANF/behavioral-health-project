<template>
  <view class="set-page">
    <scroll-view scroll-y class="set-scroll">
      <!-- 账号信息 -->
      <view class="set-group">
        <view class="set-group-title">账号信息</view>
        <view class="set-item">
          <text class="set-item-label">用户名</text>
          <text class="set-item-value">{{ userInfo.username || '—' }}</text>
        </view>
        <view class="set-item">
          <text class="set-item-label">姓名</text>
          <text class="set-item-value">{{ userInfo.name || '—' }}</text>
        </view>
        <view class="set-item">
          <text class="set-item-label">角色</text>
          <text class="set-item-value">{{ userInfo.role_label || '行为健康教练' }}</text>
        </view>
      </view>

      <!-- 通知设置 -->
      <view class="set-group">
        <view class="set-group-title">通知设置</view>
        <view class="set-item">
          <text class="set-item-label">系统通知</text>
          <switch :checked="notifySystem" @change="(e: any) => notifySystem = e.detail.value" color="#2D8E69" />
        </view>
        <view class="set-item">
          <text class="set-item-label">评估提醒</text>
          <switch :checked="notifyAssess" @change="(e: any) => notifyAssess = e.detail.value" color="#2D8E69" />
        </view>
        <view class="set-item">
          <text class="set-item-label">学习提醒</text>
          <switch :checked="notifyLearn" @change="(e: any) => notifyLearn = e.detail.value" color="#2D8E69" />
        </view>
      </view>

      <!-- 其他 -->
      <view class="set-group">
        <view class="set-group-title">其他</view>
        <view class="set-item set-item--tap" @tap="clearCache">
          <text class="set-item-label">清除缓存</text>
          <text class="set-item-arrow">›</text>
        </view>
        <view class="set-item set-item--tap" @tap="showAbout">
          <text class="set-item-label">关于平台</text>
          <text class="set-item-arrow">›</text>
        </view>
      </view>

      <view class="set-logout-btn" @tap="doLogout">
        <text>退出登录</text>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const userInfo = ref<any>({})
const notifySystem = ref(true)
const notifyAssess = ref(true)
const notifyLearn = ref(true)

onMounted(() => {
  try {
    const stored = uni.getStorageSync('user_info')
    if (stored) {
      const u = typeof stored === 'string' ? JSON.parse(stored) : stored
      userInfo.value = {
        username: u.username || '',
        name: u.full_name || u.display_name || u.username || '教练',
        role_label: ({ coach:'行为健康教练', promoter:'行为健康促进师', supervisor:'行为健康促进师', master:'行为健康大师', admin:'管理员', sharer:'分享者', grower:'成长者', observer:'观察员' } as Record<string,string>)[(u.role||'').toLowerCase()] || u.role || '用户'
      }
    }
  } catch (e) { console.warn('[profile-extra/settings] operation:', e) }
})

function clearCache() {
  uni.showModal({
    title: '清除缓存',
    content: '将清除本地缓存数据，不影响账号信息',
    success: (res) => {
      if (res.confirm) {
        uni.clearStorageSync()
        uni.showToast({ title: '缓存已清除', icon: 'success' })
      }
    }
  })
}

function showAbout() {
  uni.showModal({ title: '关于', content: '行健平台 v5.0\n行为健康促进与慢病逆转\n\n© 2026 BehaviorOS', showCancel: false })
}

function doLogout() {
  uni.showModal({
    title: '确认退出',
    content: '退出后需要重新登录',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('access_token')
        uni.removeStorageSync('user_info')
        uni.reLaunch({ url: '/auth/login' })
      }
    }
  })
}
</script>

<style scoped>
.set-page { min-height: 100vh; background: #F5F6FA; }
.set-scroll { height: 100vh; }
.set-group { background: #fff; margin: 16rpx 24rpx; border-radius: 16rpx; overflow: hidden; }
.set-group-title { font-size: 22rpx; color: #8E99A4; padding: 16rpx 24rpx 8rpx; text-transform: uppercase; }
.set-item { display: flex; justify-content: space-between; align-items: center; padding: 20rpx 24rpx; border-bottom: 1rpx solid #F8F8F8; }
.set-item:last-child { border-bottom: none; }
.set-item--tap:active { background: #F8F8F8; }
.set-item-label { font-size: 28rpx; color: #2C3E50; }
.set-item-value { font-size: 26rpx; color: #8E99A4; }
.set-item-arrow { font-size: 32rpx; color: #CCC; }
.set-logout-btn { margin: 24rpx; background: #FDEDEC; border-radius: 16rpx; padding: 24rpx; text-align: center; color: #E74C3C; font-size: 30rpx; font-weight: 600; }
</style>
