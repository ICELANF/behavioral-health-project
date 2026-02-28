/**
 * 同道者 API
 * 对应后端: /api/v1/companions/*
 */
import http from './request'

const companionApi = {
  /** 我的同道者列表 */
  getCompanions(params?: Record<string, any>) {
    return http.get<{ items: any[]; total: number }>('/v1/companions', params)
  },
  /** 同道者详情 */
  getCompanionDetail(id: number) {
    return http.get<any>(`/v1/companions/${id}`)
  },
  /** 发送邀请 */
  invite(data: { user_id: number; message?: string }) {
    return http.post<any>('/v1/companions/invite', data)
  },
  /** 收到的邀请 */
  getInvitations(params?: Record<string, any>) {
    return http.get<{ items: any[] }>('/v1/companions/invitations', params)
  },
  /** 接受邀请 */
  acceptInvitation(id: number) {
    return http.post<any>(`/v1/companions/invitations/${id}/accept`, {})
  },
  /** 拒绝邀请 */
  rejectInvitation(id: number) {
    return http.post<any>(`/v1/companions/invitations/${id}/reject`, {})
  },
}

export default companionApi
