<!--
  BHPTabBar — 自定义底部导航栏
  在需要自定义 Tab 样式时使用（小程序原生 tabBar 的补充）
  用法: <BHPTabBar :active="current" @change="handleChange" />
-->
<template>
  <view class="bhp-tabbar safe-area-bottom">
    <view
      v-for="item in TABS"
      :key="item.key"
      class="bhp-tabbar__item"
      :class="{ 'bhp-tabbar__item--active': active === item.key }"
      @tap="$emit('change', item.key)"
    >
      <text class="bhp-tabbar__icon">{{ active === item.key ? item.iconActive : item.icon }}</text>
      <text class="bhp-tabbar__label">{{ item.label }}</text>
      <!-- 红点 -->
      <view class="bhp-tabbar__badge" v-if="getBadge(item.key)">
        <text>{{ getBadge(item.key) }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  active:  string
  badges?: Record<string, number>   // { notifications: 3 }
}>(), {
  badges: () => ({}),
})

defineEmits<{ (e: 'change', key: string): void }>()

const TABS = [
  { key: 'home',          label: '首页', icon: '🏠',  iconActive: '🏡'  },
  { key: 'notifications', label: '消息', icon: '🔔',  iconActive: '🔔'  },
  { key: 'profile',       label: '我的', icon: '👤',  iconActive: '👤'  },
]

function getBadge(key: string): number | '' {
  const v = props.badges?.[key] ?? 0
  return v > 0 ? (v > 99 ? 99 : v) : ''
}
</script>

<style scoped>
.bhp-tabbar {
  display: flex;
  background: var(--surface);
  border-top: 1px solid var(--border-light);
  padding-top: 12rpx;
  position: fixed; bottom: 0; left: 0; right: 0;
  z-index: 100;
}
.bhp-tabbar__item {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; gap: 4rpx;
  padding: 4rpx 0; cursor: pointer; position: relative;
}
.bhp-tabbar__icon  { font-size: 40rpx; line-height: 1; }
.bhp-tabbar__label {
  font-size: 20rpx; color: var(--text-tertiary);
  transition: color 0.15s;
}
.bhp-tabbar__item--active .bhp-tabbar__label {
  color: var(--bhp-primary-500); font-weight: 600;
}
.bhp-tabbar__badge {
  position: absolute; top: -4rpx; right: calc(50% - 36rpx);
  background: #ff4d4f; color: #fff;
  font-size: 16rpx; min-width: 28rpx; height: 28rpx;
  border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  padding: 0 6rpx;
}
</style>
