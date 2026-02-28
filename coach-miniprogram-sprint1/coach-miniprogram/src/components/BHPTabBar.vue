<template>
  <!--
    双模式 TabBar
    学习者 (L0-L2): 首页 / 学习 / 路径 / 同道者 / 我的
    教练   (L3+):  工作台 / 学员 / 学习 / 消息 / 我的
  -->
  <view class="tabbar" :style="{ paddingBottom: safeBottom + 'px' }">
    <view
      v-for="tab in currentTabs"
      :key="tab.key"
      class="tabbar__item"
      :class="{ 'tabbar__item--active': current === tab.key }"
      @tap="switchTab(tab)"
    >
      <!-- 图标 -->
      <view class="tabbar__icon-wrap">
        <text class="tabbar__emoji">{{ current === tab.key ? tab.activeIcon : tab.icon }}</text>
        <!-- 红点角标 -->
        <view class="tabbar__badge" v-if="tab.badge && tab.badge > 0">
          <text class="tabbar__badge-text">{{ tab.badge > 99 ? '99+' : tab.badge }}</text>
        </view>
      </view>
      <text class="tabbar__label">{{ tab.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { useCoachStore } from '@/stores/coach'
import { getSafeAreaBottom } from '@/utils/wechat'

const props = defineProps<{ current: string }>()
const emit  = defineEmits<{ change: [key: string] }>()

const userStore  = useUserStore()
const coachStore = useCoachStore()
const safeBottom = getSafeAreaBottom()

interface TabItem {
  key:        string
  label:      string
  icon:       string
  activeIcon: string
  path:       string
  badge?:     number
}

// 学习者 Tab（L0-L2）
const learnerTabs = computed<TabItem[]>(() => [
  { key: 'home',       label: '首页',   icon: '🏠', activeIcon: '🏡', path: '/pages/home/index' },
  { key: 'learning',   label: '学习',   icon: '📖', activeIcon: '📚', path: '/pages/learning/index' },
  { key: 'journey',    label: '路径',   icon: '🗺', activeIcon: '🌟', path: '/pages/journey/overview' },
  { key: 'companions', label: '同道者', icon: '👥', activeIcon: '💫', path: '/pages/companions/index' },
  { key: 'profile',    label: '我的',   icon: '👤', activeIcon: '😊', path: '/pages/profile/index' }
])

// 教练 Tab（L3+）
const coachTabs = computed<TabItem[]>(() => [
  { key: 'dashboard',  label: '工作台', icon: '🖥', activeIcon: '💻', path: '/pages/coach/dashboard' },
  { key: 'students',   label: '学员',   icon: '👥', activeIcon: '🧑‍🤝‍🧑', path: '/pages/coach/students/index' },
  { key: 'learning',   label: '学习',   icon: '📖', activeIcon: '📚', path: '/pages/learning/index' },
  {
    key: 'messages',
    label: '消息',
    icon: '💬', activeIcon: '📩',
    path: '/pages/notifications/index',
    badge: coachStore.badgeCount
  },
  { key: 'profile',    label: '我的',   icon: '👤', activeIcon: '😊', path: '/pages/profile/index' }
])

const currentTabs = computed(() => userStore.isCoach ? coachTabs.value : learnerTabs.value)

function switchTab(tab: TabItem) {
  if (tab.key === props.current) return
  emit('change', tab.key)
  uni.switchTab({ url: tab.path })
}
</script>

<style scoped>
.tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: flex-end;
  background: var(--surface);
  border-top: 1px solid var(--border-light);
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.06);
  z-index: var(--z-sticky);
}

.tabbar__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 4px 8px;
  cursor: pointer;
  transition: opacity var(--duration-fast);
  -webkit-tap-highlight-color: transparent;
}
.tabbar__item:active { opacity: 0.7; }

.tabbar__icon-wrap {
  position: relative;
  margin-bottom: 4px;
}

.tabbar__emoji { font-size: 44rpx; line-height: 1; }

.tabbar__badge {
  position: absolute;
  top: -6px;
  right: -10px;
  min-width: 18px;
  height: 18px;
  background: #ef4444;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  border: 1.5px solid #fff;
}
.tabbar__badge-text {
  font-size: 18rpx;
  color: #fff;
  font-weight: 700;
  line-height: 1;
}

.tabbar__label {
  font-size: 20rpx;
  color: var(--bhp-gray-400);
  transition: color var(--duration-fast);
}

.tabbar__item--active .tabbar__label {
  color: var(--bhp-primary-500);
  font-weight: 600;
}
</style>
