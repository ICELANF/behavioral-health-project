import request from './request'

/**
 * 推送队列 API — 教练审批推送内容
 */
export const pushQueueApi = {
  /** 查询推送队列列表 */
  list(params?: {
    student_id?: number
    source_type?: string
    priority?: string
    status?: string
    skip?: number
    limit?: number
  }) {
    return request.get('/v1/coach/push-queue', { params })
  },

  /** 获取队列统计 */
  stats() {
    return request.get('/v1/coach/push-queue/stats')
  },

  /** 更新队列项 */
  update(itemId: string, data: Record<string, unknown>) {
    return request.put(`/v1/coach/push-queue/${itemId}`, data)
  },

  /** 审批通过 */
  approve(itemId: string) {
    return request.post(`/v1/coach/push-queue/${itemId}/approve`)
  },

  /** 拒绝 */
  reject(itemId: string) {
    return request.post(`/v1/coach/push-queue/${itemId}/reject`)
  },

  /** 批量审批 */
  batchApprove(itemIds: string[]) {
    return request.post('/v1/coach/push-queue/batch-approve', { item_ids: itemIds })
  },
}

/**
 * AI 推送建议 API
 */
export const pushRecommendationApi = {
  /** 获取全部推荐 */
  getAll() {
    return request.get('/v1/push-recommendations')
  },

  /** 获取指定学员推荐 */
  getForStudent(studentId: number) {
    return request.get(`/v1/push-recommendations/${studentId}`)
  },

  /** 一键应用推荐 */
  apply(studentId: number) {
    return request.post(`/v1/push-recommendations/${studentId}/apply`)
  },
}
