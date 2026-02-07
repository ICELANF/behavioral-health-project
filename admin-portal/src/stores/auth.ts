/**
 * Auth Store - 认证状态管理
 * 管理用户登录状态、身份信息、权限
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api/request'

/**
 * 用户身份
 */
export interface UserIdentity {
  user_id: string
  role: string
  level: number
  certifications: string[]
  status: string
  permissions: string[]
  specialty_tags?: string[]
  coach_id?: string
  team_id?: string
}

/**
 * 登录响应
 */
interface LoginResponse {
  success: boolean
  token?: string
  refresh_token?: string
  user?: UserIdentity
  expires_in?: number
  error?: string
}

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem('admin_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('admin_refresh_token'))
  const user = ref<UserIdentity | null>(null)
  const loading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')
  const isExpert = computed(() => ['EXPERT', 'ADMIN'].includes(user.value?.role || ''))
  const isCoach = computed(() =>
    ['COACH_JUNIOR', 'COACH_INTERMEDIATE', 'COACH_SENIOR', 'EXPERT', 'ADMIN'].includes(user.value?.role || '')
  )
  const userLevel = computed(() => user.value?.level || 0)
  const userRole = computed(() => user.value?.role || 'USER')

  /**
   * 检查权限
   */
  const hasPermission = (resource: string, action: string): boolean => {
    if (!user.value) return false
    return user.value.permissions.includes(`${resource}:${action}`)
  }

  /**
   * 检查认证
   */
  const hasCertification = (cert: string): boolean => {
    if (!user.value) return false
    return user.value.certifications.includes(cert)
  }

  /**
   * 登录
   */
  const login = async (username: string, password: string): Promise<boolean> => {
    loading.value = true
    try {
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', password)
      const res = await request.post('v1/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      const data = res.data

      if (data.access_token) {
        token.value = data.access_token
        refreshToken.value = data.refresh_token || null
        user.value = data.user || null

        localStorage.setItem('admin_token', data.access_token)
        if (data.refresh_token) {
          localStorage.setItem('admin_refresh_token', data.refresh_token)
        }

        return true
      }

      return false
    } catch (error) {
      console.error('Login failed:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取用户信息
   */
  const fetchProfile = async (): Promise<boolean> => {
    if (!token.value) return false

    try {
      const res = await request.get('v1/auth/me')
      const data = res.data
      if (data && data.id) {
        user.value = {
          user_id: String(data.id),
          role: data.role || '',
          level: 0,
          certifications: [],
          status: data.is_active ? 'active' : 'inactive',
          permissions: [],
        }
        return true
      }
      return false
    } catch (error) {
      console.error('Fetch profile failed:', error)
      return false
    }
  }

  /**
   * 刷新Token
   */
  const refreshAccessToken = async (): Promise<boolean> => {
    if (!refreshToken.value) return false

    try {
      const res = await request.post('v1/auth/refresh', {
        refresh_token: refreshToken.value
      })
      const data = res.data as LoginResponse

      if (data.success && data.token) {
        token.value = data.token
        refreshToken.value = data.refresh_token || null
        user.value = data.user || null

        localStorage.setItem('admin_token', data.token)
        if (data.refresh_token) {
          localStorage.setItem('admin_refresh_token', data.refresh_token)
        }

        return true
      }

      return false
    } catch (error) {
      console.error('Refresh token failed:', error)
      return false
    }
  }

  /**
   * 登出
   */
  const logout = async (): Promise<void> => {
    try {
      await request.post('v1/auth/logout')
    } catch (error) {
      console.error('Logout request failed:', error)
    } finally {
      token.value = null
      refreshToken.value = null
      user.value = null
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_refresh_token')
    }
  }

  /**
   * 初始化
   */
  const init = async (): Promise<void> => {
    if (token.value) {
      const success = await fetchProfile()
      if (!success && refreshToken.value) {
        await refreshAccessToken()
      }
    }
  }

  return {
    // 状态
    token,
    refreshToken,
    user,
    loading,

    // 计算属性
    isLoggedIn,
    isAdmin,
    isExpert,
    isCoach,
    userLevel,
    userRole,

    // 方法
    hasPermission,
    hasCertification,
    login,
    logout,
    fetchProfile,
    refreshAccessToken,
    init
  }
})
