<template>
  <view class="profile-page">

    <!-- 英雄卡 -->
    <view class="profile-hero" :style="{ background: heroGradient }">
      <!-- 头像 -->
      <view class="profile-hero__avatar">
        <image
          v-if="userStore.userInfo?.avatar_url"
          :src="userStore.userInfo.avatar_url"
          class="profile-hero__avatar-img"
          mode="aspectFill"
        />
        <text v-else class="profile-hero__avatar-text">{{ displayInitial }}</text>
      </view>

      <!-- 姓名 + 角色 -->
      <view class="profile-hero__info">
        <text class="profile-hero__name">{{ userStore.displayName }}</text>
        <view class="profile-hero__role-badge">
          <text class="profile-hero__role-text">{{ userStore.roleLabel }}</text>
        </view>
        <text class="profile-hero__since">加入于 {{ joinedDate }}</text>
      </view>
    </view>

    <!-- 三维积分 -->
    <view class="profile-points px-4">
      <view class="profile-points__card bhp-card bhp-card--flat">
        <view class="profile-points__item">
          <text class="profile-points__val">{{ userStore.growthPoints }}</text>
          <text class="profile-points__label">成长积分</text>
        </view>
        <view class="profile-points__divider"></view>
        <view class="profile-points__item">
          <text class="profile-points__val">{{ userStore.contributionPts }}</text>
          <text class="profile-points__label">贡献积分</text>
        </view>
        <view class="profile-points__divider"></view>
        <view class="profile-points__item">
          <text class="profile-points__val">{{ userStore.influencePts }}</text>
          <text class="profile-points__label">影响积分</text>
        </view>
      </view>
    </view>

    <!-- 等级进度 -->
    <view class="profile-level px-4" v-if="nextLevelThreshold > 0">
      <view class="profile-level__card bhp-card bhp-card--flat">
        <view class="profile-level__header">
          <text class="profile-level__title">{{ levelProgressText }}</text>
          <text class="profile-level__pct text-xs text-primary-color">{{ levelPct }}%</text>
        </view>
        <view class="profile-level__bar">
          <view class="profile-level__bar-fill" :style="{ width: levelPct + '%', background: userStore.roleColor }"></view>
        </view>
        <text class="profile-level__hint text-xs text-tertiary-color">
          还需 {{ nextLevelThreshold - userStore.growthPoints }} 成长积分升级
        </text>
      </view>
    </view>

    <!-- 功能入口九宫格 -->
    <view class="profile-grid px-4">
      <view
        v-for="item in gridMenu"
        :key="item.key"
        class="profile-grid__item"
        @tap="item.action"
      >
        <view class="profile-grid__icon" :style="{ background: item.color + '15' }">
          <text class="profile-grid__icon-text" :style="{ color: item.color }">{{ item.icon }}</text>
        </view>
        <text class="profile-grid__label">{{ item.label }}</text>
      </view>
    </view>

    <!-- 账号设置列表 -->
    <view class="profile-menu px-4">
      <view class="profile-menu__card bhp-card bhp-card--flat">
        <view
          v-for="item in listMenu"
          :key="item.key"
          class="profile-menu__item"
          @tap="item.action"
        >
          <view class="profile-menu__left">
            <text class="profile-menu__icon">{{ item.icon }}</text>
            <text class="profile-menu__label">{{ item.label }}</text>
          </view>
          <text class="profile-menu__arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 退出登录 -->
    <view class="profile-logout px-4">
      <view class="profile-logout__btn" @tap="handleLogout">
        <text>退出登录</text>
      </view>
    </view>

    <!-- 版本信息 -->
    <view class="profile-version">
      <text class="text-xs text-tertiary-color">行健平台 v1.0.0 · Sprint 2</text>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// ─── 等级门控常量（与 backend paths_api._LEVEL_THRESHOLDS 对齐）
const NEXT_THRESHOLDS: Record<number, number> = {
  1: 100,    // L0 → L1
  2: 500,    // L1 → L2
  3: 800,    // L2 → L3
  4: 1500,   // L3 → L4
  5: 3000,   // L4 → L5
  6: 0       // L5 已满级
}
const PREV_THRESHOLDS: Record<number, number> = {
  1: 0, 2: 100, 3: 500, 4: 800, 5: 1500, 6: 3000
}

