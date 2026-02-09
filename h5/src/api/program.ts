import api from './index'

export const programApi = {
  /** 方案模板列表 */
  listTemplates(params?: { category?: string }) {
    return api.get('/api/v1/programs/templates', { params })
  },

  /** 报名方案 */
  enroll(data: { template_id: string; coach_id?: number; push_preferences?: object }) {
    return api.post('/api/v1/programs/enroll', data)
  },

  /** 我的方案列表 */
  getMyPrograms() {
    return api.get('/api/v1/programs/my')
  },

  /** 今日推送内容 */
  getToday(enrollmentId: string) {
    return api.get(`/api/v1/programs/my/${enrollmentId}/today`)
  },

  /** 提交微调查/交互 */
  submitInteraction(enrollmentId: string, data: {
    day_number: number
    slot: string
    survey_answers?: Record<string, any>
    photo_urls?: string[]
    device_data?: object
  }) {
    return api.post(`/api/v1/programs/my/${enrollmentId}/interact`, data)
  },

  /** 行为轨迹时间线 */
  getTimeline(enrollmentId: string) {
    return api.get(`/api/v1/programs/my/${enrollmentId}/timeline`)
  },

  /** 行为特征雷达图 */
  getProgress(enrollmentId: string) {
    return api.get(`/api/v1/programs/my/${enrollmentId}/progress`)
  },

  /** 暂停/恢复/退出 */
  updateStatus(enrollmentId: string, action: string, reason?: string) {
    return api.post(`/api/v1/programs/my/${enrollmentId}/status`, { action, reason })
  },
}
