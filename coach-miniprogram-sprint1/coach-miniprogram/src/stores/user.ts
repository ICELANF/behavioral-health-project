/**
 * User Store — 用户状态管理
 * 包含: 用户信息 / 角色判断 / 积分 / 登录态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tokenStorage } from '@/api/request'
import authApi, { type UserInfo } from '@/api/auth'

// ─── 角色枚举（与后端 UserRole 对齐）────────────────────────
export const ROLES = {
  OBSERVER:   'observer',
  GROWER:     'grower',
  SHARER:     'sharer',
  COACH:      'coach',
  PROMOTER:   'promoter',
  SUPERVISOR: 'supervisor',
  MASTER:     'master',
  ADMIN:      'admin'
} as const

export type UserRole = typeof ROLES[keyof typeof ROLES]

// ─── 角色等级映射（与后端 ROLE_LEVEL 对齐）──────────────────
export const ROLE_LEVEL_MAP: Record<UserRole, number> = {
  observer:   1,
  grower:     2,
  sharer:     3,
  coach:      4,
  promoter:   5,
  supervisor: 5,
  master:     6,
  admin:      99
}

// ─── 六级颜色（与 Design System --level-* 变量对齐）─────────
export const ROLE_COLOR_MAP: Record<string, string> = {
  observer:   '#8c8c8c',
  grower:     '#52c41a',
  sharer:     '#1890ff',
  coach:      '#722ed1',
  promoter:   '#eb2f96',
  supervisor: '#eb2f96',
  master:     '#faad14',
  admin:      '#f5222d'
}

// ─── 角色中文名 ──────────────────────────────────────────────
export const ROLE_LABEL_MAP: Record<string, string> = {
  observer:   'L0 观察员',
  grower:     'L1 成长者',
  sharer:     'L2 分享者',
  coach:      'L3 教练',
  promoter:   'L4 促进师',
  supervisor: 'L4 督导专家',
  master:     'L5 大师',
  admin:      '管理员'
}

// ─── Store ───────────────────────────────────────────────────
export const useUserStore = defineStore('user', () => {
  // State
  const userInfo = ref<UserInfo | null>(null)
  const isLoggedIn = ref(false)
  const loading = ref(false)

  // Computed
  const role = computed(() => userInfo.value?.role as UserRole || 'observer')
  const roleLevel = computed(() => ROLE_LEVEL_MAP[role.value] || 1)
  const roleColor = computed(() => ROLE_COLOR_MAP[role.value] || '#8c8c8c')
  const roleLabel = computed(() => ROLE_LABEL_MAP[role.value] || '观察员')

  /** 是否是教练及以上（L3+），决定展示工作台视图 */
  const isCoach = computed(() => roleLevel.value >= 4)

  /** 是否是管理员 */
  const isAdmin = computed(() => roleLevel.value >= 99)

  /** 成长积分（首页展示用） */
  const growthPoints   = computed(() => userInfo.value?.growth_points || 0)
  const contributionPts = computed(() => userInfo.value?.contribution_points || 0)
  const influencePts   = computed(() => userInfo.value?.influence_points || 0)

  /** 用户显示名（优先 full_name，其次 username） */
  const displayName = computed(() =>
    userInfo.value?.full_name || userInfo.value?.username || '用户'
  )

  // Actions

  /** 登录成功后设置状态 */
  function setAuth(tokens: { access_token: string; refresh_token: string }, user: UserInfo) {
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
    userInfo.value = user
    isLoggedIn.value = true
    uni.setStorageSync('bhp_user_info', JSON.stringify(user))
  }

  /** App 启动时从本地恢复状态 */
  function restoreFromStorage() {
    const token = tokenStorage.getAccess()
    const stored = uni.getStorageSync('bhp_user_info')
    if (token && stored) {
      try {
        userInfo.value = JSON.parse(stored)
        isLoggedIn.value = true
      } catch { /* 解析失败，清除 */ }
    }
  }

  /** 从服务端刷新用户信息（积分/级别可能变化） */
  async function refreshUserInfo() {
    if (!isLoggedIn.value) return
    try {
      const fresh = await authApi.getMe()
      userInfo.value = fresh
      uni.setStorageSync('bhp_user_info', JSON.stringify(fresh))
    } catch { /* 静默失败 */ }
  }

  /** 退出登录 */
  async function logout() {
    try {
      await authApi.logout()
    } catch { /* 忽略 */ }
    tokenStorage.clear()
    userInfo.value = null
    isLoggedIn.value = false
    uni.reLaunch({ url: '/pages/auth/login' })
  }

  /** 更新本地积分（完成任务后即时刷新，不请求接口） */
  function addPoints(growth = 0, contribution = 0, influence = 0) {
    if (!userInfo.value) return
    userInfo.value.growth_points        = (userInfo.value.growth_points || 0) + growth
    userInfo.value.contribution_points  = (userInfo.value.contribution_points || 0) + contribution
    userInfo.value.influence_points     = (userInfo.value.influence_points || 0) + influence
  }

  return {
    // state
    userInfo, isLoggedIn, loading,
    // computed
    role, roleLevel, roleColor, roleLabel,
    isCoach, isAdmin,
    growthPoints, contributionPts, influencePts, displayName,
    // actions
    setAuth, restoreFromStorage, refreshUserInfo, logout, addPoints
  }
})