// ─── 计算属性 ──────────────────────────────────────────────────

const displayInitial = computed(() =>
  (userStore.userInfo?.full_name || userStore.userInfo?.username || '用')[0]
)

const heroGradient = computed(() => {
  const c = userStore.roleColor
  return `linear-gradient(135deg, ${c}dd, ${c}88)`
})

const joinedDate = computed(() => {
  const d = userStore.userInfo?.created_at
  if (!d) return '—'
  try {
    const dt = new Date(d)
    return `${dt.getFullYear()}.${String(dt.getMonth() + 1).padStart(2, '0')}`
  } catch { return '—' }
})

const nextLevelThreshold = computed(() => NEXT_THRESHOLDS[userStore.roleLevel] ?? 0)
const prevLevelThreshold = computed(() => PREV_THRESHOLDS[userStore.roleLevel] ?? 0)

const levelPct = computed(() => {
  const next = nextLevelThreshold.value
  if (!next) return 100
  const prev = prevLevelThreshold.value
  const range = next - prev
  const progress = Math.max(0, userStore.growthPoints - prev)
  return Math.min(Math.round((progress / range) * 100), 100)
})

const levelProgressText = computed(() => {
  if (userStore.roleLevel >= 6) return '已达最高等级 L5 大师'
  const labels: Record<number, string> = {
    1: '成长至 L1 成长者', 2: '成长至 L2 分享者',
    3: '成长至 L3 教练', 4: '成长至 L4 促进师',
    5: '成长至 L5 大师'
  }
  return labels[userStore.roleLevel] || '持续成长'
})

// ─── 九宫格菜单 ───────────────────────────────────────────────
const gridMenu = [
  {
    key: 'journey', icon: '🗺️', label: '成长路径', color: '#722ed1',
    action: () => uni.navigateTo({ url: '/pages/journey/overview' })
  },
  {
    key: 'exam', icon: '📝', label: '认证考试', color: '#1890ff',
    action: () => uni.navigateTo({ url: '/pages/exam/index' })
  },
  {
    key: 'certification', icon: '🏅', label: '我的认证', color: '#faad14',
    action: () => uni.navigateTo({ url: '/pages/profile/certification' })
  },
  {
    key: 'performance', icon: '📊', label: '我的绩效', color: '#52c41a',
    action: () => uni.navigateTo({ url: '/pages/profile/performance' })
  },
  {
    key: 'credits', icon: '🎓', label: '学分中心', color: '#eb2f96',
    action: () => uni.navigateTo({ url: '/pages/learning/credits' })
  },
  {
    key: 'companions', icon: '🤝', label: '我的同道', color: '#722ed1',
    action: () => uni.navigateTo({ url: '/pages/companions/index' })
  },
  {
    key: 'leaderboard', icon: '🏆', label: '排行榜', color: '#fa8c16',
    action: () => uni.navigateTo({ url: '/pages/profile/leaderboard' })
  },
  {
    key: 'my-learning', icon: '📚', label: '学习记录', color: '#1890ff',
    action: () => uni.navigateTo({ url: '/pages/learning/my-learning' })
  },
  {
    key: 'promotion', icon: '⬆️', label: '晋级申请', color: '#52c41a',
    action: () => uni.navigateTo({ url: '/pages/journey/promotion' })
  },
]

// ─── 列表菜单 ─────────────────────────────────────────────────
const listMenu = [
  {
    key: 'settings', icon: '⚙️', label: '账号设置',
    action: () => uni.navigateTo({ url: '/pages/profile/settings' })
  },
  {
    key: 'help', icon: '💬', label: '帮助与反馈',
    action: () => uni.showToast({ title: '请联系管理员', icon: 'none' })
  },
  {
    key: 'about', icon: 'ℹ️', label: '关于平台',
    action: () => uni.showToast({ title: '行健平台 v1.0.0', icon: 'none' })
  },
]

// ─── 退出登录 ─────────────────────────────────────────────────
function handleLogout() {
  uni.showModal({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    confirmText: '退出',
    confirmColor: '#ef4444',
    success: async (res) => {
      if (res.confirm) {
        await userStore.logout()
      }
    }
  })
}
</script>

