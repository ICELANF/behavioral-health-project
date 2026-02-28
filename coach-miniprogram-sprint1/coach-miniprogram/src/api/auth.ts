/**
 * 认证相关 API
 * 对应后端: /api/v1/auth/*
 */
import http from './request'

// ─── 类型定义 ────────────────────────────────────────────────
export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  password: string
  email: string
  full_name?: string
}

export interface WxLoginParams {
  code: string    // wx.login() 返回的 code
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: UserInfo
}

export interface UserInfo {
  id: number
  username: string
  full_name: string
  email?: string
  role: string                  // 'observer' | 'grower' | 'sharer' | 'coach' | 'promoter' | 'supervisor' | 'master' | 'admin'
  role_level: number            // 1-99
  growth_points: number
  contribution_points?: number
  influence_points?: number
  wx_openid?: string
  wx_miniprogram_openid?: string
  avatar_url?: string
  created_at: string
}

// ─── API 方法 ────────────────────────────────────────────────
export const authApi = {
  /** 账号密码登录 */
  login(params: LoginParams) {
    return http.post<AuthResponse>('/v1/auth/login', params, { noAuth: true })
  },

  /** 注册 */
  register(params: RegisterParams) {
    return http.post<AuthResponse>('/v1/auth/register', params, { noAuth: true })
  },

  /** 微信小程序一键登录 */
  wechatLogin(params: WxLoginParams) {
    return http.post<AuthResponse>('/v1/auth/wechat/miniprogram', params, { noAuth: true })
  },

  /** 获取当前用户信息 */
  getMe() {
    return http.get<UserInfo>('/v1/auth/me')
  },

  /** 退出登录 */
  logout() {
    return http.post('/v1/auth/logout', {}, { noToast: true })
  },

  /** 刷新 Token（内部使用，request.ts 已封装） */
  refresh(refreshToken: string) {
    return http.post<{ access_token: string }>('/v1/auth/refresh', {
      refresh_token: refreshToken
    }, { noAuth: true })
  }
}

export default authApi
