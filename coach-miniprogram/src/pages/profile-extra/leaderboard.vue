<template>
  <view class="page-placeholder">
    <view class="page-placeholder__icon">
      <text>🏅</text>
    </view>
    <text class="page-placeholder__title">积分排行榜</text>
    <text class="page-placeholder__sub">页面开发中</text>
    <view class="page-placeholder__back" @tap="goBack">
      <text class="text-sm text-primary-color">返回</text>
    </view>
  </view>
</template>

<script setup lang="ts">
function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.page-placeholder {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 100vh; background: var(--surface-secondary); gap: 20rpx;
}
.page-placeholder__icon { font-size: 80rpx; }
.page-placeholder__title { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }
.page-placeholder__sub { font-size: 26rpx; color: var(--text-secondary); }
.page-placeholder__back { margin-top: 40rpx; padding: 16rpx 48rpx; border-radius: var(--radius-full); border: 1px solid var(--bhp-primary-500); }
</style>
