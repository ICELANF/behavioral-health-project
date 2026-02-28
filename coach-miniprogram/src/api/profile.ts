/**
 * 个人中心 API
 * 对应后端: /api/v1/profile/*
 */
import http from './request'

const profileApi = {
  /** 个人信息 */
  getProfile() {
    return http.get<any>('/v1/auth/me')
  },
  /** 更新个人信息 */
  updateProfile(data: Record<string, any>) {
    return http.put<any>('/v1/profile', data)
  },
  /** 我的认证 */
  getCertifications() {
    return http.get<{ items: any[] }>('/v1/profile/certifications')
  },
  /** 积分排行榜 */
  getLeaderboard(params?: Record<string, any>) {
    return http.get<{ items: any[] }>('/v1/profile/leaderboard', params)
  },
  /** 修改密码 */
  changePassword(data: { old_password: string; new_password: string }) {
    return http.post<any>('/v1/profile/change-password', data)
  },
  /** 账号设置 */
  getSettings() {
    return http.get<any>('/v1/profile/settings')
  },
  /** 更新设置 */
  updateSettings(data: Record<string, any>) {
    return http.put<any>('/v1/profile/settings', data)
  },
}

export default profileApi
