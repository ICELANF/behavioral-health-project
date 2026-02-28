/**
 * 用户状态 Store
 * 管理登录态、角色判断、积分、退出等
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/api/auth'

// 角色等级映射
const ROLE_LEVEL: Record<string, number> = {
  observer:   1,
  grower:     2,
  sharer:     3,
  coach:      4,
  promoter:   5,
  supervisor: 5,
  master:     6,
  admin:      99,
}

// 角色颜色
const ROLE_COLOR: Record<string, string> = {
  observer:   '#9ca3af',
  grower:     '#10b981',
  sharer:     '#3b82f6',
  coach:      '#8b5cf6',
  promoter:   '#f59e0b',
  supervisor: '#ec4899',
  master:     '#ef4444',
  admin:      '#111827',
}

// 角色中文标签
const ROLE_LABEL: Record<string, string> = {
  observer:   '观察者',
  grower:     '成长者',
  sharer:     '分享者',
  coach:      '教练',
  promoter:   '促进师',
  supervisor: '督导',
  master:     '大师',
  admin:      '管理员',
}

export const useUserStore = defineStore('user', () => {
  const userInfo    = ref<UserInfo | null>(null)
  const accessToken = ref<string>('')

  // ── Computed ──────────────────────────────────────────
  const isLoggedIn = computed(() => !!accessToken.value && !!userInfo.value)
  const role       = computed(() => userInfo.value?.role?.toLowerCase() || 'observer')
  const roleLevel  = computed(() => ROLE_LEVEL[role.value] ?? 1)
  const roleColor  = computed(() => ROLE_COLOR[role.value]  ?? '#9ca3af')
  const roleLabel  = computed(() => ROLE_LABEL[role.value]  ?? '观察者')

  const displayName = computed(() =>
    userInfo.value?.full_name || userInfo.value?.username || '用户'
  )

  const growthPoints      = computed(() => userInfo.value?.growth_points        ?? 0)
  const contributionPts   = computed(() => userInfo.value?.contribution_points  ?? 0)
  const influencePts      = computed(() => userInfo.value?.influence_points     ?? 0)

  const isCoach      = computed(() => roleLevel.value >= 4)
  const isPromoter   = computed(() => roleLevel.value >= 5)
  const isAdmin      = computed(() => roleLevel.value >= 99)
  const isObserver   = computed(() => role.value === 'observer')

  // ── Actions ───────────────────────────────────────────
  function setAuth(
    tokens: { access_token: string; refresh_token: string },
    user: UserInfo
  ) {
    accessToken.value = tokens.access_token
    userInfo.value    = user
    uni.setStorageSync('access_token',  tokens.access_token)
    uni.setStorageSync('refresh_token', tokens.refresh_token)
    uni.setStorageSync('user_info',     JSON.stringify(user))
  }

  function restoreFromStorage() {
    const token = uni.getStorageSync('access_token')
    const raw   = uni.getStorageSync('user_info')
    if (token && raw) {
      try {
        accessToken.value = token
        userInfo.value    = JSON.parse(raw) as UserInfo
      } catch {
        clearAuth()
      }
    }
  }

  function updateUserInfo(partial: Partial<UserInfo>) {
    if (!userInfo.value) return
    userInfo.value = { ...userInfo.value, ...partial }
    uni.setStorageSync('user_info', JSON.stringify(userInfo.value))
  }

  function addPoints(delta: number) {
    if (!userInfo.value) return
    userInfo.value.growth_points = (userInfo.value.growth_points || 0) + delta
    uni.setStorageSync('user_info', JSON.stringify(userInfo.value))
  }

  async function refreshUserInfo() {
    try {
      const { default: authApi } = await import('@/api/auth')
      const fresh = await authApi.getMe()
      updateUserInfo(fresh)
    } catch {/* ignore */}
  }

  function clearAuth() {
    accessToken.value = ''
    userInfo.value    = null
    uni.removeStorageSync('access_token')
    uni.removeStorageSync('refresh_token')
    uni.removeStorageSync('user_info')
  }

  async function logout() {
    try {
      const { default: authApi } = await import('@/api/auth')
      await authApi.logout()
    } catch {/* ignore */}
    clearAuth()
    uni.reLaunch({ url: '/pages/auth/login' })
  }

  return {
    userInfo,
    accessToken,
    isLoggedIn,
    role,
    roleLevel,
    roleColor,
    roleLabel,
    displayName,
    growthPoints,
    contributionPts,
    influencePts,
    isCoach,
    isPromoter,
    isAdmin,
    isObserver,
    setAuth,
    restoreFromStorage,
    updateUserInfo,
    addPoints,
    refreshUserInfo,
    clearAuth,
    logout,
  }
})
