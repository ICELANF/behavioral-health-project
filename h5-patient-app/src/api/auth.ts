import request from './request'
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types'

/**
 * 认证相关API
 */
export const authAPI = {
  /**
   * 用户登录
   */
  async login(data: LoginRequest): Promise<TokenResponse> {
    // Use URLSearchParams for OAuth2 password flow (application/x-www-form-urlencoded)
    const params = new URLSearchParams()
    params.append('username', data.username)
    params.append('password', data.password)

    console.log('[Auth] Login attempt:', data.username)
    console.log('[Auth] Request body:', params.toString())

    return request.post<TokenResponse>('/api/v1/auth/login', params.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      silentError: true // 使用Mock登录fallback，不显示错误提示
    })
  },

  /**
   * 用户注册
   */
  register(data: RegisterRequest): Promise<TokenResponse> {
    return request.post<TokenResponse>('/api/v1/auth/register', data)
  },

  /**
   * 获取当前用户信息
   */
  getCurrentUser(): Promise<User> {
    return request.get<User>('/api/v1/auth/me', {
      silentError: true // 静默失败，由调用方处理
    })
  },

  /**
   * 用户登出
   */
  logout(): Promise<void> {
    return request.post<void>('/api/v1/auth/logout', undefined, {
      silentError: true // 静默失败，由调用方处理
    })
  }
}