<style scoped>
.profile-page { background: var(--surface-secondary); min-height: 100vh; }

/* 英雄卡 */
.profile-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 32rpx 40rpx;
  gap: 16rpx;
}
.profile-hero__avatar {
  width: 120rpx; height: 120rpx;
  border-radius: 50%;
  background: rgba(255,255,255,0.3);
  display: flex; align-items: center; justify-content: center;
  border: 4rpx solid rgba(255,255,255,0.6);
  overflow: hidden;
}
.profile-hero__avatar-img { width: 100%; height: 100%; }
.profile-hero__avatar-text { font-size: 52rpx; color: #fff; font-weight: 700; }

.profile-hero__info { display: flex; flex-direction: column; align-items: center; gap: 10rpx; }
.profile-hero__name { font-size: 38rpx; font-weight: 700; color: #fff; }
.profile-hero__role-badge {
  background: rgba(255,255,255,0.25);
  border-radius: var(--radius-full);
  padding: 6rpx 20rpx;
}
.profile-hero__role-text { font-size: 24rpx; color: #fff; font-weight: 600; }
.profile-hero__since { font-size: 22rpx; color: rgba(255,255,255,0.75); }

/* 三维积分 */
.profile-points { margin-top: -20rpx; }
.profile-points__card {
  display: flex;
  align-items: center;
  padding: 24rpx 16rpx;
}
.profile-points__item {
  flex: 1;
  display: flex; flex-direction: column; align-items: center; gap: 6rpx;
}
.profile-points__val { font-size: 36rpx; font-weight: 700; color: var(--text-primary); }
.profile-points__label { font-size: 22rpx; color: var(--text-tertiary); }
.profile-points__divider {
  width: 1px; height: 48rpx;
  background: var(--border-light);
}

/* 等级进度 */
.profile-level { padding-top: 12rpx; }
.profile-level__card { padding: 20rpx 24rpx; }
.profile-level__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.profile-level__title { font-size: 24rpx; font-weight: 600; color: var(--text-primary); }
.profile-level__pct { font-weight: 700; }
.profile-level__bar {
  height: 10rpx;
  background: var(--bhp-gray-100);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: 10rpx;
}
.profile-level__bar-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.4s ease;
}
.profile-level__hint { display: block; }

/* 九宫格 */
.profile-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
  padding-top: 16rpx;
}
.profile-grid__item {
  background: var(--surface);
  border-radius: var(--radius-lg);
  display: flex; flex-direction: column; align-items: center;
  padding: 20rpx 8rpx;
  gap: 12rpx;
  cursor: pointer;
  border: 1px solid var(--border-light);
}
.profile-grid__item:active { opacity: 0.75; transform: scale(0.97); }
.profile-grid__icon {
  width: 72rpx; height: 72rpx;
  border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
}
.profile-grid__icon-text { font-size: 34rpx; }
.profile-grid__label { font-size: 22rpx; color: var(--text-primary); font-weight: 500; text-align: center; }

/* 列表菜单 */
.profile-menu { padding-top: 16rpx; }
.profile-menu__card { overflow: hidden; }
.profile-menu__item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 28rpx 24rpx;
  cursor: pointer;
  border-bottom: 1px solid var(--border-light);
}
.profile-menu__item:last-child { border-bottom: none; }
.profile-menu__item:active { background: var(--surface-secondary); }
.profile-menu__left { display: flex; align-items: center; gap: 16rpx; }
.profile-menu__icon { font-size: 30rpx; }
.profile-menu__label { font-size: 28rpx; color: var(--text-primary); }
.profile-menu__arrow { font-size: 32rpx; color: var(--text-tertiary); }

/* 退出 */
.profile-logout { padding-top: 24rpx; }
.profile-logout__btn {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 28rpx;
  text-align: center;
  font-size: 28rpx;
  color: var(--bhp-error-500, #ef4444);
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border-light);
}
.profile-logout__btn:active { opacity: 0.75; }

/* 版本 */
.profile-version {
  padding: 24rpx 0;
  text-align: center;
}
</style>
