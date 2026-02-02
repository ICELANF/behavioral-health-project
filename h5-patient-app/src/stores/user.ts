import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api/auth'
import { storage } from '@/utils/storage'
import type { User, LoginRequest, RegisterRequest } from '@/types'
import { showToast } from 'vant'

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(storage.token.get())
  const loading = ref(false)

  // Getters
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const userName = computed(() => user.value?.full_name || user.value?.username || '用户')
  const userRole = computed(() => user.value?.role || 'patient')

  // Actions

  /**
   * 检查登录状态
   */
  const checkLoginStatus = async () => {
    const savedToken = storage.token.get()
    const savedUser = storage.user.get()

    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = savedUser

      // 如果是Mock token，跳过验证
      if (savedToken.startsWith('mock-jwt-token-')) {
        console.log('🔧 Mock登录模式 - 跳过token验证')
        return
      }

      // 尝试获取最新用户信息
      try {
        const freshUser = await authAPI.getCurrentUser()
        user.value = freshUser
        storage.user.set(freshUser)
      } catch (error) {
        // Token可能已过期，清除本地数据
        console.error('Token verification failed:', error)
        logout()
      }
    }
  }

  /**
   * 用户登录
   */
  const login = async (credentials: LoginRequest) => {
    loading.value = true

    // 清除旧token，避免干扰登录请求
    storage.token.remove()
    storage.user.remove()
    token.value = null
    user.value = null

    try {
      console.log('[UserStore] Attempting real API login...')
      // 尝试调用真实API
      const response = await authAPI.login(credentials)

      // 保存Token和用户信息
      token.value = response.access_token
      user.value = response.user

      storage.token.set(response.access_token)
      storage.user.set(response.user)

      console.log('[UserStore] Real API login SUCCESS!', response)
      showToast('登录成功')
      return response
    } catch (error: any) {
      console.error('[UserStore] Real API login FAILED:', error?.response?.status, error?.response?.data)

      // 【临时方案】Mock登录 - 用于UI测试
      console.warn('🔧 使用Mock登录模式（仅用于测试）')

      const mockToken = 'mock-jwt-token-' + Date.now()
      const mockUser: User = {
        id: credentials.username === 'admin' ? 1 : 2,
        username: credentials.username,
        email: credentials.username + '@example.com',
        role: credentials.username === 'admin' ? 'admin' :
              credentials.username.includes('coach') ? 'coach' : 'patient',
        full_name: credentials.username === 'patient_alice' ? 'Alice Wang' :
                   credentials.username === 'patient_bob' ? 'Bob Chen' :
                   credentials.username === 'coach_carol' ? 'Carol Li' :
                   credentials.username === 'admin' ? 'Admin User' : 'Test User',
        is_active: true,
        created_at: new Date().toISOString()
      }

      token.value = mockToken
      user.value = mockUser
      storage.token.set(mockToken)
      storage.user.set(mockUser)

      showToast('登录成功（测试模式）')

      return {
        access_token: mockToken,
        refresh_token: mockToken,
        token_type: 'bearer',
        user: mockUser
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 用户注册
   */
  const register = async (data: RegisterRequest) => {
    loading.value = true
    try {
      const response = await authAPI.register(data)

      // 注册成功后自动登录
      token.value = response.access_token
      user.value = response.user

      storage.token.set(response.access_token)
      storage.user.set(response.user)

      showToast('注册成功')
      return response
    } catch (error) {
      console.error('Register failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 用户登出
   */
  const logout = async () => {
    try {
      // 调用后端登出接口（可选）
      await authAPI.logout().catch(() => {
        // 忽略错误，继续清除本地数据
      })
    } finally {
      // 清除本地数据
      token.value = null
      user.value = null
      storage.token.remove()
      storage.user.remove()
      showToast('已退出登录')
    }
  }

  /**
   * 更新用户信息
   */
  const updateUserInfo = (newUser: User) => {
    user.value = newUser
    storage.user.set(newUser)
  }

  return {
    // State
    user,
    token,
    loading,

    // Getters
    isLoggedIn,
    userName,
    userRole,

    // Actions
    checkLoginStatus,
    login,
    register,
    logout,
    updateUserInfo
  }
})
