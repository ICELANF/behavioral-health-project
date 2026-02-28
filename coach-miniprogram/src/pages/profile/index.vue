<template>
  <view class="pf-page">

    <!-- 用户信息头部 -->
    <view class="pf-hero safe-area-top">
      <view class="pf-hero__bg"></view>
      <view class="pf-hero__info">
        <image
          class="pf-hero__avatar"
          :src="user?.avatar || '/static/default-avatar.png'"
          mode="aspectFill"
        />
        <view class="pf-hero__text">
          <text class="pf-hero__name">{{ user?.full_name || user?.username || '用户' }}</text>
          <view class="pf-hero__badge" :style="{ background: levelColor + '18', color: levelColor }">
            <text>{{ levelLabel }}</text>
          </view>
        </view>
      </view>
    </view>

    <scroll-view scroll-y class="pf-body">

      <!-- 三维积分 -->
      <view class="pf-points">
        <view class="pf-point" v-for="pt in pointCards" :key="pt.key">
          <text class="pf-point__val" :style="{ color: pt.color }">{{ pt.value }}</text>
          <text class="pf-point__label">{{ pt.label }}</text>
        </view>
      </view>

      <!-- 功能菜单 -->
      <view class="pf-menu">
        <view
          v-for="item in menuItems"
          :key="item.key"
          class="pf-menu__item"
          @tap="goTo(item.url)"
        >
          <text class="pf-menu__icon">{{ item.icon }}</text>
          <text class="pf-menu__label">{{ item.label }}</text>
          <text class="pf-menu__arrow">›</text>
        </view>
      </view>

      <!-- 退出登录 -->
      <view class="pf-logout" @tap="handleLogout">
        <text>退出登录</text>
      </view>

      <!-- 版本号 -->
      <text class="pf-version">v1.0.0</text>

    </scroll-view>

    <!-- TabBar 占位 -->
    <view style="height: 120rpx;"></view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import http from '@/api/request'
import { ROLE_COLOR, LEVEL_LABEL, ROLE_LEVEL, formatPoints } from '@/utils/level'

const userStore = useUserStore()
const user = ref<any>(null)

const levelLabel = computed(() => {
  const role = user.value?.role || 'observer'
  const lvl = ROLE_LEVEL[role] ?? 1
  return LEVEL_LABEL[lvl] || '观察者'
})

const levelColor = computed(() => {
  const role = user.value?.role || 'observer'
  return ROLE_COLOR[role] || '#9ca3af'
})

const pointCards = computed(() => [
  { key: 'growth',       label: '成长积分',   value: formatPoints(user.value?.growth_points ?? 0),       color: '#10b981' },
  { key: 'contribution', label: '贡献积分',   value: formatPoints(user.value?.contribution_points ?? 0), color: '#3b82f6' },
  { key: 'influence',    label: '影响力积分', value: formatPoints(user.value?.influence_points ?? 0),    color: '#8b5cf6' },
])

const menuItems = [
  { key: 'learning',   icon: '📚', label: '学习记录',   url: '/pages/learning/my-learning' },
  { key: 'assessment', icon: '📋', label: '我的评估',   url: '/pages/assessment/pending' },
  { key: 'exam',       icon: '📝', label: '考试中心',   url: '/pages/exam/index' },
  { key: 'journey',    icon: '🗺', label: '晋级之路',   url: '/pages/journey/overview' },
  { key: 'cert',       icon: '🏅', label: '我的证书',   url: '/pages/profile-extra/certification' },
  { key: 'rank',       icon: '🏆', label: '排行榜',     url: '/pages/profile-extra/leaderboard' },
  { key: 'settings',   icon: '⚙',  label: '设置',       url: '/pages/profile-extra/settings' },
]

onMounted(async () => {
  await loadProfile()
})

async function loadProfile() {
  try {
    const res = await http.get<any>('/v1/auth/me')
    user.value = res
  } catch {
    // 使用本地缓存
    user.value = userStore.userInfo
  }
}

function goTo(url: string) {
  uni.navigateTo({ url })
}

function handleLogout() {
  uni.showModal({
    title: '退出登录',
    content: '确认退出当前账号？',
    success: (res) => {
      if (!res.confirm) return
      userStore.logout()
    },
  })
}
</script>

<style scoped>
.pf-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 头部 */
.pf-hero {
  position: relative; background: var(--surface); padding: 32rpx 32rpx 40rpx;
  border-bottom: 1px solid var(--border-light);
}
.pf-hero__bg {
  position: absolute; inset: 0; opacity: 0.06;
  background: linear-gradient(135deg, var(--bhp-primary-500), var(--bhp-accent-500));
}
.pf-hero__info { display: flex; align-items: center; gap: 20rpx; position: relative; z-index: 1; }
.pf-hero__avatar { width: 120rpx; height: 120rpx; border-radius: 50%; flex-shrink: 0; background: var(--bhp-gray-100); border: 4rpx solid #fff; }
.pf-hero__text { flex: 1; }
.pf-hero__name { font-size: 36rpx; font-weight: 800; color: var(--text-primary); display: block; }
.pf-hero__badge {
  display: inline-block; font-size: 22rpx; font-weight: 700;
  padding: 4rpx 20rpx; border-radius: var(--radius-full); margin-top: 8rpx;
}

.pf-body { flex: 1; padding: 20rpx 32rpx; }

/* 三维积分 */
.pf-points { display: flex; gap: 16rpx; margin-bottom: 24rpx; }
.pf-point {
  flex: 1; background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx 12rpx; display: flex; flex-direction: column; align-items: center; gap: 6rpx;
  border: 1px solid var(--border-light);
}
.pf-point__val { font-size: 36rpx; font-weight: 800; }
.pf-point__label { font-size: 22rpx; color: var(--text-secondary); }

/* 菜单 */
.pf-menu {
  background: var(--surface); border-radius: var(--radius-lg);
  border: 1px solid var(--border-light); overflow: hidden; margin-bottom: 24rpx;
}
.pf-menu__item {
  display: flex; align-items: center; gap: 16rpx;
  padding: 28rpx 24rpx; border-bottom: 1px solid var(--border-light); cursor: pointer;
}
.pf-menu__item:last-child { border-bottom: none; }
.pf-menu__item:active { background: var(--surface-secondary); }
.pf-menu__icon { font-size: 32rpx; flex-shrink: 0; width: 44rpx; text-align: center; }
.pf-menu__label { flex: 1; font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.pf-menu__arrow { font-size: 32rpx; color: var(--text-tertiary); }

/* 退出 */
.pf-logout {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 28rpx; text-align: center; cursor: pointer;
  border: 1px solid var(--border-light); margin-bottom: 20rpx;
}
.pf-logout text { font-size: 28rpx; font-weight: 600; color: #ef4444; }
.pf-logout:active { background: rgba(239,68,68,0.04); }

/* 版本 */
.pf-version { display: block; text-align: center; font-size: 22rpx; color: var(--text-tertiary); padding: 16rpx 0 40rpx; }
</style>
