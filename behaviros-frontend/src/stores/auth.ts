/**
 * 认证 Store — 用户登录状态、角色权限、Token 管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { segmentsApi } from '@/api'
import { getToken, setToken, removeToken, getStoredUser, setStoredUser } from '@/api/http'
import { UserRole, ROLE_LEVEL, type User, type UserPermissions, type LoginRequest, type RegisterRequest } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // =====================================================================
  // 状态
  // =====================================================================

  const user = ref<User | null>(getStoredUser())
  const permissions = ref<UserPermissions | null>(null)
  const loading = ref(false)
  const initialized = ref(false)

  // =====================================================================
  // 计算属性
  // =====================================================================

  const isLoggedIn = computed(() => !!user.value && !!getToken())
  const role = computed(() => user.value?.role || UserRole.OBSERVER)
  const roleLevel = computed(() => ROLE_LEVEL[role.value] || 0)
  const isAdmin = computed(() => role.value === UserRole.ADMIN)
  const isCoachOrAbove = computed(() => roleLevel.value >= ROLE_LEVEL[UserRole.COACH])
  const displayName = computed(() => user.value?.display_name || user.value?.username || '用户')

  // =====================================================================
  // 方法
  // =====================================================================

  function hasRole(minRole: UserRole): boolean {
    return roleLevel.value >= (ROLE_LEVEL[minRole] || 0)
  }

  async function login(data: LoginRequest) {
    loading.value = true
    try {
      const res = await authApi.login(data)
      setToken(res.access_token)
      user.value = res.user
      setStoredUser(res.user)
      await fetchPermissions()
      return res
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterRequest) {
    loading.value = true
    try {
      const res = await authApi.register(data)
      setToken(res.access_token)
      user.value = res.user
      setStoredUser(res.user)
      await fetchPermissions()
      return res
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!getToken()) return
    try {
      const me = await authApi.getMe()
      user.value = me
      setStoredUser(me)
    } catch {
      logout()
    }
  }

  async function fetchPermissions() {
    if (!getToken()) return
    try {
      permissions.value = await segmentsApi.getPermissions()
    } catch {
      // permissions fetch optional, don't logout
    }
  }

  async function initialize() {
    if (initialized.value) return
    if (getToken()) {
      await fetchMe()
      await fetchPermissions()
    }
    initialized.value = true
  }

  function logout() {
    authApi.logout().catch(() => {})
    removeToken()
    user.value = null
    permissions.value = null
  }

  // 监听 auth:expired 事件 (从 HTTP 拦截器触发)
  if (typeof window !== 'undefined') {
    window.addEventListener('auth:expired', () => {
      user.value = null
      permissions.value = null
    })
  }

  return {
    user, permissions, loading, initialized,
    isLoggedIn, role, roleLevel, isAdmin, isCoachOrAbove, displayName,
    hasRole, login, register, logout, fetchMe, fetchPermissions, initialize,
  }
})
