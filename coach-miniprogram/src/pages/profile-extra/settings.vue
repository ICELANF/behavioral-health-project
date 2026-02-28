<template>
  <view class="st-page">

    <view class="st-navbar safe-area-top">
      <view class="st-navbar__back" @tap="goBack"><text class="st-navbar__arrow">‹</text></view>
      <text class="st-navbar__title">设置</text>
      <view class="st-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="st-body">

      <!-- 账号安全 -->
      <view class="st-section">
        <text class="st-section__title">账号安全</text>
        <view class="st-cell" @tap="goChangePwd">
          <text class="st-cell__label">修改密码</text>
          <text class="st-cell__arrow">›</text>
        </view>
        <view class="st-cell">
          <text class="st-cell__label">绑定手机</text>
          <text class="st-cell__val">{{ maskedPhone }}</text>
          <text class="st-cell__arrow">›</text>
        </view>
      </view>

      <!-- 通知设置 -->
      <view class="st-section">
        <text class="st-section__title">通知设置</text>
        <view class="st-cell">
          <text class="st-cell__label">学习提醒</text>
          <switch :checked="notify.learning" @change="notify.learning = $event.detail.value" color="var(--bhp-primary-500)" />
        </view>
        <view class="st-cell">
          <text class="st-cell__label">教练消息</text>
          <switch :checked="notify.coach" @change="notify.coach = $event.detail.value" color="var(--bhp-primary-500)" />
        </view>
        <view class="st-cell">
          <text class="st-cell__label">系统通知</text>
          <switch :checked="notify.system" @change="notify.system = $event.detail.value" color="var(--bhp-primary-500)" />
        </view>
      </view>

      <!-- 隐私设置 -->
      <view class="st-section">
        <text class="st-section__title">隐私设置</text>
        <view class="st-cell">
          <text class="st-cell__label">数据共享给教练</text>
          <switch :checked="privacy.shareData" @change="privacy.shareData = $event.detail.value" color="var(--bhp-primary-500)" />
        </view>
      </view>

      <!-- 关于 -->
      <view class="st-section">
        <text class="st-section__title">关于</text>
        <view class="st-cell">
          <text class="st-cell__label">版本号</text>
          <text class="st-cell__val">v1.0.0</text>
        </view>
        <view class="st-cell">
          <text class="st-cell__label">用户服务协议</text>
          <text class="st-cell__arrow">›</text>
        </view>
        <view class="st-cell">
          <text class="st-cell__label">隐私政策</text>
          <text class="st-cell__arrow">›</text>
        </view>
      </view>

      <!-- 退出登录 -->
      <view class="st-logout" @tap="handleLogout">
        <text>退出登录</text>
      </view>

      <!-- 存储清理 -->
      <view class="st-cache">
        <text class="text-sm text-secondary-color" @tap="clearCache">清除缓存</text>
      </view>

    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { reactive, computed } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const notify = reactive({ learning: true, coach: true, system: true })
const privacy = reactive({ shareData: true })

const maskedPhone = computed(() => {
  const phone = userStore.userInfo?.phone || ''
  if (phone.length >= 11) return phone.slice(0, 3) + '****' + phone.slice(7)
  return '未绑定'
})

function goChangePwd() {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

function handleLogout() {
  uni.showModal({
    title: '确认退出',
    content: '确定要退出登录吗？',
    success(res) {
      if (res.confirm) {
        userStore.logout()
        uni.reLaunch({ url: '/pages/auth/login' })
      }
    },
  })
}

function clearCache() {
  uni.showModal({
    title: '清除缓存',
    content: '将清除本地缓存数据，不影响账号信息',
    success(res) {
      if (res.confirm) {
        try { uni.clearStorageSync() } catch { /* ignore */ }
        uni.showToast({ title: '缓存已清除', icon: 'success' })
      }
    },
  })
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.st-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.st-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.st-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.st-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.st-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.st-navbar__placeholder { width: 64rpx; }

.st-body { flex: 1; padding: 20rpx 0 40rpx; }

.st-section {
  background: var(--surface); margin-bottom: 20rpx;
  border-top: 1px solid var(--border-light); border-bottom: 1px solid var(--border-light);
}
.st-section__title {
  display: block; font-size: 24rpx; font-weight: 600; color: var(--text-tertiary);
  padding: 20rpx 32rpx 8rpx; text-transform: uppercase;
}

.st-cell {
  display: flex; align-items: center; padding: 24rpx 32rpx;
  border-bottom: 1px solid var(--border-light); cursor: pointer;
}
.st-cell:last-child { border-bottom: none; }
.st-cell__label { flex: 1; font-size: 28rpx; color: var(--text-primary); }
.st-cell__val { font-size: 26rpx; color: var(--text-tertiary); margin-right: 8rpx; }
.st-cell__arrow { font-size: 32rpx; color: var(--text-tertiary); }

.st-logout {
  margin: 32rpx 32rpx 0; padding: 24rpx; text-align: center;
  background: var(--surface); border-radius: var(--radius-lg);
  border: 1px solid var(--border-light); cursor: pointer;
  font-size: 28rpx; font-weight: 600; color: #ef4444;
}
.st-logout:active { background: rgba(239,68,68,0.04); }

.st-cache { text-align: center; padding: 24rpx; cursor: pointer; }
</style>
