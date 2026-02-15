/**
 * 认证 API (响应格式对齐版)
 * 对接: auth_api.py (6端点)
 *
 * 归一化:
 *  - login/register 返回的 user.full_name → display_name
 *  - user.intervention_stage → journey_stage
 *  - getMe 返回同上
 */

import http from './http'
import { normalizeUser } from './normalizers'
import type { LoginRequest, LoginResponse, RegisterRequest, User } from '@/types'

export const authApi = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    const raw = await http.post('/auth/login', data).then(r => r.data)
    return {
      access_token: raw.access_token,
      refresh_token: raw.refresh_token,
      token_type: raw.token_type || 'bearer',
      user: normalizeUser(raw.user),
    }
  },

  async register(data: RegisterRequest): Promise<LoginResponse> {
    const raw = await http.post('/auth/register', data).then(r => r.data)
    return {
      access_token: raw.access_token,
      refresh_token: raw.refresh_token,
      token_type: raw.token_type || 'bearer',
      user: normalizeUser(raw.user),
    }
  },

  async getMe(): Promise<User> {
    const raw = await http.get('/auth/me').then(r => r.data)
    return normalizeUser(raw)
  },

  refreshToken(refreshToken?: string): Promise<{ access_token: string }> {
    return http.post('/auth/refresh', { refresh_token: refreshToken }).then(r => r.data)
  },

  changePassword(data: { old_password: string; new_password: string }): Promise<void> {
    return http.put('/auth/password', data).then(r => r.data)
  },

  logout(): Promise<void> {
    return http.post('/auth/logout').then(r => r.data)
  },
}
