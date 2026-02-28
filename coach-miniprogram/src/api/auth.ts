/**
 * 认证相关 API
 * 对应后端: /api/v1/auth/*
 */
import http from './request'

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username:  string
  password:  string
  email:     string
  full_name?: string
}

export interface WxLoginParams {
  code: string
}

export interface UserInfo {
  id:                      number
  username:                string
  full_name:               string
  email?:                  string
  role:                    string   // observer|grower|sharer|coach|promoter|supervisor|master|admin
  role_level:              number   // 1-99
  growth_points:           number
  contribution_points?:    number
  influence_points?:       number
  wx_openid?:              string
  wx_miniprogram_openid?:  string
  avatar_url?:             string
  created_at:              string
}

export interface AuthResponse {
  access_token:  string
  refresh_token: string
  token_type:    string
  user:          UserInfo
}

const authApi = {
  login(params: LoginParams) {
    return http.post<AuthResponse>('/v1/auth/login', params, { noAuth: true })
  },
  register(params: RegisterParams) {
    return http.post<AuthResponse>('/v1/auth/register', params, { noAuth: true })
  },
  wechatLogin(params: WxLoginParams) {
    return http.post<AuthResponse>('/v1/auth/wechat/miniprogram', params, { noAuth: true })
  },
  getMe() {
    return http.get<UserInfo>('/v1/auth/me')
  },
  logout() {
    return http.post('/v1/auth/logout', {}, { noToast: true })
  },
  refresh(refreshToken: string) {
    return http.post<{ access_token: string }>('/v1/auth/refresh', {
      refresh_token: refreshToken,
    }, { noAuth: true })
  },
}

export default authApi
